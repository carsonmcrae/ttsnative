# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Keep a per-process credential and bounded, expiring reader handoffs.

Scope: One-use tickets, read-only progress acknowledgements and private discovery lifecycle.
Does NOT belong: Document contents, media playback or installation of models.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ltts.agent.discovery import publish, unpublish
from ltts.agent.schemas import Acknowledge, ReadClaim, ReadCreated, ReadProgress, ReadRequest
from ltts.common import new_id
from ltts.config import Settings, loopback_origin
from ltts.errors import BusyError, ConflictError, ForbiddenError, NotFoundError

REQUEST_TTL_S = 600.0
MAX_REQUESTS = 64
log = logging.getLogger("ltts.agent")


@dataclass
class Handoff:
    request: ReadRequest
    ticket: str | None
    ack_token: str
    expires: float
    progress: ReadProgress


class AgentState:
    def __init__(self, settings: Settings, clock: Callable[[], float] = time.monotonic):
        self.settings = settings
        self.instance_id = new_id()
        self.token = secrets.token_hex(32)
        hostname = "::1" if settings.host == "::1" else "127.0.0.1"
        self.origin = loopback_origin(hostname, settings.agent_port)
        self.ui_url = settings.agent_ui_url or self.origin
        self._clock = clock
        self._lock = threading.Lock()
        self._requests: dict[str, Handoff] = {}
        self._published: Path | None = None

    def descriptor(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "protocolVersion": 1,
            "instanceId": self.instance_id,
            "pid": os.getpid(),
            "origin": self.origin,
            "uiUrl": self.ui_url,
            "kind": self.settings.agent_kind,
            "token": self.token,
        }
        if self.settings.agent_launcher is not None:
            result["launcher"] = self.settings.agent_launcher
        if self.settings.agent_source_root is not None:
            result["sourceRoot"] = str(self.settings.agent_source_root.resolve())
        return result

    def start(self) -> None:
        if self.settings.agent_port and not self.available:
            try:
                self._published = publish(self.settings, self.descriptor())
            except OSError:
                # Agent discovery is optional; never log an exception that may contain the token or path.
                log.warning("local agent discovery unavailable; the reader remains available")

    @property
    def available(self) -> bool:
        return self._published is not None

    def close(self) -> None:
        if self._published is not None:
            published = self._published
            self._published = None
            try:
                unpublish(published)
            except OSError:
                log.warning("local agent discovery cleanup unavailable")

    def _prune(self) -> None:
        now = self._clock()
        self._requests = {key: value for key, value in self._requests.items() if value.expires > now}

    def create(self, request: ReadRequest) -> ReadCreated:
        with self._lock:
            self._prune()
            if len(self._requests) >= MAX_REQUESTS:
                raise BusyError("Too many pending reader requests.", code="agent_busy")
            request_id, ticket = new_id(), secrets.token_hex(32)
            self._requests[request_id] = Handoff(
                request,
                ticket,
                secrets.token_hex(32),
                self._clock() + REQUEST_TTL_S,
                ReadProgress(status="pending"),
            )
            return ReadCreated(request_id=request_id, ticket=ticket)

    def progress(self, request_id: str) -> ReadProgress:
        with self._lock:
            self._prune()
            return self._get(request_id).progress.model_copy()

    def _get(self, request_id: str) -> Handoff:
        if request_id not in self._requests:
            raise NotFoundError("That reader request expired or does not exist.", code="agent_request_not_found")
        return self._requests[request_id]

    def claim(self, ticket: str) -> ReadClaim:
        with self._lock:
            self._prune()
            for request_id, handoff in self._requests.items():
                if handoff.ticket is not None and hmac.compare_digest(handoff.ticket, ticket):
                    handoff.ticket = None
                    return ReadClaim(**handoff.request.model_dump(), request_id=request_id, ack_token=handoff.ack_token)
            raise ForbiddenError("The reader ticket is invalid or expired.", code="agent_ticket_invalid")

    def acknowledge(self, body: Acknowledge) -> ReadProgress:
        with self._lock:
            self._prune()
            handoff = self._get(body.request_id)
            if handoff.ticket is not None or not hmac.compare_digest(handoff.ack_token, body.ack_token):
                raise ForbiddenError("The reader acknowledgement is invalid.", code="agent_ack_invalid")
            if handoff.progress.status != "pending":
                raise ConflictError("This reader request already finished.", code="agent_request_finished")
            handoff.progress = ReadProgress(status=body.status, error_code=body.error_code)
            return handoff.progress.model_copy()

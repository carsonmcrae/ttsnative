# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Bounded, expiring reader requests and safe one-use acknowledgements.

Scope: Tickets cannot be replayed or used to alter a preauthorized document/voice request.
Does NOT belong: Browser playback or model installation.
"""

import pytest

from ltts.agent.schemas import Acknowledge, ReadRequest
from ltts.agent.state import MAX_REQUESTS, REQUEST_TTL_S, AgentState
from ltts.config import Settings
from ltts.errors import BusyError, ConflictError, ForbiddenError, NotFoundError


def test_tickets_expire_and_free_capacity_without_changing_the_request(settings: Settings) -> None:
    now = [0.0]
    state = AgentState(settings, clock=lambda: now[0])
    request = ReadRequest(document_id="1" * 32, voice_id="kokoro:alpha", pace=1.5, autoplay=False)
    created = state.create(request)
    claimed = state.claim(created.ticket)
    assert state.progress(created.request_id).status == "pending"
    assert claimed.document_id == request.document_id and claimed.pace == 1.5 and claimed.autoplay is False
    with pytest.raises(ForbiddenError):
        state.claim(created.ticket)
    with pytest.raises(ForbiddenError):
        state.acknowledge(Acknowledge(request_id=created.request_id, ack_token="0" * 64, status="playing"))
    second = state.create(request)
    with pytest.raises(ForbiddenError):
        state.acknowledge(Acknowledge(request_id=second.request_id, ack_token="0" * 64, status="opened"))
    for _ in range(MAX_REQUESTS - 2):
        state.create(request)
    with pytest.raises(BusyError):
        state.create(request)
    now[0] = REQUEST_TTL_S
    with pytest.raises(ForbiddenError):
        state.claim(second.ticket)
    with pytest.raises(NotFoundError):
        state.progress(created.request_id)
    new = state.create(request)
    assert state.progress(new.request_id).status == "pending"


@pytest.mark.parametrize("status", ["opened", "playing", "user_action_required", "failed"])
def test_acknowledgement_reports_only_a_claimed_fixed_request(settings: Settings, status: str) -> None:
    state = AgentState(settings)
    created = state.create(ReadRequest(document_id="2" * 32, voice_id="kokoro:alpha"))
    claimed = state.claim(created.ticket)
    assert state.progress(created.request_id).status == "pending"
    body = Acknowledge.model_validate(
        {"requestId": created.request_id, "ackToken": claimed.ack_token, "status": status}
    )
    assert state.acknowledge(body).status == status
    assert state.progress(created.request_id).status == status
    with pytest.raises(ConflictError):
        state.acknowledge(body.model_copy(update={"status": "opened"}))

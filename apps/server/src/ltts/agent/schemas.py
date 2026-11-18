# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Bounded agent requests and one-use browser handoffs.

Scope: Document/voice identifiers, playback options, safe acknowledgement codes and export options.
Does NOT belong: Authentication, request storage or synthesis.
"""

from typing import Annotated, Literal

from pydantic import Field

from ltts.common import ApiModel
from ltts.exports.models import ExportRequest

Identifier = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
Secret = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Voice = Annotated[str, Field(min_length=1, max_length=160)]
Pace = Annotated[float, Field(ge=0.5, le=2.0, allow_inf_nan=False)]
ReadStatus = Literal["pending", "opened", "playing", "user_action_required", "failed"]


class ReadRequest(ApiModel):
    document_id: Identifier
    voice_id: Voice
    pace: Pace = 1.0
    autoplay: bool = True


class ReadCreated(ApiModel):
    request_id: str
    ticket: str
    status: Literal["pending"] = "pending"


class ReadProgress(ApiModel):
    status: ReadStatus
    error_code: str | None = None


class ClaimRequest(ApiModel):
    ticket: Secret


class ReadClaim(ReadRequest):
    request_id: str
    ack_token: str


class Acknowledge(ApiModel):
    request_id: Identifier
    ack_token: Secret
    status: Literal["opened", "playing", "user_action_required", "failed"]
    error_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")] | None = None


class AgentExportRequest(ExportRequest):
    document_id: Identifier
    voice_id: Voice
    pace: Pace = 1.0
    format: Literal["mp3", "wav", "m4b"] = "mp3"

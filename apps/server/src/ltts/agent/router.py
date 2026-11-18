# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Authenticated native access to existing local document and export pipelines.

Scope: Native bearer requests and a separate, origin-bound browser ticket claim/acknowledgement.
Does NOT belong: LAN access, downloads/installations of dependencies or generic UI remote control.
"""

from __future__ import annotations

import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from starlette.exceptions import HTTPException

from ltts import __version__
from ltts.agent.schemas import (
    Acknowledge,
    AgentExportRequest,
    ClaimRequest,
    ReadClaim,
    ReadCreated,
    ReadProgress,
    ReadRequest,
)
from ltts.agent.state import AgentState
from ltts.container import ServicesDep
from ltts.documents.router import DocumentId, upload_document
from ltts.documents.schemas import DocumentDetail
from ltts.engines.router import list_voices
from ltts.errors import ForbiddenError
from ltts.exports import router as exports
from ltts.exports.m4b import FfmpegMissingError, find_ffmpeg
from ltts.jobs import JobOut
from ltts.speech_api.guard import bearer, is_local
from ltts.speech_api.router import TokenError


def _local(request: Request, services: ServicesDep) -> AgentState:
    state: AgentState = request.app.state.agent
    if not state.available:
        raise HTTPException(status_code=404)
    if services.lan.serving(request.scope) or not is_local(request.client.host if request.client else None):
        raise ForbiddenError("Agent access is available only on this computer.", code="network_not_allowed")
    return state


def _native(request: Request, services: ServicesDep) -> AgentState:
    state = _local(request, services)
    if any(name == "origin" or name.startswith("sec-fetch-") for name in request.headers):
        raise ForbiddenError("Web pages cannot use native agent credentials.", code="browser_not_allowed")
    supplied = bearer(request.headers.get("authorization")) or ""
    if not hmac.compare_digest(state.token.encode(), supplied.encode()):
        raise TokenError("A valid agent credential is required.", headers={"WWW-Authenticate": "Bearer"})
    return state


def _browser(request: Request, services: ServicesDep) -> AgentState:
    state = _local(request, services)
    origins = request.headers.getlist("origin")
    if origins != [state.ui_url] or not request.headers.get("x-ltts-client"):
        raise ForbiddenError("Use the configured TTSNative reader on this computer.", code="agent_origin_invalid")
    return state


Native = Annotated[AgentState, Depends(_native)]
Browser = Annotated[AgentState, Depends(_browser)]
router = APIRouter(prefix="/api/agent/v1", tags=["agent"], dependencies=[Depends(_native)])
reader_router = APIRouter(prefix="/api/agent-reader", tags=["agent reader"])


@router.get("/status")
def status(agent: Native, services: ServicesDep) -> dict[str, Any]:
    return {
        "protocolVersion": 1,
        "instanceId": agent.instance_id,
        "version": services.settings.build_version or __version__,
        "kind": services.settings.agent_kind,
        "uiUrl": agent.ui_url,
        "formats": ["mp3", "wav", "m4b"],
        "supportedDocuments": ["pdf", "epub", "docx", "md", "markdown", "txt"],
        "maxUploadBytes": services.settings.max_upload_bytes,
        "ffmpegAvailable": find_ffmpeg() is not None,
        "engines": services.engines.infos(),
    }


@router.post("/documents/upload", status_code=201)
async def upload(
    request: Request,
    services: ServicesDep,
    filename: Annotated[str, Query(min_length=1, max_length=255, pattern=r"^[^/\\]+$")],
) -> DocumentDetail:
    return await upload_document(request, services, filename)


@router.post("/read-requests", status_code=201)
def read_request(body: ReadRequest, agent: Native, services: ServicesDep) -> ReadCreated:
    services.document_repo.get(body.document_id)
    services.engines.resolve(body.voice_id)
    return agent.create(body)


@router.get("/read-requests/{request_id}")
def read_progress(request_id: DocumentId, agent: Native) -> ReadProgress:
    return agent.progress(request_id)


@reader_router.post("/claim")
def claim(body: ClaimRequest, agent: Browser) -> ReadClaim:
    return agent.claim(body.ticket)


@reader_router.post("/ack")
def acknowledge(body: Acknowledge, agent: Browser) -> ReadProgress:
    return agent.acknowledge(body)


@router.post("/exports", status_code=202)
def start_export(body: AgentExportRequest, services: ServicesDep) -> JobOut:
    services.engines.resolve(body.voice_id)
    if body.format == "m4b" and find_ffmpeg() is None:
        raise FfmpegMissingError("M4B export needs an ffmpeg installed by the user.")
    return services.exports.start(body)


# Keep export recovery, cancellation and download behavior identical to the reader's own UI.
router.add_api_route("/voices", list_voices, methods=["GET"])
router.add_api_route("/exports/{job_id}", exports.get_export, methods=["GET"])
router.add_api_route("/exports/{job_id}/download", exports.download_export, methods=["GET"])
router.add_api_route("/exports/{job_id}/pause", exports.pause_export, methods=["POST"], status_code=202)
router.add_api_route("/exports/{job_id}/resume", exports.resume_export, methods=["POST"], status_code=202)
router.add_api_route("/exports/{job_id}/cancel", exports.cancel_export, methods=["POST"], status_code=202)

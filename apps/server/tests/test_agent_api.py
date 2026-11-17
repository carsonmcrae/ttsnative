# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Agent authentication and actual document, reader-ticket and export workflows.

Scope: No browser bearer access, fixed origin claims, local uploads, ready voices and existing jobs.
Does NOT belong: Private discovery filesystem behavior or real-model audio quality.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from starlette.requests import Request

from conftest import FakeEngine, wait_job
from export_support import pause_after_saving, request
from ltts.agent import router as agent_router
from ltts.app import create_app
from ltts.config import Settings
from ltts.container import Services
from ltts.errors import ConflictError, ForbiddenError
from ltts.exports.models import ExportRequest
from ltts.jobs import JobOut

PREFIX = "/api/agent/v1"
UI = "http://127.0.0.1:5173"


@pytest.fixture
def agent_client(settings: Settings, services: Services, tmp_path: Path) -> Iterator[TestClient]:
    settings.agent_port = 8765
    settings.agent_ui_url = UI
    settings.agent_discovery_dir = tmp_path / "private-discovery"
    app = create_app(settings, services=services)
    with TestClient(
        app, base_url="http://127.0.0.1:8765", client=("127.0.0.1", 45000), headers={"X-LTTS-Client": "agent"}
    ) as caller:
        caller.headers["Authorization"] = f"Bearer {app.state.agent.token}"
        yield caller


def upload(caller: TestClient, filename: str = "agent.txt") -> str:
    result = caller.post(
        f"{PREFIX}/documents/upload",
        params={"filename": filename},
        content=b"A lantern lit the harbor. A second boat arrived.",
    )
    assert result.status_code == 201
    return str(result.json()["id"])


def create_read(caller: TestClient, **extra: Any) -> dict[str, Any]:
    response = caller.post(
        f"{PREFIX}/read-requests", json={"documentId": upload(caller), "voiceId": "kokoro:alpha", "pace": 1.25, **extra}
    )
    assert response.status_code == 201
    return dict(response.json())


def test_status_is_authenticated_and_never_returns_credentials(agent_client: TestClient) -> None:
    status = agent_client.get(f"{PREFIX}/status")
    assert status.status_code == 200 and status.headers["cache-control"] == "no-store"
    body = status.json()
    assert body["protocolVersion"] == 1 and body["uiUrl"] == UI and body["kind"] == "source"
    assert body["formats"] == ["mp3", "wav", "m4b"] and body["maxUploadBytes"] == 25 * 1024 * 1024
    assert body["engines"][0]["status"] == "ready" and "token" not in body
    assert agent_client.get(f"{PREFIX}/voices").json()[0]["id"] == "kokoro:alpha"
    for value in ("", "Bearer wrong", "Basic x"):
        denied = agent_client.get(f"{PREFIX}/status", headers={"Authorization": value})
        assert denied.status_code == 401 and denied.json()["error"]["code"] == "invalid_token"
    assert agent_client.get(f"{PREFIX}/status", headers={b"Authorization": b"Bearer caf\xe9"}).status_code == 401
    for headers in ({"Origin": UI}, {"Sec-Fetch-Mode": "cors"}, {"Sec-Fetch-Unknown": "x"}):
        denied = agent_client.get(f"{PREFIX}/status", headers=headers)
        assert denied.status_code == 403 and denied.json()["error"]["code"] == "browser_not_allowed"
        assert "access-control-allow-origin" not in denied.headers


def test_bridge_is_disabled_without_a_published_port(client: TestClient) -> None:
    assert client.get(f"{PREFIX}/status").status_code == 404


def test_both_agent_surfaces_refuse_nonlocal_or_lan_even_with_a_valid_secret(
    agent_client: TestClient,
    services: Services,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = agent_client.app
    for client_address in (None, ("192.168.1.8", 50000)):
        scope = {"type": "http", "app": app, "client": client_address, "headers": []}
        with pytest.raises(ForbiddenError, match="only on this computer"):
            agent_router._local(Request(scope), services)
    monkeypatch.setattr(services.lan, "serving", lambda scope: True)
    scope = {"type": "http", "app": app, "client": ("127.0.0.1", 50000), "headers": []}
    with pytest.raises(ForbiddenError, match="only on this computer"):
        agent_router._local(Request(scope), services)


def test_browser_requires_both_exact_origin_and_client_header(agent_client: TestClient, services: Services) -> None:
    scope = {
        "type": "http",
        "app": agent_client.app,
        "client": ("127.0.0.1", 50000),
        "headers": [(b"origin", UI.encode())],
    }
    with pytest.raises(ForbiddenError, match="configured TTSNative"):
        agent_router._browser(Request(scope), services)


def test_reader_claim_is_origin_bound_one_use_and_reports_actual_ui_ack(agent_client: TestClient) -> None:
    created = create_read(agent_client)
    url = f"{PREFIX}/read-requests/{created['requestId']}"
    assert created["status"] == "pending" and len(created["ticket"]) == 64
    assert agent_client.get(url).json()["status"] == "pending"
    for origin in (None, "http://localhost:5173", "http://127.0.0.1:8765"):
        headers = {"Origin": origin} if origin else {}
        denied = agent_client.post("/api/agent-reader/claim", json={"ticket": created["ticket"]}, headers=headers)
        assert denied.status_code == 403
    claimed = agent_client.post(
        "/api/agent-reader/claim", json={"ticket": created["ticket"]}, headers={"Origin": UI}
    ).json()
    assert claimed["requestId"] == created["requestId"] and claimed["pace"] == 1.25
    assert claimed["voiceId"] == "kokoro:alpha" and claimed["autoplay"] is True
    assert agent_client.get(url).json()["status"] == "pending"
    again = agent_client.post("/api/agent-reader/claim", json={"ticket": created["ticket"]}, headers={"Origin": UI})
    assert again.status_code == 403
    ack = {
        "requestId": created["requestId"],
        "ackToken": claimed["ackToken"],
        "status": "user_action_required",
        "errorCode": "autoplay_blocked",
    }
    assert agent_client.post("/api/agent-reader/ack", json=ack, headers={"Origin": UI}).status_code == 200
    assert agent_client.get(url).json() == {"status": "user_action_required", "errorCode": "autoplay_blocked"}
    assert agent_client.post("/api/agent-reader/ack", json=ack, headers={"Origin": UI}).status_code == 409
    assert created["ticket"] not in agent_client.get(url).text


def test_reader_validation_rejects_unavailable_unknown_and_invalid_options(
    agent_client: TestClient,
    engines: dict[str, FakeEngine],
) -> None:
    document_id = upload(agent_client)
    body = {"documentId": document_id, "voiceId": "kokoro:alpha"}
    for extra in ({"voiceId": "kokoro:no-such-voice"}, {"documentId": "0" * 32}):
        assert agent_client.post(f"{PREFIX}/read-requests", json=body | extra).status_code == 404
    for extra in ({"pace": 0}, {"pace": 2.01}, {"documentId": "../private"}, {"voiceId": ""}):
        assert agent_client.post(f"{PREFIX}/read-requests", json=body | extra).status_code == 422
    engines["kokoro"].ready = False
    failed = agent_client.post(f"{PREFIX}/read-requests", json=body)
    assert failed.status_code == 503 and failed.json()["error"]["code"] == "engine_not_installed"
    assert engines["kokoro"].calls == []


@pytest.mark.parametrize("status,error_code", [("opened", None), ("failed", "document_load_failed")])
def test_claim_cannot_report_opened_before_the_reader_load_result(
    agent_client: TestClient,
    status: str,
    error_code: str | None,
) -> None:
    created = create_read(agent_client, autoplay=False)
    claimed = agent_client.post(
        "/api/agent-reader/claim", json={"ticket": created["ticket"]}, headers={"Origin": UI}
    ).json()
    progress = f"{PREFIX}/read-requests/{created['requestId']}"
    assert agent_client.get(progress).json() == {"status": "pending", "errorCode": None}
    acknowledgement = {
        "requestId": claimed["requestId"],
        "ackToken": claimed["ackToken"],
        "status": status,
        "errorCode": error_code,
    }
    response = agent_client.post("/api/agent-reader/ack", json=acknowledgement, headers={"Origin": UI})
    assert response.status_code == 200
    assert agent_client.get(progress).json() == {"status": status, "errorCode": error_code}


@pytest.mark.parametrize(
    "configured,normalized",
    [
        ("http://LOCALHOST:5173", "http://localhost:5173"),
        ("http://LOCALHOST:80", "http://localhost"),
        ("http://127.0.0.1", "http://127.0.0.1"),
        ("http://[::1]:80", "http://[::1]"),
    ],
)
def test_browser_normalized_origin_can_claim_the_configured_reader(
    settings: Settings,
    services: Services,
    tmp_path: Path,
    configured: str,
    normalized: str,
) -> None:
    configured_settings = settings.model_copy(update={"agent_port": 8765, "agent_discovery_dir": tmp_path / "agent"})
    configured_settings.agent_ui_url = Settings(agent_ui_url=configured).agent_ui_url
    app = create_app(configured_settings, services=services)
    with TestClient(
        app, base_url="http://127.0.0.1:8765", client=("127.0.0.1", 45000), headers={"X-LTTS-Client": "web"}
    ) as caller:
        caller.headers["Authorization"] = f"Bearer {app.state.agent.token}"
        created = create_read(caller, autoplay=False)
        assert caller.get(f"{PREFIX}/status").json()["uiUrl"] == normalized
        claimed = caller.post(
            "/api/agent-reader/claim", json={"ticket": created["ticket"]}, headers={"Origin": normalized}
        )
        assert claimed.status_code == 200 and claimed.json()["requestId"] == created["requestId"]


def test_agent_upload_preserves_source_and_uses_existing_extraction_validation(agent_client: TestClient) -> None:
    assert upload(agent_client, "notes.md")
    for filename in ("../outside.txt", "audio.pdf", "legacy.doc"):
        response = agent_client.post(f"{PREFIX}/documents/upload", params={"filename": filename}, content=b"Hello.")
        assert response.status_code in (400, 415, 422)
    assert agent_client.get(f"{PREFIX}/documents/arbitrary-file").status_code == 404


def test_exports_use_existing_jobs_and_download_a_decodable_mp3(agent_client: TestClient) -> None:
    document_id = upload(agent_client)
    started = agent_client.post(f"{PREFIX}/exports", json=request(document_id, format="mp3", pace=1.25))
    assert started.status_code == 202
    job_id = started.json()["id"]
    assert wait_job(agent_client, job_id)["status"] == "succeeded"
    described = agent_client.get(f"{PREFIX}/exports/{job_id}").json()
    assert described["job"]["id"] == job_id and described["job"]["status"] == "succeeded"
    assert described["sentences"] > 0
    audio = agent_client.get(f"{PREFIX}/exports/{job_id}/download")
    assert audio.status_code == 200 and audio.headers["content-type"] == "audio/mpeg"
    samples, rate = sf.read(io.BytesIO(audio.content))
    assert len(samples) > 0 and rate == 24000


def test_agent_exports_resume_saved_work_and_cancel_discards_it(
    agent_client: TestClient,
    services: Services,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    announce = pause_after_saving(monkeypatch, services, 1)
    started = agent_client.post(f"{PREFIX}/exports", json=request(upload(agent_client))).json()
    job_id = started["id"]
    announce(job_id)
    assert wait_job(agent_client, job_id)["status"] == "paused"
    assert agent_client.get(f"{PREFIX}/exports/{job_id}").json()["savedSentences"] == 1
    assert agent_client.post(f"{PREFIX}/exports/{job_id}/pause").status_code == 202
    resumed = agent_client.post(f"{PREFIX}/exports/{job_id}/resume")
    assert resumed.status_code == 202 and resumed.json()["id"] == job_id
    assert wait_job(agent_client, job_id)["status"] == "succeeded"
    announce = pause_after_saving(monkeypatch, services, 1)
    next_job = agent_client.post(f"{PREFIX}/exports", json=request(upload(agent_client))).json()["id"]
    announce(next_job)
    assert wait_job(agent_client, next_job)["status"] == "paused"
    canceled = agent_client.post(f"{PREFIX}/exports/{next_job}/cancel")
    assert canceled.status_code == 202 and canceled.json()["status"] == "canceled"
    assert agent_client.get(f"{PREFIX}/exports/{next_job}").json()["savedSentences"] == 0
    assert not services.exports.folder(next_job).exists()


def test_m4b_missing_ffmpeg_is_refused_before_synthesis(
    agent_client: TestClient,
    engines: dict[str, FakeEngine],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent_router, "find_ffmpeg", lambda: None)
    assert agent_client.get(f"{PREFIX}/status").json()["ffmpegAvailable"] is False
    body = request(upload(agent_client), format="m4b")
    response = agent_client.post(f"{PREFIX}/exports", json=body)
    assert response.status_code == 409 and response.json()["error"]["code"] == "ffmpeg_missing"
    assert engines["kokoro"].calls == []
    monkeypatch.setattr(agent_router, "find_ffmpeg", lambda: Path("ffmpeg"))
    assert agent_client.get(f"{PREFIX}/status").json()["ffmpegAvailable"] is True
    attempted: list[ExportRequest] = []

    def full_queue(body: ExportRequest) -> JobOut:
        attempted.append(body)
        raise ConflictError("The export queue is full.", code="export_queue_full")

    monkeypatch.setattr(agent_client.app.state.services.exports, "start", full_queue)
    # A configured ffmpeg permits the existing service to decide queue eligibility, without a download.
    response = agent_client.post(f"{PREFIX}/exports", json=body)
    assert response.status_code == 409 and response.json()["error"]["code"] == "export_queue_full"
    assert len(attempted) == 1 and attempted[0].format == "m4b"

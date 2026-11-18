# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Owner-private per-instance discovery and validated UI origins.

Scope: Atomic publication, rotation, conservative cleanup and isolated platform paths.
Does NOT belong: Starting an installed application or exposing its credential to a web page.
"""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ltts.agent import discovery
from ltts.agent import state as agent_state
from ltts.agent.state import AgentState
from ltts.app import create_app
from ltts.config import Settings
from ltts.container import Services


def test_discovery_is_per_launch_private_and_removed_on_close(
    settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings.agent_port = 9876
    settings.agent_discovery_dir = tmp_path / "discovery"
    settings.agent_launcher = str(tmp_path / "TTSNative.exe")
    settings.agent_source_root = tmp_path
    first, second = AgentState(settings), AgentState(settings)
    opened: list[tuple[int, int]] = []
    original = os.open

    def private_open(path: Path, flags: int, mode: int) -> int:
        opened.append((flags, mode))
        return original(path, flags, mode)

    with monkeypatch.context() as private:
        private.setattr(discovery.os, "open", private_open)
        first.start()
        first.start()  # a repeated start cannot replace its credential or trust a preexisting leaf
    assert opened == [(os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)]
    second.start()
    path = settings.agent_discovery_dir / first.instance_id / "instance.json"
    descriptor = json.loads(path.read_text("utf-8"))
    assert descriptor["origin"] == "http://127.0.0.1:9876" and descriptor["pid"] == os.getpid()
    assert descriptor["token"] == first.token and first.token != second.token
    assert descriptor["launcher"] == settings.agent_launcher and descriptor["sourceRoot"] == str(tmp_path.resolve())
    assert list(path.parent.iterdir()) == [path]
    second_path = path.parent.parent / second.instance_id / "instance.json"
    first.close()
    first.close()
    assert not path.exists() and second_path.is_file()
    second.close()
    assert list(settings.agent_discovery_dir.iterdir()) == []


def test_preexisting_instance_directory_is_never_trusted(settings: Settings, tmp_path: Path) -> None:
    settings.agent_port = 9876
    settings.agent_discovery_dir = tmp_path
    state = AgentState(settings)
    (tmp_path / state.instance_id).mkdir()
    state.start()
    assert not state.available
    assert not (tmp_path / state.instance_id / "instance.json").exists()


def test_cleanup_never_deletes_an_unexpected_file(settings: Settings, tmp_path: Path) -> None:
    settings.agent_port = 9876
    settings.agent_discovery_dir = tmp_path
    state = AgentState(settings)
    state.start()
    unexpected = tmp_path / state.instance_id / "unrelated.txt"
    unexpected.write_text("Keep this file.", "utf-8")
    state.close()
    assert unexpected.read_text("utf-8") == "Keep this file."


@pytest.mark.parametrize("failure", ["permission", "collision"])
def test_discovery_failure_leaves_core_reading_working_and_bridge_closed(
    settings: Settings,
    services: Services,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failure: str,
) -> None:
    settings.agent_port = 8765
    settings.agent_discovery_dir = tmp_path / "discovery"
    app = create_app(settings, services=services)
    private_path = tmp_path / "sensitive-path"
    if failure == "permission":

        def denied(settings: Settings, descriptor: dict[str, object]) -> Path:
            raise PermissionError(f"{private_path}: {descriptor['token']}")

        monkeypatch.setattr(agent_state, "publish", denied)
    else:
        (settings.agent_discovery_dir / app.state.agent.instance_id).mkdir(parents=True)
    with TestClient(app, client=("127.0.0.1", 45000), headers={"X-LTTS-Client": "web"}) as caller:
        assert caller.get("/api/health").status_code == 200
        doc = caller.post("/api/documents/text", json={"text": "The lantern shines.", "title": "Harbor"}).json()
        audio = caller.get(f"/api/documents/{doc['id']}/segments/0/audio", params={"voice": "kokoro:alpha"})
        assert audio.status_code == 200 and audio.content.startswith(b"RIFF")
        headers = {"Authorization": f"Bearer {app.state.agent.token}"}
        assert caller.get("/api/agent/v1/status", headers=headers).status_code == 404
        assert caller.post("/api/agent-reader/claim", json={"ticket": "a" * 64}).status_code == 404
        assert not app.state.agent.available
    assert "discovery unavailable" in caplog.text
    assert app.state.agent.token not in caplog.text and str(private_path) not in caplog.text
    assert not list(settings.agent_discovery_dir.glob("*/instance.json"))


def test_cleanup_failure_disables_bridge_without_logging_private_values(
    settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings.agent_port = 8765
    settings.agent_discovery_dir = tmp_path
    state = AgentState(settings)
    state.start()

    def denied(path: Path) -> None:
        raise PermissionError(f"{path}: {state.token}")

    with monkeypatch.context() as cleanup:
        cleanup.setattr(agent_state, "unpublish", denied)
        state.close()
    assert not state.available and "cleanup unavailable" in caplog.text
    assert state.token not in caplog.text and str(tmp_path) not in caplog.text
    discovery.unpublish(tmp_path / state.instance_id / "instance.json")


def test_discovery_default_locations_are_platform_owned(
    settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(discovery, "_WINDOWS", True)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert discovery.discovery_root(settings) == tmp_path / "com.ttsnative.desktop" / "agent"
    monkeypatch.setattr(discovery, "_WINDOWS", False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert discovery.discovery_root(settings) == tmp_path / "ttsnative" / "agent"
    monkeypatch.delenv("XDG_STATE_HOME")
    assert discovery.discovery_root(settings) == Path.home() / ".local" / "state" / "ttsnative" / "agent"
    state = AgentState(settings)
    state.start()
    assert "launcher" not in state.descriptor() and "sourceRoot" not in state.descriptor()
    state.close()


@pytest.mark.parametrize(
    "value",
    [
        "https://127.0.0.1:8765",
        "http://evil.example:8765",
        "http://127.0.0.1:8765/",
        "http://user@127.0.0.1:8765",
        "http://:pass@127.0.0.1:8765",
        "http://127.0.0.1:8765?q=x",
        "http://127.0.0.1:8765#ticket",
        "http://127.0.0.1:0",
        "http://[::1]:99999",
    ],
)
def test_ui_origin_validation_refuses_remote_credentials_paths_and_fragments(value: str) -> None:
    with pytest.raises(ValidationError):
        Settings(agent_ui_url=value)


@pytest.mark.parametrize("value", [None, "http://127.0.0.1:8765", "http://[::1]:8770", "http://localhost:5173"])
def test_ui_origin_validation_accepts_only_explicit_local_origins(value: str | None) -> None:
    assert Settings(agent_ui_url=value).agent_ui_url == value


def test_ipv6_loopback_instance_advertises_the_actual_listener(settings: Settings) -> None:
    settings.host = "::1"
    settings.agent_port = 9876
    state = AgentState(settings)
    assert state.origin == state.ui_url == "http://[::1]:9876"


@pytest.mark.parametrize("hostname,expected", [("127.0.0.1", "http://127.0.0.1"), ("::1", "http://[::1]")])
def test_default_http_port_round_trips_without_an_explicit_suffix(
    settings: Settings,
    hostname: str,
    expected: str,
) -> None:
    settings.host = hostname
    settings.agent_port = 80
    state = AgentState(settings)
    assert state.origin == state.ui_url == expected

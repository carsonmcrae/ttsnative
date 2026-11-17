# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Tests that installing the cloning engine's runtime survives a poor network and says why it can't.

Scope: A stalled or dropped download is tried again after a pause (which a cancel ends) and reported
once the tries run out; a certificate replaced by an inspecting proxy gets one more try with this
computer's own certificates; Windows refusing to run the download is reported at once; uv is given a
longer network timeout unless one is already set; and Windows in S mode rules the install out before
anything is downloaded, in the engine's description and when asked to install anyway. A tiny script
stands in for uv (run as ``python sync …`` in the worker project).
Does NOT belong: The wording of each reason (test_install_errors.py) or updates
(test_chatterbox_update.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from chatterbox_harness import fake_chatterbox
from ltts.config import Settings
from ltts.engines import chatterbox as chatterbox_module
from ltts.engines import chatterbox_env
from ltts.engines.device_policy import S_MODE
from ltts.errors import EngineUnavailableError
from ltts.jobs import JobCanceledError

COUNT = "import pathlib\ntries = pathlib.Path('tries')\ncount = int(tries.read_text()) + 1 if tries.exists() else 1\n"
STALLS = COUNT + (
    "tries.write_text(str(count))\n"
    "if count < {works_on}:\n"
    "    print('error: Failed to download `torch==2.11.0+cpu`')\n"
    "    print('  Caused by: Failed to fetch https://download.pytorch.org/whl/cpu/torch.whl')\n"
    "    print('  Caused by: operation timed out')\n"
    "    raise SystemExit(2)\n"
    "print('Installed 3 packages')\n"
)
INSPECTED = COUNT + (
    "import os\n"
    "tries.write_text(str(count))\n"
    "if os.environ.get('UV_SYSTEM_CERTS') != '1' or {always}:\n"
    "    print('error: Failed to fetch: `https://pypi.org/simple/hatchling/`')\n"
    "    print('  Caused by: invalid peer certificate: UnknownIssuer')\n"
    "    raise SystemExit(2)\n"
    "print('Installed with this PC\\'s certificates')\n"
)
BLOCKED = COUNT + (
    "tries.write_text(str(count))\n"
    "print('error: Failed to query Python interpreter')\n"
    "print('  Caused by: An Application Control policy has blocked this file. (os error 4551)')\n"
    "raise SystemExit(2)\n"
)
TIMEOUT = "import os\nprint('timeout', os.environ['UV_HTTP_TIMEOUT'])\n"


class Job:
    """A job context that records what it is told and can be canceled when a message appears."""

    def __init__(self, cancel_on: str | None = None) -> None:
        self.messages: list[str] = []
        self._cancel_on = cancel_on
        self._stop = False

    @property
    def canceled(self) -> bool:
        return False

    def update(self, _progress: float, message: str, **_: object) -> None:
        self.messages.append(message)
        self._stop = self._stop or (self._cancel_on is not None and self._cancel_on in message)

    def check(self) -> None:
        if self._stop:
            raise JobCanceledError


def sync(project: Path, script: str, job: Job, *, update: bool = False) -> int:
    """Run the stand-in uv; how many times it ran."""
    (project / "sync").write_text(script, encoding="utf-8")
    tries = project / "tries"
    tries.unlink(missing_ok=True)
    chatterbox_env.sync_environment(sys.executable, project, project / "venv", "cpu", job, update=update)  # type: ignore[arg-type]
    return int(tries.read_text()) if tries.exists() else 1


@pytest.fixture(autouse=True)
def short_pauses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chatterbox_env, "RETRY_DELAYS_S", (0.02, 0.0))


def test_a_stalled_download_is_tried_again_and_then_succeeds(tmp_path: Path) -> None:
    job = Job()
    assert sync(tmp_path, STALLS.format(works_on=3), job) == 3
    assert job.messages.count("Installing runtime: the connection dropped; trying again…") == 2
    assert job.messages[-1] == "Installing runtime: Installed 3 packages"


def test_a_download_that_keeps_stalling_is_reported_with_its_host(tmp_path: Path) -> None:
    job = Job()
    with pytest.raises(EngineUnavailableError) as failed:
        sync(tmp_path, STALLS.format(works_on=99), job, update=True)
    assert failed.value.code == "install_network"
    assert failed.value.message == (
        "The download couldn't reach download.pytorch.org. The connection dropped, or a firewall, proxy or "
        "filtered network is blocking it. Check the connection and try again. Your current installation was kept."
    )
    assert (tmp_path / "tries").read_text() == "3"  # the first try and one after each pause
    assert job.messages.count("Updating runtime: the connection dropped; trying again…") == 2


def test_a_cancel_ends_the_pause_before_another_try(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chatterbox_env, "RETRY_DELAYS_S", (60.0,))
    with pytest.raises(JobCanceledError):
        sync(tmp_path, STALLS.format(works_on=99), Job(cancel_on="trying again"))
    assert (tmp_path / "tries").read_text() == "1"


def test_a_replaced_certificate_gets_one_try_with_this_pcs_certificates(tmp_path: Path) -> None:
    job = Job()
    assert sync(tmp_path, INSPECTED.format(always=False), job) == 2
    assert "Installing runtime: trying again with this PC's own certificates…" in job.messages
    assert job.messages[-1] == "Installing runtime: Installed with this PC's certificates"
    with pytest.raises(EngineUnavailableError) as failed:
        sync(tmp_path, INSPECTED.format(always=True), Job())
    assert failed.value.code == "install_certificate" and "certificate for pypi.org" in failed.value.message
    assert (tmp_path / "tries").read_text() == "2"


def test_windows_blocking_the_download_is_reported_at_once(tmp_path: Path) -> None:
    with pytest.raises(EngineUnavailableError) as failed:
        sync(tmp_path, BLOCKED, Job())
    assert failed.value.code == "install_blocked" and (tmp_path / "tries").read_text() == "1"


def test_uv_waits_longer_for_a_slow_network_unless_told_otherwise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("UV_HTTP_TIMEOUT", raising=False)
    job = Job()
    sync(tmp_path, TIMEOUT, job)
    monkeypatch.setenv("UV_HTTP_TIMEOUT", "45")
    sync(tmp_path, TIMEOUT, job)
    assert job.messages == ["Installing runtime: timeout 120", "Installing runtime: timeout 45"]


def test_s_mode_rules_the_install_out_up_front(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "chatterbox-worker"
    project.mkdir()
    (project / "sync").write_text("raise SystemExit('uv must not run')\n", encoding="utf-8")
    engine = fake_chatterbox(settings, project, monkeypatch)
    assert engine.info().blocked_reason is None
    monkeypatch.setattr(chatterbox_module, "install_blocker", lambda: S_MODE)
    assert engine.info().blocked_reason == S_MODE
    with pytest.raises(EngineUnavailableError) as refused:
        engine.install(Job(), "cpu")  # type: ignore[arg-type]
    assert refused.value.code == "install_blocked" and refused.value.message == S_MODE
    assert not engine._marker.exists()

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Build and track the Chatterbox worker's isolated, locked Python environment.

Scope: Locates the pinned uv, runs ``uv sync --frozen`` for one extra (``cpu``/``cuda``) of the
worker project into the engine's venv with live job progress, fingerprints the worker's ``uv.lock``
with SHA-256, and reads/writes the ``installed.json`` marker recording which lock and extra the
environment was built from, so a changed lock (a security fix, a Dependabot bump) shows up as an
available update instead of being missed by existing installs. A failed sync is tried again when the
connection only dropped or stalled, and once with this computer's own certificates when a proxy that
inspects connections replaced the server's; what still fails is reported with its reason
(``install_errors.py``).
Does NOT belong: Model weights (``modelstore``), the worker process (``worker_client.py``) or the
engine's install/update policy (``chatterbox.py``).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ltts.common import NO_CONSOLE_WINDOW, utc_now
from ltts.config import REPO_ROOT
from ltts.engines.install_errors import explain
from ltts.errors import EngineUnavailableError
from ltts.jobs import JobContext

log = logging.getLogger("ltts.engines.chatterbox")
# The desktop app ships the worker project and keeps uv's Python downloads in the user's folder.
PROJECT_DIR = Path(os.environ.get("LTTS_WORKER_PROJECT_DIR") or REPO_ROOT / "apps" / "chatterbox-worker")
PYTHON_INSTALL_DIR = Path(os.environ.get("LTTS_UV_PYTHON_DIR") or REPO_ROOT / ".tools" / "python")
# uv gives up on a connection that is silent for 30 seconds; a slow link stalls longer than that in the
# middle of a 200 MB package.
HTTP_TIMEOUT_S = "120"
RETRY_DELAYS_S = (5.0, 15.0)  # a dropped or stalled download is tried again after each; uv keeps what it has
TAIL_LINES = 20


def find_uv() -> str | None:
    explicit = os.environ.get("LTTS_UV_BIN")
    if explicit and Path(explicit).is_file():
        return explicit
    exe = "uv.exe" if sys.platform == "win32" else "uv"
    pinned = sorted((REPO_ROOT / ".tools" / "uv").glob(f"*/{exe}"))
    return str(pinned[-1]) if pinned else shutil.which("uv")


def lock_digest(project_dir: Path) -> str | None:
    """SHA-256 of the worker's ``uv.lock``, or ``None`` when it is missing (nothing to compare with)."""
    try:
        return hashlib.sha256((project_dir / "uv.lock").read_bytes()).hexdigest()
    except OSError:
        return None


def read_marker(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_marker(path: Path, extra: str, lock_sha256: str | None, venv: Path, installed_at: str | None = None) -> None:
    """Record a verified environment. Markers written before lock tracking lack ``lockSha256``."""
    now = utc_now()
    marker = {"option": extra, "extra": extra, "lockSha256": lock_sha256, "installedAt": installed_at or now,
              "syncedAt": now, "envBytes": tree_bytes(venv)}  # fmt: skip
    staging = path.with_suffix(".tmp")
    staging.write_text(json.dumps(marker), encoding="utf-8")
    staging.replace(path)  # atomic: a crash never leaves a half-written marker behind


def _run_uv(argv: list[str], cwd: Path, env: dict[str, str], context: JobContext, doing: str) -> tuple[int, list[str]]:
    """Run uv to the end, showing its lines as progress; its exit code and the last lines it printed."""
    # Popen's encoding argument needs Python 3.6; the server requires 3.11.
    # The argv is fixed, and uv verifies every package hash against the committed lockfile.
    # nosemgrep: python.lang.compatibility.python36.python36-compatibility-Popen2
    proc = subprocess.Popen(  # noqa: S603
        argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
        errors="replace", creationflags=NO_CONSOLE_WINDOW,
    )  # fmt: skip
    tail: list[str] = []
    for line in proc.stdout or ():
        tail = [*tail[-TAIL_LINES:], line.rstrip()]
        if context.canceled:
            proc.kill()
            context.check()
        if line.strip():
            context.update(0.05, f"{doing} runtime: {line.strip()[:120]}")
    return proc.wait(), tail


def _wait(seconds: float, context: JobContext) -> None:
    """Pause before another try; a cancel ends the wait at once."""
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        context.check()
        time.sleep(min(0.2, max(until - time.monotonic(), 0.0)))


def sync_environment(uv: str, project_dir: Path, venv: Path, extra: str, context: JobContext, *, update: bool) -> None:
    """Make ``venv`` match the committed lock exactly; uv only replaces the packages that differ.

    Nothing is deleted on failure: uv downloads and hash-checks every changed package before it modifies
    the environment, so a dropped connection or a full disk during download leaves the old packages in place.
    """
    env = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(venv),
           "UV_PYTHON_INSTALL_DIR": str(PYTHON_INSTALL_DIR), "UV_NO_PROGRESS": "1"}  # fmt: skip
    env.setdefault("UV_HTTP_TIMEOUT", HTTP_TIMEOUT_S)
    argv = [uv, "sync", "--frozen", "--no-dev", "--project", str(project_dir), "--extra", extra]
    doing = "Updating" if update else "Installing"
    delays = list(RETRY_DELAYS_S)
    while True:
        code, tail = _run_uv(argv, project_dir, env, context, doing)
        if code == 0:
            return
        failure = explain(tail, update=update)
        log.error("chatterbox environment sync failed (%s):\n%s", failure.code, "\n".join(tail))
        if failure.certificate and "UV_SYSTEM_CERTS" not in env:
            # A proxy that inspects connections signs them with a certificate this PC trusts and uv's own list
            # doesn't know; packages are still checked against the hashes in the committed lock.
            env["UV_SYSTEM_CERTS"] = "1"
            context.update(0.05, f"{doing} runtime: trying again with this PC's own certificates…", force=True)
        elif failure.transient and delays:
            context.update(0.05, f"{doing} runtime: the connection dropped; trying again…", force=True)
            _wait(delays.pop(0), context)
        else:
            raise EngineUnavailableError(failure.message, code=failure.code)


def tree_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())

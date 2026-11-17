# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Edge-case tests for the worker protocol client that a well-behaved worker never triggers.

Scope: Discarding private worker stderr, a process that could not be started, a pipe that
breaks while a request is written, stale replies from an abandoned request, and stopping workers
that have no stdin, ignore the shutdown request or have already exited.
Does NOT belong: Normal round trips, crashes, timeouts and idle unloading (test_engines_cli.py).
"""

from __future__ import annotations

import logging
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from ltts.engines.worker_client import WorkerClient, WorkerError

FAKE_WORKER = Path(__file__).with_name("fake_worker.py")


class Pipe:
    def __init__(self, *, broken: bool = False) -> None:
        self.broken = broken
        self.written: list[str] = []

    def write(self, text: str) -> None:
        if self.broken:
            raise BrokenPipeError
        self.written.append(text)

    def flush(self) -> None:
        return None


class FakeProcess:
    def __init__(self, stdin: Pipe | None, *, running: bool = True, ignores_shutdown: bool = False) -> None:
        self.stdin = stdin
        self.stderr: Any = None
        self._running = running
        self._ignores_shutdown = ignores_shutdown
        self.killed = False

    def poll(self) -> int | None:
        return None if self._running else 0

    def wait(self, timeout: float) -> int:
        if self._ignores_shutdown:
            raise subprocess.TimeoutExpired("worker", timeout)
        self._running = False
        return 0

    def kill(self) -> None:
        self.killed = True
        self._running = False


@pytest.fixture
def client(tmp_path: Path) -> Iterator[WorkerClient]:
    worker = WorkerClient([sys.executable, "-I", str(FAKE_WORKER)], {}, tmp_path, idle_unload_s=60)
    yield worker
    worker.stop()


@pytest.mark.parametrize("stderr", [None, ["\n", "private passage\n", r"C:\private\original recording.wav" * 600]])
def test_private_worker_stderr_is_drained_without_logging(stderr: Any, caplog: pytest.LogCaptureFixture) -> None:
    process = FakeProcess(None)
    process.stderr = iter(stderr) if stderr else None
    with caplog.at_level(logging.DEBUG, logger="ltts.worker"):
        WorkerClient._read_stderr(process)  # type: ignore[arg-type]
    assert not caplog.records
    if process.stderr is not None:
        assert list(process.stderr) == []


def test_worker_failure_is_logged_at_normal_levels_without_private_reply_or_request_fields(
    client: WorkerClient, caplog: pytest.LogCaptureFixture
) -> None:
    private = r"private passage from C:\people\original recording.wav"
    client._proc = FakeProcess(Pipe())  # type: ignore[assignment]
    client._replies.put(
        {
            "id": 1,
            "ok": False,
            "error": "PermissionError",
            "errno": 13,
            "winerror": 5,
            "frames": [{"module": "chatterbox.tts_turbo", "line": 157, "filename": private}],
            "message": private,
            "filename": private,
        }
    )
    with caplog.at_level(logging.INFO, logger="ltts.worker"), pytest.raises(WorkerError) as failed:
        client.call("load", 1, text=private)
    assert failed.value.message == "The voice engine reported an error." and failed.value.details == {}
    [record] = caplog.records
    assert record.levelno == logging.ERROR and record.worker_request_id == 1
    assert (record.operation, record.error_type, record.errno, record.winerror) == ("load", "PermissionError", 13, 5)
    assert record.frames == ["chatterbox.tts_turbo(157)"]
    assert private not in repr(record.__dict__) and private not in str(failed.value)


def test_a_worker_that_could_not_start_is_reported(client: WorkerClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "_start", lambda: None)
    with pytest.raises(WorkerError, match="could not be started"):
        client.call("ping", 1)


def test_a_broken_pipe_while_sending_stops_the_worker(client: WorkerClient) -> None:
    process = FakeProcess(Pipe(broken=True))
    client._proc = process  # type: ignore[assignment]
    with pytest.raises(WorkerError, match="stopped unexpectedly"):
        client.call("ping", 1)
    assert process.killed and client._proc is None


def test_stale_replies_from_abandoned_requests_are_skipped(client: WorkerClient) -> None:
    assert client.call("ping", 10)["ok"]
    client._replies.put({"id": 999, "ok": False, "error": "LateReply"})  # from a request that timed out
    reply = client.call("ping", 10)
    assert reply["ok"] and reply["op"] == "ping"


@pytest.mark.parametrize(
    ("process", "killed", "shutdown_sent"),
    [
        (FakeProcess(None), True, False),  # no stdin to ask it to stop
        (FakeProcess(Pipe(), ignores_shutdown=True), True, True),
        (FakeProcess(Pipe()), False, True),  # stops when asked
        (FakeProcess(Pipe(), running=False), False, False),  # already exited
    ],
)
def test_stop_asks_politely_then_kills(
    client: WorkerClient, process: FakeProcess, killed: bool, shutdown_sent: bool
) -> None:
    client._proc = process  # type: ignore[assignment]
    client.loaded = {"device": "cpu"}
    client.stop()
    assert process.killed is killed and client.loaded is None and client._proc is None
    assert bool(process.stdin and process.stdin.written) is shutdown_sent

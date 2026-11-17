# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Regressions for useful worker failure diagnostics that preserve private input.

Scope: The isolated worker's serializer, server-side validation, bounded stacks and OS errors,
and the real JSON-lines load handler failing with a controlled permission error, without models.
Does NOT belong: Worker process lifecycle or real Chatterbox inference.
"""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path
from types import FunctionType, SimpleNamespace
from typing import Any

import pytest

from ltts.config import REPO_ROOT
from ltts.engines.worker_diagnostics import failure_fields

WORKER_SOURCE = REPO_ROOT / "apps" / "chatterbox-worker" / "src"
PRIVATE = "PRIVATE_PASSAGE_402"
RECORDING = r"C:\private-person\PRIVATE ORIGINAL RECORDING.wav"


@pytest.fixture(scope="module")
def serializer() -> Any:
    namespace = runpy.run_path(str(WORKER_SOURCE / "ltts_chatterbox_worker" / "diagnostics.py"))
    return namespace["failure_details"]


def details_from_private_frame(serializer: Any, problem: Exception, module: Any, spec: str | None = None) -> Any:
    def fail() -> None:
        raise problem

    safe_globals = {"__name__": module, "__spec__": SimpleNamespace(name=spec)}
    private_frame = FunctionType(fail.__code__.replace(co_filename=RECORDING), safe_globals, closure=fail.__closure__)
    try:
        private_frame()
    except Exception as exc:  # noqa: BLE001
        return serializer(exc)
    raise AssertionError("the controlled failure did not raise")


def test_permission_failure_keeps_useful_metadata_and_omits_messages_paths_notes_and_source(serializer: Any) -> None:
    problem = PermissionError(13, PRIVATE, RECORDING)
    problem.winerror = 5
    problem.add_note(PRIVATE)
    problem.__cause__ = ValueError(PRIVATE)
    details = details_from_private_frame(serializer, problem, "chatterbox.tts_turbo")
    assert details["error"] == "PermissionError" and (details["errno"], details["winerror"]) == (13, 5)
    assert len(details["frames"]) == 1 and details["frames"][0]["module"] == "chatterbox.tts_turbo"
    assert details["frames"][0]["line"] > 0
    assert PRIVATE not in json.dumps(details) and RECORDING not in json.dumps(details)
    assert set(details) == {"error", "errno", "winerror", "frames"}


@pytest.mark.parametrize("module", [None, RECORDING, "torch.bad/name", "torch." + "x" * 160, "private_document"])
def test_worker_omits_frames_outside_approved_module_identifiers(serializer: Any, module: Any) -> None:
    assert details_from_private_frame(serializer, ValueError(PRIVATE), module)["frames"] == []


@pytest.mark.parametrize("spec", [None, RECORDING, "ltts_chatterbox_worker.__main__"])
def test_worker_main_uses_its_canonical_module_instead_of_its_file_path(serializer: Any, spec: str | None) -> None:
    frames = details_from_private_frame(serializer, RuntimeError(PRIVATE), "__main__", spec)["frames"]
    assert [frame["module"] for frame in frames] == ([spec] if spec == "ltts_chatterbox_worker.__main__" else [])


@pytest.mark.parametrize("value", [None, PRIVATE, True, -(2**31) - 1, 2**32])
def test_worker_drops_non_numeric_or_unbounded_os_errors(serializer: Any, value: Any) -> None:
    problem = RuntimeError(PRIVATE)
    problem.errno = value  # type: ignore[attr-defined]
    problem.winerror = value  # type: ignore[attr-defined]
    assert serializer(problem) == {"error": "RuntimeError", "frames": []}


def _deep_failure(depth: int, problem: Exception) -> None:
    if depth:
        _deep_failure(depth - 1, problem)
    raise problem


def test_worker_bounds_stacks_and_uses_builtin_ancestor_for_private_exception_names(serializer: Any) -> None:
    problem = type(PRIVATE, (RuntimeError,), {})(PRIVATE)
    namespace: dict[str, Any] = {"__name__": "torch.serialization"}
    nested = FunctionType(_deep_failure.__code__.replace(co_filename=RECORDING), namespace)
    namespace["_deep_failure"] = nested
    try:
        nested(20, problem)
    except RuntimeError as exc:
        details = serializer(exc)
    assert details["error"] == "RuntimeError" and len(details["frames"]) == 8
    assert all(frame["module"] == "torch.serialization" for frame in details["frames"])
    assert PRIVATE not in json.dumps(details) and RECORDING not in json.dumps(details)


@pytest.mark.parametrize("error", [None, 9, PRIVATE, "open", "SystemExit"])
def test_server_drops_unknown_exception_names_and_private_legacy_messages(error: Any) -> None:
    fields = failure_fields(PRIVATE, {"error": error, "message": PRIVATE, "filename": RECORDING})
    assert fields == {"operation": "unknown", "error_type": "unknown"}


@pytest.mark.parametrize(
    "frame",
    [
        None,
        {"module": None, "line": 1},
        {"module": RECORDING, "line": 1},
        {"module": "torch." + "x" * 160, "line": 1},
        {"module": "private_document", "line": 1},
        {"module": "torch.bad/name", "line": 1},
        {"module": "torch", "line": True},
        {"module": "torch", "line": PRIVATE},
        {"module": "torch", "line": 0},
        {"module": "torch", "line": 10_000_001},
    ],
)
def test_server_rejects_untrusted_frame_fields(frame: Any) -> None:
    assert failure_fields("load", {"frames": [frame]})["frames"] == []


@pytest.mark.parametrize("value", [None, PRIVATE, True, -(2**31) - 1, 2**32])
def test_server_drops_invalid_os_error_values(value: Any) -> None:
    assert failure_fields("load", {"errno": value, "winerror": value}) == {
        "operation": "load",
        "error_type": "unknown",
    }


def test_server_accepts_only_bounded_diagnostics_and_never_keeps_extra_worker_fields() -> None:
    fields = failure_fields(
        "synthesize",
        {
            "error": "ValueError",
            "errno": -(2**31),
            "winerror": 2**32 - 1,
            "frames": [{"module": "torch.serialization", "line": 29, "text": PRIVATE}] * 20,
            "message": PRIVATE,
            "request": {"text": PRIVATE, "reference": RECORDING},
        },
    )
    assert fields == {
        "operation": "synthesize",
        "error_type": "ValueError",
        "errno": -(2**31),
        "winerror": 2**32 - 1,
        "frames": ["torch.serialization(29)"] * 8,
    }


def test_real_worker_load_failure_emits_safe_diagnostics_without_a_raw_traceback(tmp_path: Path) -> None:
    script = """
import runpy, sys, types
sys.path.insert(0, sys.argv[1])
sys.modules['torch'] = types.ModuleType('torch')
def deny(*args):
    problem = PermissionError(13, 'PRIVATE_PASSAGE_402', r'C:\\private-person\\PRIVATE ORIGINAL RECORDING.wav')
    problem.winerror = 5
    raise problem
stub = types.ModuleType('chatterbox.tts_turbo')
deny = types.FunctionType(deny.__code__.replace(co_filename='PRIVATE ORIGINAL RECORDING.wav'), stub.__dict__)
stub.ChatterboxTurboTTS = types.SimpleNamespace(from_local=deny)
sys.modules[stub.__name__] = stub
runpy.run_module('ltts_chatterbox_worker', run_name='__main__', alter_sys=True)
"""
    done = subprocess.run(  # noqa: S603 — fixed isolated Python and controlled worker/stub source
        [sys.executable, "-I", "-c", script, str(WORKER_SOURCE)],
        input=json.dumps({"id": 1, "op": "load", "device": "cpu", "modelDir": str(tmp_path)}) + '\n{"op":"shutdown"}\n',
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    reply = json.loads(done.stdout)
    assert reply["id"] == 1 and reply["ok"] is False and reply["error"] == "PermissionError"
    assert reply["errno"] == 13 and reply["winerror"] == 5
    assert {frame["module"] for frame in reply["frames"]} >= {
        "ltts_chatterbox_worker.__main__",
        "chatterbox.tts_turbo",
    }
    assert "message" not in reply and "Traceback" not in done.stderr
    assert (
        PRIVATE not in done.stdout + done.stderr and "PRIVATE ORIGINAL RECORDING.wav" not in done.stdout + done.stderr
    )

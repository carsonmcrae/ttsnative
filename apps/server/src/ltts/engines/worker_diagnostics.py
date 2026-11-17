# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Validate the worker's privacy-preserving failure metadata before logging it.

Scope: Fixed operation names, built-in exception classes, numeric OS errors and bounded module/line
locations. Treat all other worker output, including messages and filenames, as private and omit it.
Does NOT belong: User-facing errors or the worker process lifecycle (worker_client.py).
"""

from __future__ import annotations

import builtins
import re
from typing import Any

_OPERATIONS = frozenset(
    {
        "load",
        "synthesize",
        "measure",
        "build",
        "style",
        "audition",
        "tune_start",
        "tune_epoch",
        "tune_save",
        "tune_stop",
        "ping",
    }
)
_MODULE = re.compile(
    r"(?:ltts_chatterbox_worker|chatterbox|torch|torchaudio|numpy|soundfile|librosa|safetensors|"
    r"transformers|diffusers|huggingface_hub|perth|omegaconf|pathlib|tempfile|shutil|os|io|importlib|ctypes)"
    r"(?:\.[A-Za-z_][A-Za-z_0-9]*){0,12}\Z"
)


def _location(frame: Any) -> str | None:
    if not isinstance(frame, dict):
        return None
    module, line = frame.get("module"), frame.get("line")
    if not isinstance(module, str) or len(module) > 160 or _MODULE.fullmatch(module) is None:
        return None
    if type(line) is not int or not 1 <= line <= 10_000_000:
        return None
    return f"{module}({line})"


def failure_fields(operation: str, reply: dict[str, Any]) -> dict[str, Any]:
    """Legacy or malformed replies still produce a useful generic event, never raw output."""
    name = reply.get("error")
    error = getattr(builtins, name, None) if isinstance(name, str) else None
    fields: dict[str, Any] = {
        "operation": operation if operation in _OPERATIONS else "unknown",
        "error_type": error.__name__ if isinstance(error, type) and issubclass(error, Exception) else "unknown",
    }
    for key in ("errno", "winerror"):
        value = reply.get(key)
        if type(value) is int and -(2**31) <= value <= 2**32 - 1:
            fields[key] = value
    frames = reply.get("frames")
    if isinstance(frames, list):
        fields["frames"] = [location for frame in frames[:8] if (location := _location(frame)) is not None]
    return fields

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Describe worker failures without recording the input that caused them.

Scope: Built-in exception classes, bounded numeric OS errors and approved module/line locations.
Never include exception messages, notes, filenames, source lines, locals or request contents.
Does NOT belong: Reporting failures to the user or forwarding third-party stderr.
"""

from __future__ import annotations

import builtins
import re
import traceback
from collections import deque
from typing import Any

_MODULE = re.compile(
    r"(?:ltts_chatterbox_worker|chatterbox|torch|torchaudio|numpy|soundfile|librosa|safetensors|"
    r"transformers|diffusers|huggingface_hub|perth|omegaconf|pathlib|tempfile|shutil|os|io|importlib|ctypes)"
    r"(?:\.[A-Za-z_][A-Za-z_0-9]*){0,12}\Z"
)
_MAX_FRAMES = 8


def failure_details(exc: Exception) -> dict[str, Any]:
    """Return only diagnostic fields safe to persist, even when a library echoes private input."""
    error = next(base.__name__ for base in type(exc).__mro__ if getattr(builtins, base.__name__, None) is base)
    frames: deque[dict[str, Any]] = deque(maxlen=_MAX_FRAMES)
    for frame, line in traceback.walk_tb(exc.__traceback__):
        module = frame.f_globals.get("__name__")
        if module == "__main__":
            module = getattr(frame.f_globals.get("__spec__"), "name", None)
        if isinstance(module, str) and len(module) <= 160 and _MODULE.fullmatch(module):
            frames.append({"module": module, "line": line})
    details: dict[str, Any] = {"error": error, "frames": list(frames)}
    for field in ("errno", "winerror"):
        value = getattr(exc, field, None)
        if type(value) is int and -(2**31) <= value <= 2**32 - 1:
            details[field] = value
    return details

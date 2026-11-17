# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: How the cloning worker process is started: its command line and its environment.

Scope: The command line runs the worker from the app's own copy of its source (``<project>/src``),
named each time, instead of through the path recorded when the environment was installed: the
Microsoft Store installs every version of the app in a new folder, so a recorded path stops existing
after an update. The environment is the server's without the server's own settings, in UTF-8 and
offline, and, when the server ships a Visual C++ runtime (the desktop app on Windows), names its folder
for the worker to load from before PyTorch (``LTTS_VC_RUNTIME_DIR``) and puts it first on PATH. PATH
alone is not enough: Windows doesn't search it for DLLs inside a Store-packaged app.
Does NOT belong: The engine's requests (``chatterbox.py``) or the stdio protocol (``worker_client.py``).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

# PyTorch needs the Visual C++ runtime, which a Windows PC lacks until something installs Microsoft's
# redistributable, and the worker's Python ships only part of it; the desktop app's runtime ships it whole.
VC_RUNTIME_DLL = "msvcp140.dll"
VC_RUNTIME_DIR_ENV = "LTTS_VC_RUNTIME_DIR"
WORKER_MODULE = "ltts_chatterbox_worker"
_BOOTSTRAP = (
    "import runpy, sys; sys.path.insert(0, sys.argv[1]); "
    f"runpy.run_module({WORKER_MODULE!r}, run_name='__main__', alter_sys=True)"
)


def worker_argv(python: Path, project_dir: Path) -> list[str]:
    """The fixed command that starts the worker with ``python`` from ``project_dir``'s source."""
    return [str(python), "-I", "-c", _BOOTSTRAP, str(project_dir / "src")]


def worker_environment(base: Mapping[str, str], runtime_dir: Path) -> dict[str, str]:
    """The worker's environment: the server's without its own settings, in UTF-8 and offline, with the
    server's Visual C++ runtime named and first on PATH when it ships one (the desktop app on Windows)."""
    env = {k: v for k, v in base.items() if not k.startswith(("LTTS_", "UV_"))}
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "HF_HUB_OFFLINE": "1"})
    if (runtime_dir / VC_RUNTIME_DLL).is_file():
        key = next((k for k in env if k.upper() == "PATH"), "PATH")  # Windows spells it "Path"
        env[key] = os.pathsep.join(part for part in (str(runtime_dir), env.get(key)) if part)
        env[VC_RUNTIME_DIR_ENV] = str(runtime_dir)
    return env

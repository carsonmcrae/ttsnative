# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: How the cloning worker process is started: its command line and its environment.

Scope: The command line runs the worker from the app's own copy of its source (``<project>/src``),
named each time, instead of through the path recorded when the environment was installed: the
Microsoft Store installs every version of the app in a new folder, so a recorded path stops existing
after an update. The environment is the server's without the server's own settings, in UTF-8 and
offline, and, when the server ships a Visual C++ runtime (the desktop app on Windows), copies its DLLs
into the engine's user folder and names that folder for the worker to load before PyTorch
(``LTTS_VC_RUNTIME_DIR``). The downloaded Python cannot load those DLLs from the Store's protected
install folder. PATH alone is not enough: Windows doesn't search it for DLLs inside a packaged app.
Does NOT belong: The engine's requests (``chatterbox.py``) or the stdio protocol (``worker_client.py``).
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

from ltts.errors import EngineUnavailableError

# PyTorch needs the Visual C++ runtime, which a Windows PC lacks until something installs Microsoft's
# redistributable, and the worker's Python ships only part of it; the desktop app's runtime ships it whole.
VC_RUNTIME_DLL = "msvcp140.dll"
VC_RUNTIME_DLLS = ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "msvcp140_1.dll")
VC_RUNTIME_DIR_ENV = "LTTS_VC_RUNTIME_DIR"
WORKER_MODULE = "ltts_chatterbox_worker"
_BOOTSTRAP = (
    "import runpy, sys; sys.path.insert(0, sys.argv[1]); "
    f"runpy.run_module({WORKER_MODULE!r}, run_name='__main__', alter_sys=True)"
)


def worker_argv(python: Path, project_dir: Path) -> list[str]:
    """The fixed command that starts the worker with ``python`` from ``project_dir``'s source."""
    return [str(python), "-I", "-c", _BOOTSTRAP, str(project_dir / "src")]


def prepare_vc_runtime(runtime_dir: Path, engine_root: Path) -> Path:
    """Copy the app's C++ runtime where the downloaded worker can load it.

    A Store package's DLLs can be read but not loaded by the external Python. Publish a complete,
    content-addressed copy in the engine's user folder; an update never overwrites a mapped DLL.
    Without a bundled runtime, the source/browser install keeps using its existing environment.
    """
    if not (runtime_dir / VC_RUNTIME_DLL).is_file():
        return runtime_dir
    files = {name: (runtime_dir / name).read_bytes() for name in VC_RUNTIME_DLLS}
    digest = hashlib.sha256()
    for name, data in files.items():
        digest.update(name.encode("ascii"))
        digest.update(hashlib.sha256(data).digest())
    destination = engine_root / "vc-runtime" / digest.hexdigest()
    if not destination.is_dir():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".copy-", dir=destination.parent) as temporary:
            staging = Path(temporary)
            for name, data in files.items():
                (staging / name).write_bytes(data)
            try:
                staging.rename(destination)
            except OSError:
                if not destination.is_dir():
                    raise
                # Another process published the same content first; verify its copy below.
    if not all(
        (destination / name).is_file() and (destination / name).read_bytes() == data for name, data in files.items()
    ):
        raise EngineUnavailableError(
            "Chatterbox's local runtime copy is damaged. "
            "Remove and reinstall Chatterbox from Settings → Engines & models.",
            code="engine_runtime_damaged",
        )
    return destination


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

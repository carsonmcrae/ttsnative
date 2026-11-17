# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Compatibility shims for third-party packages the worker loads.

Scope: Provides ``pkg_resources.resource_filename`` for the Perth watermarker (imported by Chatterbox),
which still imports it although setuptools 81 and later no longer ship ``pkg_resources``. Only that one
function is provided, backed by ``importlib.resources``; a real ``pkg_resources``, if present, wins.
Loads the desktop app's Visual C++ runtime by full path before PyTorch looks for it by name: a PC
without Microsoft's redistributable has it nowhere else, and inside a Store-packaged app Windows doesn't
search PATH for DLLs, so naming the folder on PATH (enough for the direct install) finds nothing there.
Does NOT belong: The JSON-lines protocol and model handling (``__main__``).
"""

from __future__ import annotations

# importlib.resources.files needs Python 3.9; this worker requires 3.11.
# nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2
import importlib.resources
import importlib.util
import os
import sys
import types
from collections.abc import Callable

# The server names the folder that holds its Visual C++ runtime (the desktop app ships one).
VC_RUNTIME_DIR_ENV = "LTTS_VC_RUNTIME_DIR"
VC_RUNTIME_DLLS = ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "msvcp140_1.dll")
Loader = tuple[Callable[[str], bool], Callable[[str], object]]  # (is a DLL of this name loaded, load this path)


def resource_filename(package: str, resource: str) -> str:
    """Filesystem path of ``resource`` inside an installed (non-zipped) package."""
    return str(importlib.resources.files(package).joinpath(resource))


def install_pkg_resources_shim() -> bool:
    """Registers a minimal ``pkg_resources`` module unless a real one is importable.

    Returns True when the shim was installed.
    """
    if "pkg_resources" in sys.modules or importlib.util.find_spec("pkg_resources") is not None:
        return False
    shim = types.ModuleType("pkg_resources")
    shim.__dict__["resource_filename"] = resource_filename
    sys.modules["pkg_resources"] = shim
    return True


def _windows_loader() -> Loader:
    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    return (lambda name: bool(kernel32.GetModuleHandleW(name))), ctypes.WinDLL


def preload_vc_runtime(folder: str | None, loader: Loader | None = None) -> list[str]:
    """Loads the Visual C++ runtime DLLs in ``folder`` by full path; returns the names it loaded.

    A DLL that is already loaded answers every later lookup by name, wherever Windows would or wouldn't
    search. One the process already has (Python brings ``vcruntime140.dll``) is left as it is, and a
    file that is missing or won't load is skipped: PyTorch then reports the missing runtime itself.
    """
    if not folder or (loader is None and sys.platform != "win32"):
        return []
    is_loaded, load = loader or _windows_loader()
    done: list[str] = []
    for name in VC_RUNTIME_DLLS:
        path = os.path.join(folder, name)
        if is_loaded(name) or not os.path.isfile(path):
            continue
        try:
            load(path)
        except OSError:
            continue
        done.append(name)
    return done

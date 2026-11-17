# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Tests for the cloning worker's start-up shim that loads the app's Visual C++ runtime.

Scope: ``compat.py`` of the worker project, loaded by path (the worker isn't installed in the server's
environment): the DLLs in the named folder are loaded by full path, in order, leaving out the ones the
process already has, the ones the folder lacks and the ones that won't load; nothing happens without a
folder or away from Windows; and on Windows the real loader recognises a loaded DLL and survives a file
that isn't one.
Does NOT belong: How the server names the folder (test_engine_runtime.py) or PyTorch itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from ltts.config import REPO_ROOT

COMPAT = REPO_ROOT / "apps" / "chatterbox-worker" / "src" / "ltts_chatterbox_worker" / "compat.py"


@pytest.fixture(scope="module")
def compat() -> ModuleType:
    spec = importlib.util.spec_from_file_location("worker_compat_under_test", COMPAT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_runtime_is_loaded_by_full_path_before_anything_looks_for_it_by_name(
    compat: ModuleType, tmp_path: Path
) -> None:
    for name in ("vcruntime140.dll", "msvcp140.dll", "msvcp140_1.dll"):  # no vcruntime140_1.dll in this folder
        (tmp_path / name).write_bytes(b"")
    asked: list[str] = []

    def load(path: str) -> None:
        asked.append(path)
        if path.endswith("msvcp140_1.dll"):
            raise OSError("not a valid Win32 application")

    loaded = compat.preload_vc_runtime(str(tmp_path), (lambda name: name == "vcruntime140.dll", load))
    assert loaded == ["msvcp140.dll"]  # Python already had vcruntime140.dll, and msvcp140_1.dll wouldn't load
    assert asked == [str(tmp_path / "msvcp140.dll"), str(tmp_path / "msvcp140_1.dll")]
    assert compat.VC_RUNTIME_DIR_ENV == "LTTS_VC_RUNTIME_DIR"


def test_nothing_is_loaded_without_a_folder_or_away_from_windows(
    compat: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert compat.preload_vc_runtime(None) == [] and compat.preload_vc_runtime("") == []
    (tmp_path / "msvcp140.dll").write_bytes(b"")
    monkeypatch.setattr(compat.sys, "platform", "linux")
    assert compat.preload_vc_runtime(str(tmp_path)) == []


@pytest.mark.skipif(sys.platform != "win32", reason="the real loader is Windows' own")
def test_on_windows_a_loaded_dll_is_recognised_and_a_broken_file_is_skipped(compat: ModuleType, tmp_path: Path) -> None:
    is_loaded, _load = compat._windows_loader()
    assert is_loaded("kernel32.dll") and not is_loaded("no-such-library-ttsnative.dll")
    (tmp_path / "msvcp140_1.dll").write_bytes(b"not a library")
    assert "msvcp140_1.dll" not in compat.preload_vc_runtime(str(tmp_path))

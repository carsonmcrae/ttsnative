# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Prove that a downloaded worker uses an intact, local copy of the app's C++ runtime.

Scope: Exact bundled bytes, reuse across package-folder changes, immutable copies on updates,
interrupted/concurrent publication, rejection of damaged copies, and the engine's worker environment.
Does NOT belong: Windows' DLL loader (test_worker_compat.py) or real model inference.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from ltts.config import Settings
from ltts.engines import chatterbox
from ltts.engines.chatterbox import ChatterboxEngine
from ltts.engines.worker_launch import VC_RUNTIME_DIR_ENV, VC_RUNTIME_DLLS, prepare_vc_runtime
from ltts.errors import EngineUnavailableError
from ltts.modelstore.store import ModelStore


def bundled_runtime(folder: Path) -> dict[str, bytes]:
    folder.mkdir(parents=True)
    files = {name: f"bundled {name}".encode() for name in VC_RUNTIME_DLLS}
    for name, data in files.items():
        (folder / name).write_bytes(data)
    return files


def test_source_install_without_bundled_cpp_runtime_creates_no_copy(tmp_path: Path) -> None:
    runtime, engine = tmp_path / "python", tmp_path / "engine"
    runtime.mkdir()
    assert prepare_vc_runtime(runtime, engine) == runtime
    assert not engine.exists()


def test_runtime_copy_is_exact_and_reused_across_package_folder_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original, moved, engine = tmp_path / "package-one", tmp_path / "package-two", tmp_path / "engine"
    files = bundled_runtime(original)
    bundled_runtime(moved)
    (original / "unrelated.dll").write_bytes(b"not part of the C++ runtime")
    copied = prepare_vc_runtime(original, engine)
    assert copied.parent == engine / "vc-runtime" and len(copied.name) == 64
    assert {file.name: file.read_bytes() for file in copied.iterdir()} == files
    for file in copied.iterdir():
        file.touch()
    timestamps = {file.name: file.stat().st_mtime_ns for file in copied.iterdir()}

    def no_rewrite(path: Path, data: bytes) -> int:
        pytest.fail("an unchanged runtime must not rewrite a potentially mapped DLL")

    monkeypatch.setattr(Path, "write_bytes", no_rewrite)
    assert prepare_vc_runtime(moved, engine) == copied
    assert {file.name: file.stat().st_mtime_ns for file in copied.iterdir()} == timestamps


def test_changed_runtime_uses_another_directory_without_replacing_old_dlls(tmp_path: Path) -> None:
    runtime, engine = tmp_path / "package", tmp_path / "engine"
    old_files = bundled_runtime(runtime)
    old = prepare_vc_runtime(runtime, engine)
    changed = VC_RUNTIME_DLLS[2]
    (runtime / changed).write_bytes(b"new Microsoft runtime")
    new = prepare_vc_runtime(runtime, engine)
    assert new != old and new.parent == old.parent
    assert {file.name: file.read_bytes() for file in old.iterdir()} == old_files
    assert (new / changed).read_bytes() == b"new Microsoft runtime"
    assert sorted(path.name for path in old.parent.iterdir()) == sorted([old.name, new.name])


def test_missing_bundled_file_does_not_publish_an_incomplete_runtime(tmp_path: Path) -> None:
    runtime, engine = tmp_path / "package", tmp_path / "engine"
    bundled_runtime(runtime)
    (runtime / VC_RUNTIME_DLLS[0]).unlink()
    with pytest.raises(FileNotFoundError):
        prepare_vc_runtime(runtime, engine)
    assert not engine.exists()


@pytest.mark.parametrize("damage", ["missing", "changed"])
def test_damaged_cached_runtime_is_rejected(tmp_path: Path, damage: str) -> None:
    runtime, engine = tmp_path / "package", tmp_path / "engine"
    files = bundled_runtime(runtime)
    copied = prepare_vc_runtime(runtime, engine)
    target = copied / VC_RUNTIME_DLLS[0]
    if damage == "missing":
        target.unlink()
    else:
        target.write_bytes(b"damaged")
    with pytest.raises(EngineUnavailableError) as error:
        prepare_vc_runtime(runtime, engine)
    assert error.value.code == "engine_runtime_damaged"
    assert {file.name: file.read_bytes() for file in runtime.iterdir()} == files


def test_interrupted_copy_publishes_nothing_and_a_retry_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime, engine = tmp_path / "package", tmp_path / "engine"
    files = bundled_runtime(runtime)
    write = Path.write_bytes

    def fail_second_file(path: Path, data: bytes) -> int:
        if path.name == VC_RUNTIME_DLLS[1]:
            raise OSError("disk full")
        return write(path, data)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_bytes", fail_second_file)
        with pytest.raises(OSError, match="disk full"):
            prepare_vc_runtime(runtime, engine)
    assert list((engine / "vc-runtime").iterdir()) == []
    copied = prepare_vc_runtime(runtime, engine)
    assert {file.name: file.read_bytes() for file in copied.iterdir()} == files


def test_another_process_can_publish_the_same_runtime_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime, engine = tmp_path / "package", tmp_path / "engine"
    files = bundled_runtime(runtime)

    def publish_first(staging: Path, destination: Path) -> None:
        shutil.copytree(staging, destination)
        raise FileExistsError("another worker published it")

    monkeypatch.setattr(Path, "rename", publish_first)
    copied = prepare_vc_runtime(runtime, engine)
    assert {file.name: file.read_bytes() for file in copied.iterdir()} == files
    assert list(copied.parent.iterdir()) == [copied]


def test_failed_publication_removes_staging_and_preserves_the_bundled_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime, engine = tmp_path / "package", tmp_path / "engine"
    files = bundled_runtime(runtime)

    def denied(staging: Path, destination: Path) -> None:
        raise PermissionError("cannot publish")

    monkeypatch.setattr(Path, "rename", denied)
    with pytest.raises(PermissionError, match="cannot publish"):
        prepare_vc_runtime(runtime, engine)
    assert list((engine / "vc-runtime").iterdir()) == []
    assert {file.name: file.read_bytes() for file in runtime.iterdir()} == files


def test_chatterbox_worker_receives_the_copied_runtime_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / "package" / "runtime" / "python"
    files = bundled_runtime(runtime)
    settings = Settings(data_dir=tmp_path / "data")
    store = ModelStore(settings.resolved_models_dir, reserve_mb=0)
    engine = ChatterboxEngine(settings, store, tmp_path / "package" / "runtime" / "worker")
    captured: dict[str, Any] = {}

    class Worker:
        loaded = None

        def __init__(self, argv: list[str], env: dict[str, str], cwd: Path, idle_unload_s: float):
            captured.update(argv=argv, env=env, cwd=cwd)

        def call(self, op: str, timeout_s: float, **fields: Any) -> dict[str, Any]:
            captured.update(op=op, fields=fields)
            return {"device": "cpu"}

    monkeypatch.setattr(chatterbox.sys, "executable", str(runtime / "ttsnative-backend.exe"))
    monkeypatch.setattr(chatterbox, "WorkerClient", Worker)
    assert engine._ensure_worker("cpu") == {"device": "cpu"}
    copied = Path(captured["env"][VC_RUNTIME_DIR_ENV])
    assert copied.parent == settings.resolved_engines_dir / "chatterbox" / "vc-runtime"
    assert copied != runtime
    assert {file.name: file.read_bytes() for file in copied.iterdir()} == files
    assert captured["cwd"] == settings.resolved_engines_dir / "chatterbox"
    assert captured["op"] == "load" and captured["fields"]["device"] == "cpu"

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Tests for saying why the cloning engine's runtime could not be installed.

Scope: Sorting uv's last lines into Windows refusing to run downloaded software, a certificate replaced
by an inspecting proxy, an unreachable or stalled network (naming the host), a full disk and anything
else (quoting uv, with the user's folder shortened); which failures are worth another try; the wording
for an update; and Windows in S mode ruling an install out before anything is downloaded.
Does NOT belong: Running uv and retrying (test_chatterbox_update.py).
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

import pytest

from ltts.engines import device_policy
from ltts.engines.install_errors import BLOCKED, CERTIFICATE, DISK_FULL, FAILED, NETWORK, UPDATE_FAILED, explain

POLICY = [
    "error: Failed to query Python interpreter at `C:/Users/reader/tools/python/python.exe`",
    "  Caused by: An Application Control policy has blocked this file. (os error 4551)",
]
INSPECTED = [
    "error: Failed to fetch: `https://pypi.org/simple/hatchling/`",
    "  Caused by: Request failed after 3 retries",
    "  Caused by: error sending request for url (https://pypi.org/simple/hatchling/)",
    "  Caused by: client error (Connect)",
    "  Caused by: invalid peer certificate: UnknownIssuer",
]
NO_HOST = [
    "error: Failed to download `torch==2.11.0+cpu`",
    "  Caused by: error sending request for url (https://download.pytorch.org/whl/cpu/torch-2.11.0.whl)",
    "  Caused by: dns error: No such host is known. (os error 11001)",
]
STALLED = [
    "error: Failed to download `scipy==1.17.1`",
    "  Caused by: Failed to fetch https://files.pythonhosted.org/packages/aa/scipy.whl",
    "  Caused by: operation timed out",
]


@pytest.mark.parametrize(
    "lines",
    [
        POLICY,
        ["error: failed to spawn", "  Caused by: This program is blocked by group policy. (os error 1260)"],
        ["Caused by: Operation did not complete successfully because the file contains a virus or potentially "
         "unwanted software. (os error 225)"],
    ],
)  # fmt: skip
def test_windows_refusing_to_run_the_download_is_named(lines: list[str]) -> None:
    failure = explain(lines)
    assert failure.code == BLOCKED and not failure.transient and not failure.certificate
    assert "Windows blocked the voice-cloning engine" in failure.message and "S mode" in failure.message
    assert "Nothing was installed" in failure.message


def test_a_replaced_certificate_names_the_host_and_is_retried_with_the_pcs_own_certificates() -> None:
    failure = explain(INSPECTED)
    assert failure.code == CERTIFICATE and failure.certificate and not failure.transient
    assert "security certificate for pypi.org" in failure.message and "inspects connections" in failure.message


def test_an_unreachable_host_is_named_and_a_stalled_download_is_worth_another_try() -> None:
    unreachable, stalled = explain(NO_HOST), explain(STALLED)
    assert unreachable.code == NETWORK and not unreachable.transient
    assert "couldn't reach download.pytorch.org" in unreachable.message
    assert stalled.code == NETWORK and stalled.transient
    assert "couldn't reach files.pythonhosted.org" in stalled.message
    assert "firewall, proxy or filtered network" in stalled.message
    nameless = explain(["error: Request failed after 3 retries", "  Caused by: connection reset"])
    assert nameless.code == NETWORK and "couldn't reach the servers it needs" in nameless.message


def test_a_full_disk_is_not_blamed_on_the_network() -> None:
    lines = ["error: Failed to download https://files.pythonhosted.org/x.whl", "  Caused by: (os error 112)"]
    failure = explain(lines)
    assert failure.code == DISK_FULL and "disk filled up" in failure.message


def test_anything_else_quotes_what_uv_said_without_the_users_folder() -> None:
    home = str(Path.home())
    failure = explain(["Resolved 3 packages", f"error: Distribution not found at: {home}/worker", "   hint: none"])
    assert failure.code == FAILED and not failure.transient
    assert "Installing the Chatterbox runtime failed." in failure.message
    assert "Distribution not found at: ~/worker" in failure.message and home not in failure.message
    assert explain([]).message == "Installing the Chatterbox runtime failed. The server log has the rest."
    long = explain(["error: " + "x" * 500])
    assert len(long.message) < 320 and "…" in long.message


def test_an_update_says_the_installation_was_kept() -> None:
    assert explain(STALLED, update=True).message.endswith("Your current installation was kept.")
    other = explain(["error: odd"], update=True)
    assert other.code == UPDATE_FAILED and other.message.startswith("Updating the Chatterbox runtime failed.")
    assert other.message.endswith("Your current installation was kept.")


def test_s_mode_rules_an_install_out_before_anything_is_downloaded() -> None:
    assert device_policy.install_blocker(lambda: 1) == device_policy.S_MODE
    assert "S mode" in device_policy.S_MODE and "Microsoft Store" in device_policy.S_MODE
    assert device_policy.install_blocker(lambda: 0) is None
    assert device_policy.install_blocker(lambda: None) is None
    assert device_policy.install_blocker() in (None, device_policy.S_MODE)  # this computer's own setting


def test_s_mode_is_read_from_windows_code_integrity_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    stored: dict[str, tuple[object, int]] = {}
    opened: list[tuple[int, str]] = []

    @contextmanager
    def open_key(root: int, path: str) -> Iterator[str]:
        opened.append((root, path))
        yield path

    def query(_key: str, name: str) -> tuple[object, int]:
        if name not in stored:
            raise FileNotFoundError(name)
        return stored[name]

    registry = ModuleType("winreg")
    registry.__dict__.update(HKEY_LOCAL_MACHINE=2, REG_DWORD=4, OpenKey=open_key, QueryValueEx=query)
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(sys, "platform", "win32")
    assert device_policy.install_blocker() is None  # the value isn't there on ordinary Windows editions
    assert opened == [(2, r"SYSTEM\CurrentControlSet\Control\CI\Policy")]
    stored["SkuPolicyRequired"] = (1, 4)
    assert device_policy.install_blocker() == device_policy.S_MODE
    stored["SkuPolicyRequired"] = (0, 4)
    assert device_policy.install_blocker() is None
    stored["SkuPolicyRequired"] = ("1", 1)  # text, not a number: not the setting Windows writes
    assert device_policy.install_blocker() is None
    monkeypatch.setattr(sys, "platform", "linux")
    stored["SkuPolicyRequired"] = (1, 4)
    assert device_policy.install_blocker() is None  # only Windows has S mode

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Tell when Windows itself won't run software that arrives outside the Microsoft Store.

Scope: Windows in S mode, read from the code-integrity policy key (``SkuPolicyRequired``): it runs only
software from the Store and from Microsoft, so the cloning engine, which is downloaded after the app is
installed, can never start there. Gives the sentence to show in place of an install button. Policies
that decide file by file (Smart App Control, an organization's application control, security software)
are not guessed at here; they are named when they block an install (``install_errors.py``).
Does NOT belong: Installing anything, or the wording of a failed install.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

S_MODE = (
    "Windows on this PC is in S mode, which only runs software from the Microsoft Store. The voice-cloning "
    "engine is downloaded separately from the app, so it can't be installed here."
)
_POLICY_KEY = r"SYSTEM\CurrentControlSet\Control\CI\Policy"
_S_MODE_VALUE = "SkuPolicyRequired"


def _sku_policy() -> int | None:
    """The ``SkuPolicyRequired`` value (1 in S mode), or None when it isn't set or this isn't Windows."""
    policy: int | None = None
    if sys.platform == "win32":  # the registry module exists only there
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _POLICY_KEY) as key:
                value, kind = winreg.QueryValueEx(key, _S_MODE_VALUE)
        except OSError:
            return None
        if kind == winreg.REG_DWORD:
            policy = int(value)
    return policy


def install_blocker(read: Callable[[], int | None] = _sku_policy) -> str | None:
    """Why this PC can never install downloaded engines, or None when nothing rules it out up front."""
    return S_MODE if read() == 1 else None

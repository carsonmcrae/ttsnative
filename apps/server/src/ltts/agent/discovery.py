# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Publish a native credential in a fresh, private directory for this running instance.

Scope: Per-instance owner-only discovery files and removal of this instance's own file at shutdown.
Python >=3.12.4 gives mode 0700 directories an owner/administrators-only ACL on Windows.
Does NOT belong: HTTP authentication, process launching or user data cleanup.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

from ltts.config import Settings

_WINDOWS = sys.platform == "win32"


def discovery_root(settings: Settings) -> Path:
    if settings.agent_discovery_dir is not None:
        return settings.agent_discovery_dir
    if _WINDOWS:
        return Path(os.environ["LOCALAPPDATA"]) / "com.ttsnative.desktop" / "agent"
    return Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "ttsnative" / "agent"


def publish(settings: Settings, descriptor: dict[str, Any]) -> Path:
    root = discovery_root(settings)
    root.mkdir(parents=True, exist_ok=True)
    leaf = root / str(descriptor["instanceId"])
    # Exclusive creation is essential: exist_ok would trust an old, potentially broad Windows ACL.
    leaf.mkdir(mode=0o700)
    temporary = leaf / "instance.tmp"
    descriptor_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor_fd, "w", encoding="utf-8") as output:
        output.write(json.dumps(descriptor))
    target = leaf / "instance.json"
    temporary.replace(target)
    return target


def unpublish(path: Path) -> None:
    path.unlink(missing_ok=True)
    # Never recursively remove a folder: an unexpected file belongs to its creator.
    with suppress(OSError):
        path.parent.rmdir()

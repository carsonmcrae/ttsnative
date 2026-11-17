# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Say why the cloning engine's runtime could not be installed, in words a person can act on.

Scope: Reads the last lines uv printed when ``uv sync`` failed and sorts the failure into: Windows
refused to run the downloaded software (S mode, Smart App Control, an application-control or group
policy, security software), a certificate replaced by a proxy that inspects connections, the network
(a host that can't be reached, a timeout, a proxy or firewall), a full disk, or something else. Each
has a stable error code and a message that names the host or quotes the line that says the most, with
the user's own folder shortened to ``~``. Also says which of them are worth another automatic try.
Does NOT belong: Running uv (``chatterbox_env.py``) or checking the PC up front (``device_policy.py``).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

BLOCKED = "install_blocked"
CERTIFICATE = "install_certificate"
NETWORK = "install_network"
DISK_FULL = "install_disk_full"
FAILED = "install_failed"
UPDATE_FAILED = "update_failed"
# Windows error numbers and wording for "this PC won't run that file": an application-control policy (S mode,
# Smart App Control, WDAC), a group policy, an installer policy, or security software quarantining it.
_BLOCKED = re.compile(
    r"os error (?:4551|1260|1625|225|226)\b|application control policy|blocked by group policy"
    r"|blocked by your organi[sz]ation|smart app control|contains a virus or potentially unwanted software",
    re.IGNORECASE,
)
_CERTIFICATE = re.compile(
    r"invalid peer certificate|unknownissuer|certificate verify failed|self[- ]signed certificate"
    r"|unable to get local issuer|certificate is not trusted|certificate has expired|badcertificate",
    re.IGNORECASE,
)
_DISK_FULL = re.compile(
    r"os error (?:112|39)\b|no space left on device|not enough space on the disk|disk is full", re.IGNORECASE
)
# Dropped or stalled connections: the same request often works a moment later.
_TRANSIENT = re.compile(
    r"timed out|timeout|os error (?:10060|10054|10053)\b|connection reset|connection closed|connection aborted"
    r"|unexpected eof|incomplete message|http status server error",
    re.IGNORECASE,
)
_NETWORK = re.compile(
    r"error sending request|dns error|failed to lookup address|no such host is known|connection refused"
    r"|os error (?:11001|11002|11004|10061|10065|10051|10013)\b|network is unreachable|failed to fetch"
    r"|failed to download|request failed after|http status client error|proxy|tunnel",
    re.IGNORECASE,
)
_URL_HOST = re.compile(r"https?://([A-Za-z0-9.-]+)")
_SAYS_WHY = re.compile(r"^\s*(?:error|caused by)\b", re.IGNORECASE)
_LABEL = re.compile(r"^\s*(?:error|caused by)\s*:\s*", re.IGNORECASE)
_DETAIL_CHARS = 200
_KEPT = " Your current installation was kept."


@dataclass(frozen=True, slots=True)
class SyncFailure:
    code: str
    message: str
    transient: bool = False  # a dropped or stalled connection: worth another automatic try
    certificate: bool = False  # worth one try with the Windows certificate store


def _host(text: str) -> str | None:
    hosts = _URL_HOST.findall(text)
    return hosts[-1].lower() if hosts else None


def _detail(lines: Sequence[str]) -> str:
    """The last line that says why (uv's ``error:`` or ``Caused by:``), else the last line, kept short."""
    said = [line for line in lines if line.strip()]
    if not said:
        return ""
    why = [line for line in said if _SAYS_WHY.match(line)]
    text = _LABEL.sub("", why[-1] if why else said[-1]).strip().replace(str(Path.home()), "~")
    return text if len(text) <= _DETAIL_CHARS else text[: _DETAIL_CHARS - 1] + "…"


def _blocked() -> str:
    return (
        "Windows blocked the voice-cloning engine on this PC. The engine is downloaded separately from the app, "
        "and this PC only runs approved software: Windows in S mode, Smart App Control, security software or a "
        "rule set by an organization does this. Nothing was installed."
    )


def _certificate(host: str | None) -> str:
    where = f"for {host}" if host else "of the download server"
    return (
        f"The download was refused because this network replaced the security certificate {where}. A proxy or "
        "security product that inspects connections does this. Nothing was installed."
    )


def _network(host: str | None) -> str:
    where = host or "the servers it needs"
    return (
        f"The download couldn't reach {where}. The connection dropped, or a firewall, proxy or filtered network "
        "is blocking it. Check the connection and try again."
    )


def explain(output: Sequence[str], *, update: bool = False) -> SyncFailure:
    """Why ``uv sync`` failed, from the last lines it printed."""
    text = "\n".join(output)
    kept = _KEPT if update else ""
    if _BLOCKED.search(text):
        return SyncFailure(BLOCKED, _blocked() + kept)
    if _DISK_FULL.search(text):
        return SyncFailure(DISK_FULL, "The disk filled up during the download. Free some space and try again." + kept)
    if _CERTIFICATE.search(text):
        return SyncFailure(CERTIFICATE, _certificate(_host(text)) + kept, certificate=True)
    if _TRANSIENT.search(text) or _NETWORK.search(text):
        return SyncFailure(NETWORK, _network(_host(text)) + kept, transient=bool(_TRANSIENT.search(text)))
    doing = "Updating" if update else "Installing"
    detail = _detail(output)
    said = f" The installer said: “{detail}”." if detail else ""
    return SyncFailure(
        UPDATE_FAILED if update else FAILED,
        f"{doing} the Chatterbox runtime failed.{said} The server log has the rest.{kept}",
    )

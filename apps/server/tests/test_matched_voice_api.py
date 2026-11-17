# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Tests for making a matched voice from a custom voice's recording over HTTP.

Scope: A matched voice is an ordinary blend of two built-in voices named after the profile, readable
without the cloning engine; where the recording sits between the deeper and lighter voices the other
version can be asked for and replaces the first; the profile and its recording are left as they were;
a recording with no clear pitch, missing built-in voices and an unknown profile are refused plainly.
Does NOT belong: Measuring pitch and choosing voices (test_voice_matching.py).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient

from conftest import SAMPLE_RATE, FakeEngine, wav_bytes
from ltts.container import Services
from ltts.voices.matching import GROUPS

MISSING_ID = "f" * 32


def spoken(hz: float, seconds: float = 12.0) -> np.ndarray:
    """Syllable-like bursts of a buzzy tone at ``hz``: passes the recording checks and has a clear pitch."""
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    bursts = (np.sin(2 * np.pi * 3.0 * t) > -0.6).astype(np.float32)
    tone = sum(np.sin(2 * np.pi * hz * k * t) / k for k in range(1, 7))
    hiss = 0.0005 * np.random.default_rng(7).standard_normal(len(t))
    return (0.3 * bursts * tone / 2.5 + hiss).astype(np.float32)


@pytest.fixture
def builtin(engines: dict[str, FakeEngine]) -> FakeEngine:
    """The fake Kokoro with the real built-in voices a matched voice is mixed from."""
    kokoro = engines["kokoro"]
    first = FakeEngine.voices(kokoro)[0]
    voices = [
        first.model_copy(update={"id": f"kokoro:{key}", "name": key.partition("_")[2].title()})
        for key in (*GROUPS["deeper"], *GROUPS["lighter"])
    ]
    kokoro.voices = lambda: voices  # type: ignore[method-assign]
    return kokoro


def profile(client: TestClient, hz: float, name: str = "Narrator") -> dict[str, Any]:
    made = client.post("/api/voice-profiles", params={"name": name, "consent": "true"}, content=wav_bytes(spoken(hz)))
    assert made.status_code == 201, made.text
    created: dict[str, Any] = made.json()
    return created


def matched(client: TestClient, profile_id: str, **body: Any) -> Any:
    return client.post(f"/api/voice-profiles/{profile_id}/matched-voice", json=body)


def keys(blend: dict[str, Any]) -> set[str]:
    return {part["voiceId"].removeprefix("kokoro:") for part in blend["parts"]}


def test_a_matched_voice_reads_without_the_cloning_engine(
    client: TestClient, builtin: FakeEngine, engines: dict[str, FakeEngine]
) -> None:
    engines["chatterbox"].ready = False
    narrator = profile(client, 118.0)
    made = matched(client, narrator["id"])
    assert made.status_code == 201, made.text
    body = made.json()
    blend = body["blend"]
    assert blend["name"] == "Narrator (matched)" and blend["voiceId"] == f"blend:{blend['id']}"
    assert (body["tone"], body["otherTone"]) == ("deeper", None)
    assert len(blend["parts"]) == 2 and keys(blend) <= set(GROUPS["deeper"])
    assert sum(part["weight"] for part in blend["parts"]) == pytest.approx(1.0, abs=1e-3)
    listed = {voice["id"]: voice for voice in client.get("/api/voices").json()}
    assert listed[blend["voiceId"]]["available"] and listed[blend["voiceId"]]["engineId"] == "kokoro"
    assert not listed[narrator["voiceId"]]["available"]  # the cloned voice itself still waits for the engine
    doc = client.post("/api/documents/text", json={"text": "Hello there."}).json()
    audio = client.get(f"/api/documents/{doc['id']}/segments/0/audio", params={"voice": blend["voiceId"]})
    assert audio.status_code == 200
    assert {key for key, _ in builtin.specs[-1].blend} == keys(blend)
    # The profile and its recording are untouched.
    assert client.get("/api/voice-profiles").json() == [narrator]
    assert client.get(f"/api/voice-profiles/{narrator['id']}/reference").status_code == 200


def test_the_other_version_replaces_the_first_and_leaves_other_blends_alone(
    client: TestClient, builtin: FakeEngine
) -> None:
    parts = [{"voiceId": "kokoro:am_onyx", "weight": 1}, {"voiceId": "kokoro:af_heart", "weight": 1}]
    own = client.post("/api/voice-profiles/blends", json={"name": "My own mix", "parts": parts}).json()
    between = profile(client, 150.0, name="Between")
    first = matched(client, between["id"]).json()
    assert (first["tone"], first["otherTone"]) == ("deeper", "lighter")
    second = matched(client, between["id"], tone="lighter").json()
    assert (second["tone"], second["otherTone"]) == ("lighter", "deeper")
    assert keys(second["blend"]) <= set(GROUPS["lighter"]) and second["blend"]["id"] != first["blend"]["id"]
    blends = client.get("/api/voice-profiles/blends").json()
    assert [blend["name"] for blend in blends] == ["My own mix", "Between (matched)"]
    assert blends[0] == own and blends[1]["id"] == second["blend"]["id"]
    again = matched(client, between["id"], tone=None).json()
    assert again["tone"] == "deeper" and len(client.get("/api/voice-profiles/blends").json()) == 2


def test_a_long_name_still_fits(client: TestClient, builtin: FakeEngine) -> None:
    long = profile(client, 190.0, name="N" * 60)
    blend = matched(client, long["id"]).json()["blend"]
    assert blend["name"] == "N" * 50 + " (matched)" and len(blend["name"]) == 60


def test_what_cannot_be_matched_is_refused_plainly(
    client: TestClient, builtin: FakeEngine, services: Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert matched(client, MISSING_ID).status_code == 404
    narrator = profile(client, 118.0)
    assert matched(client, narrator["id"], tone="squeaky").status_code == 422
    builtin.voices = lambda: FakeEngine.voices(builtin)  # type: ignore[method-assign]
    unavailable = matched(client, narrator["id"])
    assert unavailable.status_code == 409 and unavailable.json()["error"]["code"] == "matched_voice_unavailable"
    from ltts.voices import matched as matched_module

    monkeypatch.setattr(matched_module, "median_pitch", lambda *_args: None)
    unclear = matched(client, narrator["id"])
    assert unclear.status_code == 422 and unclear.json()["error"]["code"] == "pitch_not_found"
    services.voices.reference_path(narrator["id"]).unlink()
    gone = matched(client, narrator["id"])
    assert gone.status_code == 404 and gone.json()["error"]["code"] == "voice_not_found"
    assert client.get("/api/voice-profiles/blends").json() == []

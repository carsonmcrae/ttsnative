# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Real-inference checks for the matched voice, with the installed Kokoro model and no fakes.

Scope: The committed pitch table (``builtin_pitch.json``) still matches what the model's built-in
voices measure on the table's own passage, and a matched blend, spoken by the real model, lands
within a semitone and a half of the pitch it was chosen for across the range the built-in voices
cover. Set ``LTTS_WRITE_BUILTIN_PITCH=1`` to rewrite the table from the model (after a model update).
Run with ``npm run test:inference``. Skips cleanly when the model is not installed.
Does NOT belong: The choice of voices on its own (test_voice_matching.py), which needs no model.
"""

from __future__ import annotations

import json
import math
import os
from importlib import resources
from pathlib import Path

import numpy as np
import pytest

from ltts.config import REPO_ROOT
from ltts.engines.base import VoiceSpec
from ltts.engines.kokoro import KokoroEngine
from ltts.modelstore.store import ModelStore
from ltts.voices import matching
from ltts.voices.matching import builtin_pitch, match, median_pitch

pytestmark = pytest.mark.inference

MODELS = REPO_ROOT / "data" / "models"
TABLE = Path(str(resources.files("ltts.voices").joinpath("builtin_pitch.json")))
ENGLISH = ("af_", "am_", "bf_", "bm_")


@pytest.fixture(scope="module")
def kokoro() -> KokoroEngine:
    if not (MODELS / "kokoro-v1.0" / ".installed.json").is_file():
        pytest.skip("Kokoro model not installed (run `npm run setup`)")
    return KokoroEngine(ModelStore(MODELS, reserve_mb=0))


def spoken_pitch(kokoro: KokoroEngine, spec: VoiceSpec, text: str) -> float:
    clip = kokoro.synthesize(text, spec, 1.0)
    pitch = median_pitch(np.asarray(clip.samples, dtype=np.float32), clip.sample_rate)
    assert pitch is not None
    return pitch


def semitones(a: float, b: float) -> float:
    return abs(12 * math.log2(a / b))


def test_the_pitch_table_matches_the_model(kokoro: KokoroEngine) -> None:
    recorded = json.loads(TABLE.read_text("utf-8"))
    measured = {}
    for voice in kokoro.voices():
        key = voice.id.partition(":")[2]
        if key.startswith(ENGLISH):
            spec = VoiceSpec(key=key, language_code=voice.language_code)
            measured[key] = round(spoken_pitch(kokoro, spec, recorded["passage"]), 1)
    if os.environ.get("LTTS_WRITE_BUILTIN_PITCH") == "1":
        TABLE.write_text(json.dumps({**recorded, "voices": measured}, indent=2) + "\n", encoding="utf-8")
        builtin_pitch.cache_clear()
    table = builtin_pitch()
    assert set(table) == set(measured)
    drift = {key: round(semitones(measured[key], table[key]), 2) for key in table}
    assert max(drift.values()) < 0.25, drift


@pytest.mark.parametrize("pitch", [95.0, 112.0, 126.0, 144.0, 158.0, 172.0, 188.0, 200.0])
def test_a_matched_blend_speaks_at_the_pitch_it_was_chosen_for(kokoro: KokoroEngine, pitch: float) -> None:
    available = {voice.id.partition(":")[2] for voice in kokoro.voices()}
    text = "She opened the letter slowly, read it twice, and then put it back in the drawer without a word."
    likelier = match(pitch, available)
    assert likelier is not None
    for found in (likelier, match(pitch, available, likelier.other) if likelier.other else None):
        if found is None:
            continue
        group = matching._group(found.tone, available)
        spec = VoiceSpec(key=found.parts[0][0], language_code="en-us", blend=found.parts)
        landed = spoken_pitch(kokoro, spec, text)
        if group[0][1] <= pitch <= group[-1][1]:  # between the group's own voices: the blend is on the pitch
            assert semitones(landed, pitch) < 1.5, (found, landed)
        else:  # in its reach beyond them: the nearest it has
            assert semitones(landed, pitch) < 1.5 + matching.REACH_SEMITONES, (found, landed)

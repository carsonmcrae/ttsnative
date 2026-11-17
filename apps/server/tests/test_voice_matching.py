# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Tests for the matched voice: a recording's pitch and the built-in voices that stand in for it.

Scope: Measuring the median pitch of voiced sound (and refusing to guess from hum, noise or a clip that
is too short), the measured pitch table of the built-in voices, and choosing the two voices that bracket
a pitch with weights that land on it: the deeper or the lighter group, the other one offered where both
reach, the nearest voice leading beyond a group's range, better-graded voices preferred nearby, and
voices that aren't installed left out.
Does NOT belong: Creating the blend over HTTP (test_matched_voice_api.py) or mixing in Kokoro.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ltts.engines.kokoro_voices import GRADES
from ltts.voices import matching
from ltts.voices.matching import GROUPS, builtin_pitch, match, median_pitch

RATE = 24_000
EVERY_VOICE = frozenset(GRADES)


def voice(hz: float, seconds: float = 4.0, rate: int = RATE, level: float = 0.3) -> np.ndarray:
    """A buzzy, vowel-like tone in syllable-length bursts, its pitch wavering slightly like speech."""
    t = np.arange(int(seconds * rate)) / rate
    phase = 2 * np.pi * hz * t + 0.3 * np.sin(2 * np.pi * 5 * t)  # the pitch moves a hertz or two either way
    tone = sum(np.sin(k * phase) / k for k in range(1, 9))
    bursts = (np.sin(2 * np.pi * 3.0 * t) > -0.6).astype(np.float64)
    return (level * bursts * tone / 2.7).astype(np.float32)


def blend_pitch(parts: tuple[tuple[str, float], ...]) -> float:
    """Where a blend lands: the log-linear mix of its parts' measured pitches."""
    table = builtin_pitch()
    return math.exp(sum(weight * math.log(table[key]) for key, weight in parts))


def semitones(a: float, b: float) -> float:
    return abs(12 * math.log2(a / b))


@pytest.mark.parametrize("hz", [75.0, 95.0, 120.0, 150.0, 185.0, 230.0, 320.0])
def test_the_pitch_of_voiced_sound_is_measured_closely(hz: float) -> None:
    measured = median_pitch(voice(hz), RATE)
    assert measured is not None and semitones(measured, hz) < 0.35


@pytest.mark.parametrize("rate", [16_000, 22_050, 44_100, 48_000])
def test_the_recording_rate_does_not_change_the_pitch(rate: int) -> None:
    measured = median_pitch(voice(140.0, rate=rate), rate)
    assert measured is not None and semitones(measured, 140.0) < 0.35


def test_quiet_mains_hum_and_hiss_between_words_are_not_taken_for_the_voice() -> None:
    t = np.arange(4 * RATE) / RATE
    hum = 0.004 * np.sin(2 * np.pi * 50 * t) + 0.002 * np.random.default_rng(3).standard_normal(t.size)
    measured = median_pitch((voice(132.0) + hum).astype(np.float32), RATE)
    assert measured is not None and semitones(measured, 132.0) < 0.35


def test_no_pitch_is_guessed_without_a_second_of_voiced_speech() -> None:
    noise = (0.1 * np.random.default_rng(5).standard_normal(4 * RATE)).astype(np.float32)
    assert median_pitch(noise, RATE) is None
    assert median_pitch(np.zeros(4 * RATE, dtype=np.float32), RATE) is None
    assert median_pitch(voice(150.0, seconds=0.6), RATE) is None
    assert median_pitch(np.zeros(10, dtype=np.float32), RATE) is None


def test_every_voice_in_the_groups_has_a_measured_pitch_in_a_speaking_range() -> None:
    table = builtin_pitch()
    for key in (*GROUPS["deeper"], *GROUPS["lighter"]):
        assert key in GRADES and 70 < table[key] < 260
    assert max(table[key] for key in GROUPS["deeper"]) < max(table[key] for key in GROUPS["lighter"])
    assert min(table[key] for key in GROUPS["deeper"]) < min(table[key] for key in GROUPS["lighter"])


@pytest.mark.parametrize("pitch", [90.0, 104.0, 118.0, 131.0, 146.0, 150.0, 168.0, 181.0, 196.0, 202.0])
def test_a_match_is_two_voices_whose_blend_lands_on_the_pitch(pitch: float) -> None:
    found = match(pitch, EVERY_VOICE)
    assert found is not None and len(found.parts) == 2
    (first, heavier), (second, lighter) = found.parts
    assert first != second and {first, second} <= set(GROUPS[found.tone])
    assert heavier >= lighter >= matching.MIN_WEIGHT and heavier + lighter == pytest.approx(1.0)
    assert semitones(blend_pitch(found.parts), pitch) < 0.6


def test_the_likelier_group_is_chosen_and_the_other_offered_where_both_reach() -> None:
    low, between, high = match(110.0, EVERY_VOICE), match(150.0, EVERY_VOICE), match(190.0, EVERY_VOICE)
    assert low is not None and (low.tone, low.other) == ("deeper", None)
    assert between is not None and (between.tone, between.other) == ("deeper", "lighter")
    assert high is not None and (high.tone, high.other) == ("lighter", None)
    just_above = match(166.0, EVERY_VOICE)
    assert just_above is not None and (just_above.tone, just_above.other) == ("lighter", "deeper")


def test_the_other_group_can_be_asked_for() -> None:
    lighter = match(150.0, EVERY_VOICE, "lighter")
    assert lighter is not None and lighter.tone == "lighter" and lighter.other == "deeper"
    assert {key for key, _ in lighter.parts} <= set(GROUPS["lighter"])
    assert semitones(blend_pitch(lighter.parts), 150.0) < 0.6


def test_beyond_every_voice_the_nearest_one_leads() -> None:
    table = builtin_pitch()
    lowest = min(GROUPS["deeper"], key=lambda key: table[key])
    highest = max(GROUPS["lighter"], key=lambda key: table[key])
    deep, high = match(60.0, EVERY_VOICE), match(300.0, EVERY_VOICE)
    assert deep is not None and deep.tone == "deeper" and deep.parts[0] == (lowest, matching.OUTSIDE_WEIGHT)
    assert high is not None and high.tone == "lighter" and high.parts[0] == (highest, matching.OUTSIDE_WEIGHT)
    assert deep.other is None and high.other is None


def test_a_better_voice_nearby_is_preferred_to_the_very_nearest(monkeypatch: pytest.MonkeyPatch) -> None:
    table = {"am_onyx": 100.0, "am_echo": 118.0, "am_michael": 112.0, "am_fenrir": 140.0}
    monkeypatch.setattr(matching, "builtin_pitch", lambda: table)
    found = match(120.0, EVERY_VOICE)
    # Echo (D) is nearest below, but Michael (C+) is within a few semitones and reads better.
    assert found is not None and {key for key, _ in found.parts} == {"am_michael", "am_fenrir"}


def test_voices_that_are_not_installed_are_left_out() -> None:
    only = {"am_onyx", "am_fenrir", "af_heart"}
    found = match(120.0, only)
    assert found is not None and {key for key, _ in found.parts} == {"am_onyx", "am_fenrir"}
    assert found.other is None  # one lighter voice is not enough to blend
    forced = match(120.0, only, "lighter")
    assert forced is not None and forced.tone == "deeper"
    assert match(120.0, {"am_onyx", "af_heart"}) is None
    assert match(120.0, frozenset()) is None

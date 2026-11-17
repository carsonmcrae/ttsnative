# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: A matched voice: the built-in voices nearest a recording's pitch, as the parts of a blend.

Scope: Measures the median speaking pitch of a recording (normalized autocorrelation, numpy only) and
picks, from the built-in US English Kokoro voices, the two whose measured pitch (``builtin_pitch.json``)
brackets it, weighted so the blend lands on the recording's pitch: a blend's pitch follows the
log-linear mix of its parts' pitches to within about 4% (measured with kokoro-v1.0). The built-in
voices form a deeper and a lighter group whose ranges meet around 140 to 150 Hz, so a recording near
there can be matched either way: the likelier group is chosen and the caller is told when the other
one is possible too. This is what Voice Studio offers when the cloning engine can't be installed on a
PC. It is not a copy of the speaker's voice and is never described as one.
Does NOT belong: Storing the blend (``blends.py``), the cloning engine or HTTP (``router.py``).
"""

from __future__ import annotations

import json
import math
from collections.abc import Collection
from dataclasses import dataclass
from functools import cache
from importlib import resources
from typing import Literal

import numpy as np
import numpy.typing as npt

from ltts.audio import Float32Array, resample
from ltts.engines.kokoro_voices import GRADES

Tone = Literal["deeper", "lighter"]
PITCH_RATE = 16_000  # pitch is measured on a 16 kHz copy: plenty for 65-400 Hz and light on memory
MIN_HZ, MAX_HZ = 65.0, 400.0  # the floor sits above mains hum (50 or 60 Hz)
FRAME_S, HOP_S = 0.04, 0.01
VOICED_PEAK = 0.6  # normalized autocorrelation at the pitch lag: vowels score well above it, noise below
LOUD_DB = 25.0  # only frames within this of the loudest ones are measured
NEAR_PEAK = 0.9  # the shortest lag whose peak is this close to the best wins (guards against octave-low picks)
MIN_VOICED_FRAMES = 100  # a second of voiced speech
CHUNK_FRAMES = 512
# The deeper and the lighter group. Left out: Santa (a character voice) and Nicole (a whisper).
GROUPS: dict[Tone, tuple[str, ...]] = {
    "deeper": ("am_onyx", "am_echo", "am_puck", "am_michael", "am_adam", "am_liam", "am_fenrir", "am_eric"),
    "lighter": (
        "af_alloy", "af_kore", "af_sky", "af_nova", "af_river", "af_aoede", "af_sarah", "af_heart", "af_bella",
        "af_jessica",
    ),
}  # fmt: skip
# Read speech averages about 120 Hz for men and 210 Hz for women; below this a deeper voice is the likelier fit.
LIKELIER_DEEPER_BELOW_HZ = 162.0
REACH_SEMITONES = 2.0  # how far past its own range a group can still stand in
NEAR_SEMITONES = 3.0  # a better-graded voice this close to the pitch is preferred over the nearest one
MIN_WEIGHT = 0.15  # a blend needs two parts; neither is mixed in below this
OUTSIDE_WEIGHT = 0.75  # the nearest voice's share when the pitch is beyond the whole group
_GRADE_POINTS = {
    "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0,
    "D-": 0.7, "F+": 0.3, "F": 0.0,
}  # fmt: skip


@dataclass(frozen=True, slots=True)
class Match:
    tone: Tone
    parts: tuple[tuple[str, float], ...]  # (Kokoro voice key, weight): two parts, heaviest first, adding up to one
    other: Tone | None  # the other group can stand in for this pitch as well


def _frames(samples: npt.NDArray[np.float64], size: int, hop: int) -> npt.NDArray[np.float64]:
    count = 1 + (len(samples) - size) // hop
    index = np.arange(size)[None, :] + hop * np.arange(count)[:, None]
    block: npt.NDArray[np.float64] = samples[index]
    return block


def _pitch_of(
    block: npt.NDArray[np.float64], window: npt.NDArray[np.float64], taper: npt.NDArray[np.float64]
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.bool_]]:
    """Each frame's pitch in Hz and whether it is voiced."""
    size = block.shape[1]
    centered = block - block.mean(axis=1, keepdims=True)
    spectrum = np.fft.rfft(centered * window, n=2 * size, axis=1)
    acf = np.fft.irfft(np.abs(spectrum) ** 2, axis=1)[:, :size]
    acf = acf / np.maximum(acf[:, :1], 1e-12) / taper  # undo the window's own fall-off at long lags
    low, high = int(PITCH_RATE / MAX_HZ), int(PITCH_RATE / MIN_HZ)
    span = acf[:, low : high + 1]
    best = span.max(axis=1, keepdims=True)
    peaks = (span[:, 1:-1] >= span[:, :-2]) & (span[:, 1:-1] > span[:, 2:]) & (span[:, 1:-1] >= NEAR_PEAK * best)
    found = peaks.any(axis=1)
    lag = low + 1 + np.argmax(peaks, axis=1)
    rows = np.arange(len(acf))
    before, at, after = acf[rows, lag - 1], acf[rows, lag], acf[rows, lag + 1]
    curve = before - 2 * at + after
    shift = np.where(np.abs(curve) < 1e-9, 0.0, 0.5 * (before - after) / np.where(curve == 0, 1.0, curve))
    return PITCH_RATE / (lag + np.clip(shift, -1.0, 1.0)), found & (at > VOICED_PEAK)


def median_pitch(samples: Float32Array, sample_rate: int) -> float | None:
    """The median pitch of the voiced speech in Hz, or None when there is under a second of it."""
    speech = resample(samples, sample_rate, PITCH_RATE).astype(np.float64)
    size, hop = int(FRAME_S * PITCH_RATE), int(HOP_S * PITCH_RATE)
    if len(speech) < size + hop:
        return None
    block = _frames(speech, size, hop)
    energy = (block**2).mean(axis=1)
    loud = energy > max(float(np.percentile(energy, 95)) * 10 ** (-LOUD_DB / 10), 1e-9)
    window = np.hanning(size)
    taper = np.correlate(window, window, mode="full")[size - 1 :]
    taper = np.maximum(taper / taper[0], 1e-3)
    voiced: list[npt.NDArray[np.float64]] = []
    for start in range(0, len(block), CHUNK_FRAMES):
        keep = loud[start : start + CHUNK_FRAMES]
        if keep.any():
            hz, ok = _pitch_of(block[start : start + CHUNK_FRAMES][keep], window, taper)
            voiced.append(hz[ok])
    track = np.concatenate(voiced) if voiced else np.empty(0)
    return float(np.median(track)) if track.size >= MIN_VOICED_FRAMES else None


@cache
def builtin_pitch() -> dict[str, float]:
    """Kokoro voice key -> its median pitch in Hz, measured on a fixed passage with the pinned model."""
    raw = json.loads(resources.files("ltts.voices").joinpath("builtin_pitch.json").read_text("utf-8"))
    return {str(key): float(value) for key, value in raw["voices"].items()}


def _semitones(pitch: float, reference: float) -> float:
    return 12.0 * math.log2(pitch / reference)


def _group(tone: Tone, available: Collection[str]) -> list[tuple[str, float]]:
    """The group's usable voices as (key, pitch), lowest first."""
    table = builtin_pitch()
    return sorted(((key, table[key]) for key in GROUPS[tone] if key in available and key in table), key=lambda v: v[1])


def _reaches(group: list[tuple[str, float]], pitch: float) -> bool:
    below, above = _semitones(group[0][1], pitch), _semitones(pitch, group[-1][1])  # how far outside its range
    return below <= REACH_SEMITONES and above <= REACH_SEMITONES


def _preferred(side: list[tuple[str, float]], pitch: float) -> tuple[str, float]:
    """The best-graded voice within a few semitones of the pitch, else simply the nearest."""

    def distance(voice: tuple[str, float]) -> float:
        return abs(_semitones(voice[1], pitch))

    near = [voice for voice in side if distance(voice) <= NEAR_SEMITONES]
    if not near:
        return min(side, key=distance)
    return max(near, key=lambda voice: (_GRADE_POINTS.get(GRADES.get(voice[0]) or "", 0.0), -distance(voice)))


def _parts(group: list[tuple[str, float]], pitch: float) -> tuple[tuple[str, float], ...]:
    below = [voice for voice in group if voice[1] <= pitch]
    above = [voice for voice in group if voice[1] > pitch]
    if not below or not above:  # beyond the whole group: its nearest voice, steadied by the next one
        nearest, next_one = (group[0], group[1]) if not below else (group[-1], group[-2])
        return ((nearest[0], OUTSIDE_WEIGHT), (next_one[0], round(1 - OUTSIDE_WEIGHT, 4)))
    low, high = _preferred(below, pitch), _preferred(above, pitch)
    share = math.log(pitch / low[1]) / math.log(high[1] / low[1])  # the higher voice's share, log-linear in pitch
    share = round(min(max(share, MIN_WEIGHT), 1 - MIN_WEIGHT), 4)
    parts = ((low[0], round(1 - share, 4)), (high[0], share))
    return parts if parts[0][1] >= parts[1][1] else (parts[1], parts[0])


def match(pitch_hz: float, available: Collection[str], tone: Tone | None = None) -> Match | None:
    """The blend that stands in for a voice at ``pitch_hz``; None when too few built-in voices are usable.

    ``tone`` asks for one group; left out, the likelier one for the pitch is used.
    """
    groups: dict[Tone, list[tuple[str, float]]] = {name: _group(name, available) for name in GROUPS}
    usable = [name for name, group in groups.items() if len(group) >= 2]
    if not usable:
        return None
    likelier: Tone = "deeper" if pitch_hz < LIKELIER_DEEPER_BELOW_HZ else "lighter"
    reaching = [name for name in usable if _reaches(groups[name], pitch_hz)]
    chosen = tone if tone in usable else None
    if chosen is None:
        candidates = reaching or usable
        chosen = likelier if likelier in candidates else candidates[0]
    other = next((name for name in reaching if name != chosen), None)
    return Match(tone=chosen, parts=_parts(groups[chosen], pitch_hz), other=other)

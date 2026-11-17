# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Carson McRae
"""Purpose: Make a matched voice for a custom voice profile: a stand-in that needs no cloning engine (ADR-27).

Scope: Measures the pitch of the profile's stored recording, picks the built-in voices that bracket it
(``matching.py``) and saves them as an ordinary voice blend named after the profile, replacing the
matched voice made for it before (so trying the other tone doesn't leave two). The recording is only
measured: the result is a mix of the app's own voices at the speaker's pitch, not a copy of the
speaker's voice, and the profile itself is left as it is for when the engine can be installed.
Does NOT belong: Measuring and choosing (``matching.py``), storing blends (``blends.py``) or HTTP.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ltts.audio import read_audio
from ltts.common import ApiModel
from ltts.engines.base import VoiceInfo
from ltts.errors import AppError, ConflictError, NotFoundError
from ltts.voices.blends import BLEND_ENGINE, BlendIn, BlendOut, BlendPart, BlendStore
from ltts.voices.matching import Tone, match, median_pitch

SUFFIX = " (matched)"
MAX_NAME = 60  # a blend's name limit


class MatchedVoiceIn(ApiModel):
    tone: Tone | None = None  # left out: the likelier group for the recording's pitch


class MatchedVoiceOut(ApiModel):
    blend: BlendOut
    tone: Tone
    other_tone: Tone | None  # set when the other group can match this recording too


class PitchNotFoundError(AppError):
    status_code = 422
    code = "pitch_not_found"


def matched_name(profile_name: str) -> str:
    return profile_name.strip()[: MAX_NAME - len(SUFFIX)].rstrip() + SUFFIX


def create_matched_voice(
    profile_name: str,
    recording: Path,
    blends: BlendStore,
    builtin: Callable[[], list[VoiceInfo]],
    tone: Tone | None = None,
) -> MatchedVoiceOut:
    if not recording.is_file():
        raise NotFoundError("This voice's reference recording is missing.", code="voice_not_found")
    samples, rate = read_audio(recording)
    pitch = median_pitch(samples, rate)
    if pitch is None:
        raise PitchNotFoundError(
            "TTSNative couldn't hear the pitch of this recording. A matched voice needs a second or more of "
            "clear speech."
        )
    prefix = f"{BLEND_ENGINE}:"
    available = {voice.id.removeprefix(prefix) for voice in builtin() if voice.available}
    found = match(pitch, available, tone)
    if found is None:
        raise ConflictError(
            "The built-in voices a matched voice is mixed from aren't available. Check the voice model in "
            "Settings → Engines & models.",
            code="matched_voice_unavailable",
        )
    name = matched_name(profile_name)
    for earlier in blends.list_all():
        if earlier.name == name:
            blends.delete(earlier.id)
    parts = [BlendPart(voice_id=f"{prefix}{key}", weight=weight) for key, weight in found.parts]
    return MatchedVoiceOut(
        blend=blends.create(BlendIn(name=name, parts=parts)), tone=found.tone, other_tone=found.other
    )

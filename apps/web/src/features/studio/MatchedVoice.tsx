// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Offer a matched voice for a custom voice whose cloning engine isn't installed.
 * Scope: Says what a matched voice is (TTSNative's own voices mixed at the pitch of the recording, not
 *   a copy of the voice), makes it, plays a sample, makes it the reading voice, and swaps to the
 *   deeper or lighter version where the recording could be matched either way. `MatchedVoiceButton`
 *   is the short form on a profile card.
 * Does NOT belong: Measuring the recording or mixing voices (the server), or installing the engine
 *   (features/engines).
 */
import { Blend, Check, Play } from 'lucide-react';
import { describeError } from '@/api/client';
import { useCreateMatchedVoice } from '@/api/blendQueries';
import type { VoiceProfile } from '@/api/types';
import { Button } from '@/components/ui/Button';
import { Banner } from '@/components/ui/Feedback';
import { useToast } from '@/components/ui/Toast';
import { useReadingVoice } from '@/features/player/useReadingVoice';
import { useVoicePreview } from '@/features/voices/useVoicePreview';

const SAMPLE_TEXT =
  'Hello! This is a matched voice. It was mixed from the voices that come with the app, at the pitch of my recording.';
const WHAT_IT_IS =
  'TTSNative can mix a stand-in from its own voices at the pitch of this recording. It reads straight away and needs no download. It isn’t a copy of the voice. You can install the optional cloning engine later and use this saved recording to clone the voice, without recording again.';

export function MatchedVoice({ profile }: Readonly<{ profile: VoiceProfile }>) {
  const create = useCreateMatchedVoice();
  const preview = useVoicePreview();
  const reading = useReadingVoice();
  const made = create.data;
  const voiceId = made?.blend.voiceId;
  const isDefault = voiceId !== undefined && reading.current === voiceId;
  const heading = `matched-voice-${profile.id}`;

  return (
    <section
      aria-labelledby={heading}
      className="flex flex-col gap-3 rounded-[var(--radius-md)] border border-line p-4"
    >
      <h3 id={heading} className="font-semibold">
        Use a matched voice without a download
      </h3>
      <p className="text-sm text-muted">{WHAT_IT_IS}</p>
      {create.error ? <Banner tone="error">{describeError(create.error)}</Banner> : null}
      {made ? (
        <Banner tone="success" title={`“${made.blend.name}” is ready`}>
          It is in your voice list, mixed from two of TTSNative’s own voices.
        </Banner>
      ) : null}
      {preview.state.error ? <Banner tone="error">{preview.state.error.message}</Banner> : null}
      <div className="flex flex-wrap gap-2">
        {made && voiceId ? (
          <>
            <Button
              variant="primary"
              icon={<Play size={15} fill="currentColor" />}
              loading={preview.state.status === 'loading'}
              onClick={() => void preview.play(voiceId, SAMPLE_TEXT)}
            >
              {preview.state.status === 'loading' ? 'Generating…' : 'Play sample'}
            </Button>
            <Button
              icon={isDefault ? <Check size={15} /> : undefined}
              disabled={isDefault}
              onClick={() => reading.choose(voiceId)}
            >
              {isDefault ? 'Used for reading' : 'Use for reading'}
            </Button>
            {made.otherTone ? (
              <Button
                variant="ghost"
                loading={create.isPending}
                onClick={() => create.mutate({ profileId: profile.id, tone: made.otherTone })}
              >
                Try a {made.otherTone} version
              </Button>
            ) : null}
          </>
        ) : (
          <Button
            icon={<Blend size={15} />}
            loading={create.isPending}
            onClick={() => create.mutate({ profileId: profile.id })}
          >
            Create matched voice
          </Button>
        )}
      </div>
    </section>
  );
}

/** The short form for a profile card: one button, and a note where the voice went. */
export function MatchedVoiceButton({ profile }: Readonly<{ profile: VoiceProfile }>) {
  const create = useCreateMatchedVoice();
  const toast = useToast();
  return (
    <Button
      size="sm"
      variant="ghost"
      icon={<Blend size={14} />}
      loading={create.isPending}
      title="A stand-in mixed from TTSNative’s own voices at the pitch of this recording. Not a copy of the voice."
      onClick={() =>
        create.mutate(
          { profileId: profile.id },
          {
            onSuccess: (made) =>
              toast.notify(
                'success',
                `“${made.blend.name}” is in your voice list`,
                'A stand-in mixed from TTSNative’s own voices at the pitch of this recording. It isn’t a copy of the voice.',
              ),
            onError: (error) =>
              toast.notify('error', 'Couldn’t make a matched voice', describeError(error)),
          },
        )
      }
    >
      Make a matched voice
    </Button>
  );
}

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Tests for the matched voice offered while the cloning engine isn't installed.
 * Scope: The panel on the wizard's last step (what it says a matched voice is, making one, playing a
 *   sample, using it for reading, swapping to the other tone, and failures to make or play it) and
 *   the short form on a profile card (the note where the voice went, and a failure).
 * Does NOT belong: Measuring the recording and choosing voices (the server's tests).
 */
import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { MatchedTone, MatchedVoice } from '@/api/blendQueries';
import { keys } from '@/api/queries';
import { json, kokoro, mockApi, preferences, renderWithApp, voiceProfile } from '@/test/render';
import { ProfileCard } from './ProfileCard';
import { TestStep } from './TestStep';

afterEach(() => vi.unstubAllGlobals());

const profile = voiceProfile({ name: 'Narrator' });
const MAKE = `/api/voice-profiles/${profile.id}/matched-voice`;

const matched = (id: string, tone: MatchedTone, otherTone: MatchedTone | null): MatchedVoice => ({
  blend: {
    id,
    voiceId: `blend:${id}`,
    name: 'Narrator (matched)',
    parts: [
      { voiceId: 'kokoro:am_michael', weight: 0.6 },
      { voiceId: 'kokoro:am_fenrir', weight: 0.4 },
    ],
    createdAt: '2026-11-17T10:00:00+00:00',
  },
  tone,
  otherTone,
});

function api(routes: Record<string, unknown>) {
  let saved = preferences;
  return mockApi({
    'GET /api/engines': [
      kokoro(),
      kokoro({ id: 'chatterbox', name: 'Chatterbox Turbo', status: 'not_installed' }),
    ],
    'GET /api/preferences': () => saved,
    'PUT /api/preferences': (_url: URL, init: RequestInit) =>
      (saved = JSON.parse(String(init.body)) as typeof preferences),
    'POST /api/voices/': () => new Response(new Blob(['wav'])),
    ...routes,
  });
}

const refusal = (message: string) => json({ error: { code: 'pitch_not_found', message } }, 422);

describe('Matched voice on the wizard’s last step', () => {
  it('says what it is, makes one, plays it and uses it for reading', async () => {
    const { calls } = api({ [`POST ${MAKE}`]: matched('a'.repeat(32), 'deeper', null) });
    const user = userEvent.setup();
    renderWithApp(<TestStep profile={profile} />);
    expect(
      await screen.findByRole('heading', {
        name: 'Use a matched voice without a download',
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/It isn’t a copy of the voice/)).toBeInTheDocument();
    expect(screen.getByText(/without recording again/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Create matched voice' }));
    expect(await screen.findByText('“Narrator (matched)” is ready')).toBeInTheDocument();
    expect(calls.find((call) => call.path === MAKE)?.body).toBe('{"tone":null}');
    expect(screen.queryByRole('button', { name: /Try a/ })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Play sample' }));
    await waitFor(() =>
      expect(calls.some((call) => call.path === `/api/voices/blend:${'a'.repeat(32)}/preview`)).toBe(true),
    ); // prettier-ignore
    await user.click(screen.getByRole('button', { name: 'Use for reading' }));
    expect(await screen.findByRole('button', { name: 'Used for reading' })).toBeDisabled();
    expect(calls.findLast((call) => call.method === 'PUT')?.body).toContain(`blend:${'a'.repeat(32)}`); // prettier-ignore
  });

  it('uses the saved original as a cloned voice after installing the engine later', async () => {
    let ready = false;
    const made = matched('a'.repeat(32), 'deeper', null);
    const { calls } = api({
      'GET /api/engines': () => [
        kokoro(),
        kokoro({ id: 'chatterbox', status: ready ? 'ready' : 'not_installed' }),
      ],
      [`POST ${MAKE}`]: made,
    });
    const user = userEvent.setup();
    const { queryClient } = renderWithApp(<TestStep profile={profile} />);
    await user.click(await screen.findByRole('button', { name: 'Create matched voice' }));
    await user.click(await screen.findByRole('button', { name: 'Use for reading' }));
    expect(await screen.findByRole('button', { name: 'Used for reading' })).toBeDisabled();
    expect(calls.findLast((call) => call.method === 'PUT')?.body).toContain(made.blend.voiceId);

    ready = true;
    await act(async () => {
      await queryClient.invalidateQueries({ queryKey: keys.engines });
    });
    await user.click(await screen.findByRole('button', { name: 'Generate sample' }));
    await waitFor(() =>
      expect(calls.some((call) => call.path === `/api/voices/${profile.voiceId}/preview`)).toBe(
        true,
      ),
    );
    await user.click(screen.getByRole('button', { name: 'Use for reading' }));
    expect(await screen.findByRole('button', { name: 'Used for reading' })).toBeDisabled();
    expect(calls.findLast((call) => call.method === 'PUT')?.body).toContain(profile.voiceId);
    expect(calls.filter((call) => call.path === MAKE)).toHaveLength(1);
    expect(calls.filter((call) => ['PATCH', 'DELETE'].includes(call.method))).toHaveLength(0);
  });

  it('swaps to the other tone where the recording could be matched either way', async () => {
    const answers = [matched('a'.repeat(32), 'deeper', 'lighter'), matched('b'.repeat(32), 'lighter', 'deeper')]; // prettier-ignore
    const { calls } = api({ [`POST ${MAKE}`]: () => answers.shift() });
    const user = userEvent.setup();
    renderWithApp(<TestStep profile={profile} />);
    await user.click(await screen.findByRole('button', { name: 'Create matched voice' }));
    await user.click(await screen.findByRole('button', { name: 'Try a lighter version' }));
    expect(await screen.findByRole('button', { name: 'Try a deeper version' })).toBeInTheDocument();
    expect(calls.filter((call) => call.path === MAKE).map((call) => call.body)).toEqual([
      '{"tone":null}',
      '{"tone":"lighter"}',
    ]);
  });

  it('explains why one could not be made, or its sample not played', async () => {
    const answers: unknown[] = [refusal('A matched voice needs a second or more of clear speech.'), matched('a'.repeat(32), 'deeper', null)]; // prettier-ignore
    api({
      [`POST ${MAKE}`]: () => answers.shift(),
      'POST /api/voices/': () =>
        json({ error: { code: 'synthesis_failed', message: 'The voice model is missing.' } }, 500),
    });
    const user = userEvent.setup();
    renderWithApp(<TestStep profile={profile} />);
    await user.click(await screen.findByRole('button', { name: 'Create matched voice' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('A matched voice needs a second or more of clear speech.'); // prettier-ignore
    await user.click(screen.getByRole('button', { name: 'Create matched voice' }));
    await user.click(await screen.findByRole('button', { name: 'Play sample' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('The voice model is missing.');
  });
});

describe('Matched voice on a profile card', () => {
  it('makes one and says where it went, or why it could not', async () => {
    const answers: unknown[] = [matched('a'.repeat(32), 'lighter', null), refusal('No clear pitch.')]; // prettier-ignore
    api({ [`POST ${MAKE}`]: () => answers.shift() });
    const user = userEvent.setup();
    renderWithApp(
      <ul>
        <ProfileCard profile={profile} engineReady={false} />
      </ul>,
    );
    const make = screen.getByRole('button', { name: 'Make a matched voice' });
    expect(make).toHaveAttribute('title', expect.stringContaining('Not a copy of the voice'));
    await user.click(make);
    expect(await screen.findByText('“Narrator (matched)” is in your voice list')).toBeInTheDocument(); // prettier-ignore
    await user.click(make);
    expect(await screen.findByText('Couldn’t make a matched voice')).toBeInTheDocument();
    expect(screen.getByText('No clear pitch.')).toBeInTheDocument();
  });
});

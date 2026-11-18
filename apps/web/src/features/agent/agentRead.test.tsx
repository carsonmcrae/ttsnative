// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Verify one-shot agent reading through the actual reader and shared playback controller.
 * Scope: Capability handling, effect replay, saved preferences, skipped sentences, autoplay blocks,
 *   playback failures and interruptions, and a truthful request-scoped acknowledgement.
 * Does NOT belong: Agent authentication on the server or Windows activation.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StrictMode } from 'react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from '@/app/App';
import type { usePlayer } from '@/features/player/PlayerProvider';
import ReaderPage from '@/features/reader/ReaderPage';
import { styles } from '@/test/styledReader';
import {
  documentDetail,
  json,
  mockReaderApi,
  PlayerSpy,
  preferences,
  renderWithApp,
} from '@/test/render';
import AgentReadPage from './AgentReadPage';
import type { AgentReadRequest } from './readRequest';
import { takeReadRequest } from './readRequest';

const ticket = 'a'.repeat(64);
const doc = documentDetail();
const request: AgentReadRequest = {
  requestId: 'read-request',
  documentId: doc.id,
  voiceId: 'kokoro:bm_george',
  pace: 1.2,
  autoplay: true,
  ackToken: 'request-scoped-test-capability',
};

afterEach(() => {
  takeReadRequest(doc.id);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  history.replaceState({}, '', '/');
});

function prepare(overrides: Record<string, unknown> = {}, options: Partial<AgentReadRequest> = {}) {
  return mockReaderApi(doc, {
    [`GET /api/documents/${doc.id}/styles`]: styles(),
    'POST /api/agent-reader/claim': { ...request, ...options },
    'POST /api/agent-reader/ack': {},
    ...overrides,
  });
}

function open(route = `/agent-read#${ticket}`, strict = false) {
  let player: ReturnType<typeof usePlayer>;
  history.replaceState({}, '', route);
  const content = (
    <Routes>
      <Route path="/agent-read" element={<AgentReadPage />} />
      <Route
        path="/read/:documentId"
        element={
          <>
            <ReaderPage />
            <PlayerSpy
              onPlayer={(value) => {
                player = value;
              }}
            />
          </>
        }
      />
    </Routes>
  );
  const view = renderWithApp(strict ? <StrictMode>{content}</StrictMode> : content, {
    path: '*',
    route,
  });
  return { ...view, player: () => player };
}

function acknowledgements(calls: { path: string; body: unknown }[]) {
  return calls
    .filter((call) => call.path === '/api/agent-reader/ack')
    .map((call) => JSON.parse(call.body as string) as Record<string, unknown>);
}

async function pendingAudio() {
  let finish!: (value: unknown) => void;
  const api = prepare({
    [`GET /api/documents/${doc.id}/segments`]: (url: URL) =>
      url.pathname.endsWith('/segments/0/audio')
        ? new Promise((resolve) => {
            finish = resolve;
          })
        : new Response(new Blob(['wav'])),
  });
  const view = open();
  await waitFor(() => expect(view.player()?.state.status).toBe('loading'));
  return { api, view, finish: (value: unknown) => finish(value) };
}

async function pendingPreferences() {
  let release!: (value: unknown) => void;
  const api = prepare({
    'GET /api/preferences': () =>
      new Promise((resolve) => {
        release = resolve;
      }),
  });
  const view = open();
  await screen.findByRole('heading', { level: 1, name: doc.title });
  return { api, view, release: (value: unknown) => release(value) };
}

describe('Agent reader handoff', () => {
  it('uses the real app route and reports actual playback while preserving highlighting', async () => {
    const api = prepare();
    history.replaceState({}, '', `/agent-read#${ticket}`);
    render(<App />);
    await screen.findByRole('heading', { level: 1, name: doc.title });
    await waitFor(() =>
      expect(acknowledgements(api.calls)).toEqual([
        { requestId: request.requestId, ackToken: request.ackToken, status: 'playing' },
      ]),
    );
    expect(history.state).not.toHaveProperty('ackToken');
    expect(location.hash).toBe('');
    expect(document.querySelector('[data-index="0"]')).toHaveAttribute('data-active', 'true');
    const audio = api.calls.find((call) => call.path.endsWith('/segments/0/audio'));
    expect(audio?.query.get('voice')).toBe(request.voiceId);
    expect(audio?.query.get('pace')).toBe('1.2');
  });

  it('claims once under StrictMode and waits for preferences and sentence styling', async () => {
    let releasePreferences!: (value: unknown) => void;
    let releaseStyles!: (value: unknown) => void;
    const api = prepare({
      'GET /api/preferences': () =>
        new Promise((resolve) => {
          releasePreferences = resolve;
        }),
      [`GET /api/documents/${doc.id}/styles`]: () =>
        new Promise((resolve) => {
          releaseStyles = resolve;
        }),
    });
    const view = open(undefined, true);
    await screen.findByRole('heading', { level: 1, name: doc.title });
    expect(acknowledgements(api.calls)).toEqual([]);
    await act(async () =>
      releasePreferences({ ...preferences, defaultVoiceId: 'kokoro:af_heart', pace: 0.8 }),
    );
    expect(api.calls.some((call) => call.path.includes('/segments/'))).toBe(false);
    await act(async () => releaseStyles(styles({ segments: [{ index: 0, skip: 'manual' }] })));
    await waitFor(() => expect(acknowledgements(api.calls)[0]?.status).toBe('playing'));
    expect(api.calls.filter((call) => call.path === '/api/agent-reader/claim')).toHaveLength(1);
    expect(view.player().state).toMatchObject({
      voiceId: request.voiceId,
      pace: 1.2,
      segmentIndex: 1,
    });
    expect(document.querySelector('[data-index="1"]')).toHaveAttribute('data-active', 'true');
    expect(api.calls.some((call) => call.path.endsWith('/segments/0/audio'))).toBe(false);
  });

  it('can open without autoplay and does not synthesize a clip', async () => {
    const api = prepare({}, { autoplay: false });
    const view = open();
    await waitFor(() => expect(acknowledgements(api.calls)[0]?.status).toBe('opened'));
    expect(view.media.play).not.toHaveBeenCalled();
    expect(api.calls.some((call) => call.path.includes('/segments/'))).toBe(false);
  });

  it('reports the required Play action and clears the prompt after a real manual retry', async () => {
    const api = prepare();
    const view = open();
    view.media.play.mockRejectedValueOnce(new DOMException('blocked', 'NotAllowedError'));
    await waitFor(() =>
      expect(acknowledgements(api.calls)[0]).toMatchObject({
        status: 'user_action_required',
        errorCode: 'autoplay_blocked',
      }),
    );
    expect(await screen.findByText('Press Play to allow audio.')).toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole('button', { name: /^(Play|Resume)$/ }));
    await waitFor(() => expect(view.player().state.status).toBe('playing'));
    expect(screen.queryByText('Press Play to allow audio.')).not.toBeInTheDocument();
    expect(acknowledgements(api.calls)).toHaveLength(1);
  });

  it('reports synthesis failure without claiming playback', async () => {
    const api = prepare({
      [`GET /api/documents/${doc.id}/segments`]: () =>
        json({ error: { code: 'engine_missing', message: 'Install the local model.' } }, 503),
    });
    open();
    await waitFor(() =>
      expect(acknowledgements(api.calls)[0]).toMatchObject({
        status: 'failed',
        errorCode: 'playback_failed',
      }),
    );
  });

  it('reports a user pause while synthesis was pending rather than a false playback success', async () => {
    const { api, view, finish } = await pendingAudio();
    act(() => view.player().controller.pause());
    await act(async () =>
      finish(new Response(new Blob(['wav']), { headers: { 'X-Audio-Duration': '2' } })),
    );
    await waitFor(() =>
      expect(acknowledgements(api.calls)[0]).toMatchObject({
        status: 'user_action_required',
        errorCode: 'playback_interrupted',
      }),
    );
  });

  it.each(['', 'x'.repeat(64), 'a'.repeat(63), 'https://example.com'])(
    'rejects malformed capability %s without a claim',
    async (value) => {
      const api = prepare();
      open(`/agent-read#${value}`);
      expect(
        await screen.findByText(
          'This reading link is invalid. Ask your agent to create a new request.',
        ),
      ).toBeInTheDocument();
      expect(location.hash).toBe('');
      expect(api.calls.some((call) => call.path === '/api/agent-reader/claim')).toBe(false);
    },
  );

  it('handles a refused or expired claim under effect replay', async () => {
    const api = prepare({
      'POST /api/agent-reader/claim': () =>
        json({ error: { code: 'ticket_expired', message: 'Ask your agent to try again.' } }, 410),
    });
    open(undefined, true);
    expect(await screen.findByText('Ask your agent to try again.')).toBeInTheDocument();
    expect(api.calls.filter((call) => call.path === '/api/agent-reader/claim')).toHaveLength(1);
    expect(acknowledgements(api.calls)).toEqual([]);
  });

  it('acknowledges a deleted document through the request capability', async () => {
    const api = prepare({
      [`GET /api/documents/${doc.id}`]: () =>
        json({ error: { code: 'not_found', message: 'Gone.' } }, 404),
    });
    open();
    await waitFor(() =>
      expect(acknowledgements(api.calls)[0]).toMatchObject({
        status: 'failed',
        errorCode: 'document_load_failed',
      }),
    );
  });

  it('never sends an acknowledgement for an ordinary reader without a handoff', async () => {
    const api = prepare();
    open(`/read/${doc.id}`);
    await screen.findByRole('heading', { level: 1, name: doc.title });
    expect(acknowledgements(api.calls)).toEqual([]);
    expect(takeReadRequest(doc.id)).toBeUndefined();
  });

  it.each(['clear', 'different'])(
    'never acknowledges another document after an interruption: %s',
    async (change) => {
      const { api, view, finish } = await pendingAudio();
      await act(async () => {
        if (change === 'clear') view.player().controller.unload();
        else await view.player().controller.load({ ...doc, id: 'another-document' }, 0, false);
        finish(new Response(new Blob(['wav'])));
      });
      await waitFor(() =>
        expect(acknowledgements(api.calls)[0]).toMatchObject({
          status: 'failed',
          errorCode: 'playback_interrupted',
        }),
      );
    },
  );

  it.each(['load', 'voice', 'pace'])(
    'does not mutate or play another document after the awaited %s stage',
    async (stage) => {
      let releaseStyles!: (value: unknown) => void;
      let releaseStage!: () => void;
      const held = new Promise<void>((resolve) => {
        releaseStage = resolve;
      });
      const api = prepare({
        [`GET /api/documents/${doc.id}/styles`]: () =>
          new Promise((resolve) => {
            releaseStyles = resolve;
          }),
      });
      const view = open();
      await screen.findByRole('heading', { level: 1, name: doc.title });
      await waitFor(() => expect(view.player().preferencesReady).toBe(true));
      const controller = view.player().controller;
      const load = controller.load.bind(controller);
      const voice = controller.setVoice.bind(controller);
      const pace = controller.setPace.bind(controller);
      const play = vi.spyOn(controller, 'play');
      let waiting = false;
      if (stage === 'load')
        vi.spyOn(controller, 'load').mockImplementationOnce(async (...args) => {
          await load(...args);
          waiting = true;
          await held;
        });
      else if (stage === 'voice')
        vi.spyOn(controller, 'setVoice').mockImplementationOnce(async (id) => {
          await voice(id);
          waiting = true;
          await held;
        });
      else
        vi.spyOn(controller, 'setPace').mockImplementationOnce(async (value) => {
          await pace(value);
          waiting = true;
          await held;
        });
      await act(async () => releaseStyles(styles()));
      await waitFor(() => expect(waiting).toBe(true));
      await act(async () => {
        await load({ ...doc, id: 'unrequested-document' }, 0, false);
        releaseStage();
      });
      await waitFor(() =>
        expect(acknowledgements(api.calls)[0]).toMatchObject({
          status: 'failed',
          errorCode: 'playback_interrupted',
        }),
      );
      expect(play).not.toHaveBeenCalled();
      expect(controller.getState().document?.id).toBe('unrequested-document');
      expect(view.media.play).not.toHaveBeenCalled();
    },
  );

  it('reports a controller failure before the media attempt', async () => {
    const { api, view, release } = await pendingPreferences();
    const setVoice = view.player().controller.setVoice.bind(view.player().controller);
    vi.spyOn(view.player().controller, 'setVoice').mockImplementation((voiceId) =>
      voiceId === request.voiceId
        ? Promise.reject(new Error('media unavailable'))
        : setVoice(voiceId),
    );
    await act(async () => release(preferences));
    await waitFor(() =>
      expect(acknowledgements(api.calls)[0]).toMatchObject({
        status: 'failed',
        errorCode: 'playback_failed',
      }),
    );
  });

  it('reports an ended short clip as played rather than losing its successful result', async () => {
    const { api, view, release } = await pendingPreferences();
    const controller = view.player().controller;
    const play = controller.play.bind(controller);
    vi.spyOn(controller, 'play').mockImplementation(async () => {
      await play();
      await controller.seek(doc.segmentCount - 1);
      view.media.emit('ended');
    });
    await act(async () => release(preferences));
    await waitFor(() => expect(acknowledgements(api.calls)[0]?.status).toBe('playing'));
    expect(controller.getState().status).toBe('ended');
  });

  it('keeps playback functional if the acknowledgement cannot be delivered', async () => {
    const api = prepare({
      'POST /api/agent-reader/ack': () =>
        json({ error: { code: 'request_expired', message: 'Expired.' } }, 410),
    });
    const view = open();
    await waitFor(() => expect(acknowledgements(api.calls)[0]?.status).toBe('playing'));
    expect(view.player().state.status).toBe('playing');
  });

  it('reports unavailable document styling rather than playing without its skip rules', async () => {
    const api = prepare({
      [`GET /api/documents/${doc.id}/styles`]: () =>
        json({ error: { code: 'unavailable', message: 'Unavailable.' } }, 503),
    });
    const view = open();
    await waitFor(() =>
      expect(acknowledgements(api.calls)[0]).toMatchObject({
        status: 'failed',
        errorCode: 'document_load_failed',
      }),
    );
    expect(view.media.play).not.toHaveBeenCalled();
  });

  it.each([true, false])(
    'does not retain a handoff after its page closed (claim success: %s)',
    async (success) => {
      let finish!: (value: unknown) => void;
      prepare({
        'POST /api/agent-reader/claim': () =>
          new Promise((resolve) => {
            finish = resolve;
          }),
      });
      const view = open();
      await waitFor(() => expect(finish).toBeTypeOf('function'));
      view.unmount();
      await act(async () =>
        finish(success ? request : json({ error: { code: 'expired', message: 'Expired.' } }, 410)),
      );
      expect(takeReadRequest(doc.id)).toBeUndefined();
    },
  );

  it('claims once when StrictMode replays the root effect', async () => {
    const api = prepare();
    history.replaceState({}, '', `/agent-read#${ticket}`);
    render(
      <StrictMode>
        <MemoryRouter initialEntries={[`/agent-read#${ticket}`]}>
          <Routes>
            <Route path="/agent-read" element={<AgentReadPage />} />
            <Route path="/read/:documentId" element={<h1>Opened</h1>} />
          </Routes>
        </MemoryRouter>
      </StrictMode>,
    );
    await screen.findByRole('heading', { name: 'Opened' });
    expect(api.calls.filter((call) => call.path === '/api/agent-reader/claim')).toHaveLength(1);
  });

  it('does not break the missing-document screen when its failure acknowledgement is refused', async () => {
    const api = prepare({
      [`GET /api/documents/${doc.id}`]: () =>
        json({ error: { code: 'not_found', message: 'Gone.' } }, 404),
      'POST /api/agent-reader/ack': () =>
        json({ error: { code: 'expired', message: 'Expired.' } }, 410),
    });
    open();
    await waitFor(() => expect(acknowledgements(api.calls)[0]?.status).toBe('failed'));
    expect(await screen.findByRole('heading', { name: /no longer/ })).toBeInTheDocument();
  });
});

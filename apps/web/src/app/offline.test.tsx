// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Keep the local app usable when the browser reports no network connection.
 * Scope: The real root providers load an uncached library while offline, and a local paste mutation
 *   still creates and opens a document after the browser loses its connection.
 * Does NOT belong: An unreachable server (connection.test.tsx) or real-model audio (Playwright).
 */
import { onlineManager } from '@tanstack/react-query';
import { act, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { documentDetail, kokoro, mockApi, preferences, readerRoutes, voice } from '@/test/render';
import { App } from './App';

afterEach(() => {
  onlineManager.setOnline(true);
  vi.unstubAllGlobals();
  window.history.pushState({}, '', '/');
});

const existing = documentDetail({ title: 'Already on this computer' });
const added = documentDetail({ id: 'b'.repeat(32), title: 'Added without internet' });

function localApi() {
  let pasted = false;
  return mockApi({
    'GET /api/engines': [kokoro()],
    'GET /api/preferences': preferences,
    'GET /api/voices': [voice()],
    'GET /api/documents': () => (pasted ? [existing, added] : [existing]),
    'GET /api/library/folders': [],
    'GET /api/library/collections': [],
    'POST /api/documents/text': () => {
      pasted = true;
      return added;
    },
    'PUT /api/documents/': {},
    ...readerRoutes(added),
  });
}

describe('Local API without an internet connection', () => {
  it('loads an uncached library when the browser is offline', async () => {
    const { calls } = localApi();
    window.history.pushState({}, '', '/library');
    onlineManager.setOnline(false);
    const view = render(<App />);
    try {
      expect(await screen.findByRole('link', { name: existing.title })).toBeInTheDocument();
      expect(calls.some((call) => call.method === 'GET' && call.path === '/api/documents')).toBe(
        true,
      );
      expect(screen.queryByRole('status', { name: 'Loading documents' })).not.toBeInTheDocument();
      expect(screen.getByRole('status', { name: 'Connection' })).toBeEmptyDOMElement();
    } finally {
      view.unmount();
      onlineManager.setOnline(true);
    }
  });

  it('adds and opens a document after the browser goes offline', async () => {
    const { calls } = localApi();
    window.history.pushState({}, '', '/library');
    const user = userEvent.setup();
    const view = render(<App />);
    try {
      await screen.findByRole('link', { name: existing.title });
      act(() => onlineManager.setOnline(false));
      await user.click(screen.getByRole('button', { name: 'Paste text' }));
      const dialog = screen.getByRole('dialog', { name: 'Paste text' });
      await user.type(within(dialog).getByLabelText('Title (optional)'), added.title);
      await user.type(
        within(dialog).getByLabelText('Text'),
        'A new sentence, stored on this computer.',
      );
      await user.click(within(dialog).getByRole('button', { name: 'Add to library' }));
      expect(
        await screen.findByRole('heading', { level: 1, name: added.title }),
      ).toBeInTheDocument();
      expect(
        calls.find((call) => call.method === 'POST' && call.path === '/api/documents/text')?.body,
      ).toBe(
        JSON.stringify({
          text: 'A new sentence, stored on this computer.',
          speechMarks: false,
          title: added.title,
        }),
      );
      expect(calls.some((call) => call.path === `/api/documents/${added.id}`)).toBe(true);
      expect(onlineManager.isOnline()).toBe(false);
    } finally {
      view.unmount();
      onlineManager.setOnline(true);
    }
  });
});

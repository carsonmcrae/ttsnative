// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Read documents through the authenticated agent interface in the real browser/server.
 * Scope: Private isolated discovery, native upload and one-shot ticket, real Kokoro audio and
 *   sentence highlighting; an explicitly simulated media.play refusal followed by a real click.
 * Does NOT belong: Installed Windows activation, cloud inference or the skill client tests.
 */
import { expect, test } from '@playwright/test';
import { readdir, readFile } from 'node:fs/promises';
import { request as httpRequest } from 'node:http';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { isSegmentAudio, waitForActiveSegment } from './helpers';

interface Instance {
  origin: string;
  token: string;
}

interface Handoff {
  requestId: string;
  ticket: string;
  documentId: string;
}

// Trace bodies/URLs would persist request capabilities. Keep them out of test artifacts as well.
test.use({ trace: 'off' });

function nativeJson<T>(
  instance: Instance,
  route: string,
  method = 'GET',
  body?: string,
  contentType = 'application/json',
): Promise<{ status: number; body: T }> {
  return new Promise((resolve, reject) => {
    // Node fetch adds Sec-Fetch headers; native authentication deliberately rejects browser traffic.
    const request = httpRequest(
      new URL(route, instance.origin),
      {
        method,
        headers: {
          Authorization: `Bearer ${instance.token}`,
          'X-LTTS-Client': 'agent',
          'Content-Type': contentType,
          ...(body === undefined ? {} : { 'Content-Length': Buffer.byteLength(body) }),
        },
      },
      (response) => {
        const chunks: Buffer[] = [];
        response.on('data', (chunk: Buffer) => chunks.push(chunk));
        response.on('end', () => {
          try {
            resolve({
              status: response.statusCode ?? 0,
              body: JSON.parse(Buffer.concat(chunks).toString('utf8')) as T,
            });
          } catch {
            reject(new Error('The isolated agent server returned invalid JSON.'));
          }
        });
        response.on('error', () => reject(new Error('The isolated agent response failed.')));
      },
    );
    request.on('error', () => reject(new Error('The isolated agent server could not be reached.')));
    request.end(body);
  });
}

async function instanceFor(baseURL: string): Promise<Instance> {
  const origin = new URL(baseURL);
  if (origin.hostname !== '127.0.0.1' || origin.protocol !== 'http:')
    throw new Error('Agent E2E requires its isolated loopback server.');
  const directory = path.join(tmpdir(), 'ttsnative-e2e-agent', origin.port);
  for (const name of await readdir(directory)) {
    const descriptor = JSON.parse(
      await readFile(path.join(directory, name, 'instance.json'), 'utf8'),
    ) as Instance;
    if (descriptor.origin !== origin.origin) continue;
    const response = await nativeJson<{ protocolVersion: number }>(
      descriptor,
      '/api/agent/v1/status',
    );
    if (response.status === 200 && response.body.protocolVersion === 1) return descriptor;
  }
  throw new Error('The isolated agent discovery descriptor was not found.');
}

async function createRead(instance: Instance, text: string, autoplay = true): Promise<Handoff> {
  const document = await nativeJson<{ id: string }>(
    instance,
    '/api/agent/v1/documents/upload?filename=agent-reader.txt',
    'POST',
    text,
    'application/octet-stream',
  );
  expect(document.status).toBe(201);
  const handoff = await nativeJson<Omit<Handoff, 'documentId'>>(
    instance,
    '/api/agent/v1/read-requests',
    'POST',
    JSON.stringify({
      documentId: document.body.id,
      voiceId: 'kokoro:bm_george',
      pace: 1,
      autoplay,
    }),
  );
  expect(handoff.status).toBe(201);
  // Assert only booleans: a failed assertion must never print a ticket value.
  expect(/^[0-9a-f]{64}$/.test(handoff.body.ticket)).toBe(true);
  return { ...handoff.body, documentId: document.body.id };
}

test('agent handoff plays real local speech and advances sentence highlighting', async ({
  page,
  baseURL,
}) => {
  const instance = await instanceFor(baseURL!);
  const handoff = await createRead(
    instance,
    'Sunlight enters a quiet room. A small bird sings outside. This local narration keeps its place.',
  );
  const firstAudio = page.waitForResponse((response) => isSegmentAudio(response, 0));
  await page.goto(`/agent-read#${handoff.ticket}`).catch(() => {
    throw new Error('The agent reader handoff page could not be opened.');
  });
  const audio = await firstAudio;
  expect(audio.status()).toBe(200);
  expect(audio.headers()['content-type']).toBe('audio/wav');
  expect(Number(audio.headers()['x-audio-duration'])).toBeGreaterThan(0.5);
  await expect
    .poll(
      async () =>
        (
          await nativeJson<{ status: string }>(
            instance,
            `/api/agent/v1/read-requests/${handoff.requestId}`,
          )
        ).body.status,
    )
    .toBe('playing');
  expect(await page.evaluate(() => location.hash === '')).toBe(true);
  await waitForActiveSegment(page, 1);
  await waitForActiveSegment(page, 2);
});

test('blocked autoplay reports user action, and an explicit Play recovers with real audio', async ({
  page,
  baseURL,
}) => {
  const instance = await instanceFor(baseURL!);
  const handoff = await createRead(
    instance,
    'The orange boat crosses the river. The keeper opens the blue gate. A new page is ready.',
  );
  await page.addInitScript(() => {
    const play = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = () =>
      Promise.reject(new DOMException('User action required', 'NotAllowedError'));
    window.addEventListener(
      'ttsnative-test-allow-audio',
      () => {
        HTMLMediaElement.prototype.play = play;
      },
      { once: true },
    );
  });
  const firstAudio = page.waitForResponse((response) => isSegmentAudio(response, 0));
  await page.goto(`/agent-read#${handoff.ticket}`).catch(() => {
    throw new Error('The agent reader handoff page could not be opened.');
  });
  expect((await firstAudio).status()).toBe(200);
  await expect
    .poll(
      async () =>
        (
          await nativeJson<{ status: string }>(
            instance,
            `/api/agent/v1/read-requests/${handoff.requestId}`,
          )
        ).body.status,
    )
    .toBe('user_action_required');
  await expect(page.getByText('Press Play to allow audio.')).toBeVisible();
  await page.evaluate(() => window.dispatchEvent(new Event('ttsnative-test-allow-audio')));
  await page
    .getByRole('region', { name: 'Audio player' })
    .getByRole('button', { name: 'Play', exact: true })
    .click();
  await waitForActiveSegment(page, 1);
  await expect(page.getByText('Press Play to allow audio.')).toHaveCount(0);
});

test('a claimed open request stays pending until the real reader loads its document', async ({
  page,
  baseURL,
}) => {
  const instance = await instanceFor(baseURL!);
  const handoff = await createRead(
    instance,
    'A quiet library waits for the reader. This page should open without playing.',
    false,
  );
  let releaseMetadata!: () => void;
  let requestedMetadata!: () => void;
  const held = new Promise<void>((resolve) => {
    releaseMetadata = resolve;
  });
  const requested = new Promise<void>((resolve) => {
    requestedMetadata = resolve;
  });
  const audioRequests: string[] = [];
  page.on('request', (request) => {
    if (/\/segments\/\d+\/audio/.test(request.url())) audioRequests.push(request.url());
  });
  await page.route(`**/api/documents/${handoff.documentId}`, async (route) => {
    requestedMetadata();
    await held;
    await route.continue();
  });
  const claimed = page.waitForResponse((response) =>
    response.url().endsWith('/api/agent-reader/claim'),
  );
  await page.goto(`/agent-read#${handoff.ticket}`).catch(() => {
    throw new Error('The agent reader handoff page could not be opened.');
  });
  expect((await claimed).status()).toBe(200);
  await requested;
  await expect(page.getByRole('status', { name: 'Loading document' })).toBeVisible();
  expect(
    (
      await nativeJson<{ status: string }>(
        instance,
        `/api/agent/v1/read-requests/${handoff.requestId}`,
      )
    ).body.status,
  ).toBe('pending');
  releaseMetadata();
  await expect
    .poll(
      async () =>
        (
          await nativeJson<{ status: string }>(
            instance,
            `/api/agent/v1/read-requests/${handoff.requestId}`,
          )
        ).body.status,
    )
    .toBe('opened');
  await expect(page.getByRole('heading', { level: 1, name: 'agent-reader' })).toBeVisible();
  expect(audioRequests).toHaveLength(0);
  await expect(
    page
      .getByRole('region', { name: 'Audio player' })
      .getByRole('button', { name: 'Play', exact: true }),
  ).toBeVisible();
});

// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Verify the actual standalone client against authenticated local HTTP fixtures.
 * Scope: Discovery, data-only uploads, truthful playback, exports/recovery, redirects and files.
 * Does NOT belong: Real synthesis or manual computer interaction.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import { promises as operations, writeFileSync } from 'node:fs';
import path from 'node:path';
import { promisify } from 'node:util';
import { execFile } from 'node:child_process';
import {
  main,
  localPath,
  loopback,
  descriptor,
  discoveryRoot,
} from '../../integrations/agent-skills/ttsnative-reader/scripts/ttsnative.mjs';
import { fixture, writeDescriptor, PRIVATE, TOKEN, TICKET, JOB } from './client-fixture.mjs';

function capturedBrowser() {
  let opened = '';
  return {
    launch: async (/** @type {string} */ _file, /** @type {string[]} */ args) => {
      opened = args.at(-1) || '';
      return true;
    },
    url: () => new URL(opened),
  };
}

test('native status authenticates without browser headers and exposes no credential', async (t) => {
  const f = await fixture(t);
  const result = await f.run(['status']);
  assert.equal(result.code, 'ready');
  assert(!JSON.stringify(result).includes(TOKEN));
  assert.equal(f.requests[0]?.headers.origin, undefined);
  assert.equal(f.requests[0]?.headers['sec-fetch-mode'], undefined);
  assert.equal(
    (await descriptor(path.join(f.discovery, f.data.instanceId, 'instance.json'))).instanceId,
    f.data.instanceId,
  );
});
for (const extension of ['pdf', 'epub', 'docx', 'md', 'markdown', 'txt'])
  test(`open uploads ${extension} as bytes and waits for explicit reader acknowledgement`, async (t) => {
    const f = await fixture(t);
    f.model.readStates = ['opened'];
    const file = await f.file(extension);
    const result = await f.run(['open', file, '--wait-seconds', '0']);
    assert.equal(result.code, 'reader_opened');
    const upload = f.requests.find((r) => r.path === '/documents/upload');
    assert.equal(upload?.body.toString(), PRIVATE);
    const body = JSON.parse(
      f.requests.find((r) => r.path === '/read-requests')?.body.toString() || '{}',
    );
    assert.equal(body.autoplay, false);
    assert(!JSON.stringify(result).includes(PRIVATE));
    assert(!JSON.stringify(result).includes(TICKET));
  });
test('read acknowledges actual playing and honors voice and pace', async (t) => {
  const f = await fixture(t);
  const result = await f.run([
    'read',
    await f.file('txt'),
    '--voice',
    'kokoro:test',
    '--pace',
    '1.25',
    '--wait-seconds',
    '0',
  ]);
  assert.equal(result.code, 'playback_started');
  const req = f.requests.find((r) => r.path === '/read-requests');
  assert.deepEqual(JSON.parse(req?.body.toString() || '{}'), {
    documentId: 'd'.repeat(32),
    voiceId: 'kokoro:test',
    pace: 1.25,
    autoplay: true,
  });
});

test('development UI can use another loopback port without receiving native credentials or uploads', async (t) => {
  const api = await fixture(t),
    ui = await fixture(t, '9'.repeat(32));
  api.model.uiUrl = ui.origin;
  await writeDescriptor(api.discovery, { ...api.data, uiUrl: ui.origin });
  const browser = capturedBrowser(),
    result = await api.run(['read', await api.file('markdown'), '--wait-seconds', '0'], browser);
  assert.equal(result.code, 'playback_started');
  assert.equal(browser.url().origin, ui.origin);
  assert.equal(browser.url().pathname, '/agent-read');
  assert.equal(ui.requests.length, 0);
  assert(!JSON.stringify(result).includes(TICKET));
});

test('MP3 export succeeds without ffmpeg', async (t) => {
  const f = await fixture(t);
  f.model.ffmpeg = false;
  const output = path.join(f.root, 'without-ffmpeg.mp3');
  const result = await f.run(['export', await f.file('txt'), '--output', output]);
  assert.equal(result.code, 'export_completed');
  assert.equal((await fs.readFile(output)).subarray(0, 3).toString(), 'ID3');
});

test('localhost is permitted only for the authenticated UI handoff, never native requests', async (t) => {
  const f = await fixture(t),
    uiUrl = 'http://localhost:5173';
  assert.throws(() => loopback(uiUrl));
  assert.equal(loopback(uiUrl, true), uiUrl);
  for (const unsafe of [
    'http://localhost.example',
    'http://localhost/?secret=x',
    'http://localhost/#ticket',
  ])
    assert.throws(() => loopback(unsafe, true));
  f.model.uiUrl = uiUrl;
  await writeDescriptor(f.discovery, { ...f.data, uiUrl });
  const browser = capturedBrowser(),
    result = await f.run(['read', await f.file('txt'), '--wait-seconds', '0'], browser);
  assert.equal(result.code, 'playback_started');
  assert.equal(browser.url().origin, uiUrl);
  assert.equal(browser.url().hash, '#' + TICKET);
  assert(f.requests.some((r) => r.path === '/documents/upload'));
  const count = f.requests.length;
  const invalid = await writeDescriptor(f.discovery, { ...f.data, origin: uiUrl, uiUrl });
  await assert.rejects(descriptor(invalid), { code: 'invalid_instance' });
  assert.equal((await f.run(['read', await f.file('txt')])).code, 'launch_required');
  assert.equal(f.requests.length, count);
});

for (const [apiCode, expected, status] of [
  ['no_text', 'no_text', 'unsupported'],
  ['export_queue_full', 'export_queue_full', 'user_action_required'],
  ['private\n' + PRIVATE, 'server_request_failed', 'error'],
  ['x'.repeat(65), 'server_request_failed', 'error'],
])
  test(`bounded API error projection: ${expected}/${status}`, async (t) => {
    const f = await fixture(t);
    f.model.failPath = '/documents/upload';
    f.model.httpCode = 422;
    f.model.errorCode = apiCode || '';
    const result = await f.run(['read', await f.file('txt')]);
    assert.equal(result.code, expected);
    assert.equal(result.status, status);
    assert(!JSON.stringify(result).includes(PRIVATE));
  });
for (const state of ['pending', 'opened', 'user_action_required'])
  test(`read never calls ${state} successful playback`, async (t) => {
    const f = await fixture(t);
    f.model.readStates = [state];
    const result = await f.run(['read', await f.file('txt'), '--wait-seconds', '0']);
    assert.equal(result.status, 'user_action_required');
    assert.equal(result.code, 'press_play_in_reader');
  });
test('failed playback and unavailable browser are reported truthfully', async (t) => {
  const f = await fixture(t),
    file = await f.file('txt');
  f.model.readStates = ['failed'];
  assert.equal((await f.run(['read', file])).code, 'playback_failed');
  assert.equal((await f.run(['read', file], { launch: async () => false })).code, 'open_reader');
});
test('polls reader until acknowledgement rather than counting ticket creation', async (t) => {
  const f = await fixture(t);
  f.model.readStates = ['pending', 'opened', 'playing'];
  assert.equal(
    (await f.run(['read', await f.file('txt'), '--wait-seconds', '1'])).code,
    'playback_started',
  );
  assert.equal(f.requests.filter((r) => r.path.startsWith('/read-requests/')).length, 3);
});
for (const format of ['mp3', 'wav', 'm4b'])
  test(`exports ${format} through existing jobs and verifies the downloaded file`, async (t) => {
    const f = await fixture(t);
    f.setFormat(format);
    const out = path.join(f.root, 'audio.' + format);
    const result = await f.run([
      'export',
      await f.file('md'),
      '--format',
      format,
      '--output',
      out,
      '--wait-seconds',
      '0',
    ]);
    assert.equal(result.code, 'export_completed');
    assert.equal((await fs.stat(out)).size, 64);
    assert(!JSON.stringify(result).includes(PRIVATE));
    assert(!JSON.stringify(result).includes(TOKEN));
  });
test('only changed export progress is emitted', async (t) => {
  const f = await fixture(t);
  f.model.jobStates = ['running', 'running', 'running', 'running', 'succeeded'];
  f.model.progress = [0, 0, 0.24, 0.24, 1];
  /** @type {object[]} */ const events = [];
  const result = await f.run(
    [
      'export',
      await f.file('txt'),
      '--output',
      path.join(f.root, 'out.mp3'),
      '--wait-seconds',
      '2',
    ],
    { progress: (e) => events.push(e) },
  );
  assert.equal(result.status, 'success');
  assert.deepEqual(events, [
    { jobId: JOB, progress: 0 },
    { jobId: JOB, progress: 0.24 },
    { jobId: JOB, progress: 1 },
  ]);
});
test('existing outputs require permission and are not touched while starting an export', async (t) => {
  const f = await fixture(t),
    out = path.join(f.root, 'out.mp3'),
    file = await f.file('txt');
  await fs.writeFile(out, 'original');
  assert.equal((await f.run(['export', file, '--output', out])).code, 'output_exists');
  assert.equal(await fs.readFile(out, 'utf8'), 'original');
  assert(!f.requests.some((r) => r.path === '/documents/upload'));
  assert.equal((await f.run(['export', file, '--output', out, '--overwrite'])).status, 'success');
  assert.equal((await fs.stat(out)).size, 64);
});
test('bad audio preserves an existing output and cleans partial files', async (t) => {
  const f = await fixture(t),
    out = path.join(f.root, 'out.mp3');
  await fs.writeFile(out, 'original');
  f.model.badAudio = true;
  assert.equal(
    (await f.run(['export', await f.file('txt'), '--output', out, '--overwrite'])).code,
    'invalid_audio',
  );
  assert.equal(await fs.readFile(out, 'utf8'), 'original');
  assert(!(await fs.readdir(f.root)).some((n) => n.includes('.part-')));
});

test('a writable destination without hard-link support receives the actual audio bytes', async (t) => {
  const f = await fixture(t),
    output = path.join(f.root, 'portable.mp3'),
    expected = Buffer.alloc(64);
  expected.write('ID3');
  const unavailable = t.mock.method(operations, 'link', async () => {
    throw Object.assign(new Error('hard links are unsupported'), { code: 'ENOTSUP' });
  });
  const result = await f.run(['export', await f.file('txt'), '--output', output]);
  assert.equal(result.code, 'export_completed');
  assert.deepEqual(await fs.readFile(output), expected);
  assert.equal(unavailable.mock.callCount(), 0);
  assert(!(await fs.readdir(f.root)).some((n) => n.includes('.part-')));
});

test('exclusive copying preserves a destination created after output preflight', async (t) => {
  const f = await fixture(t),
    output = path.join(f.root, 'raced.mp3');
  await assert.rejects(fs.stat(output), { code: 'ENOENT' });
  let created = false;
  const result = await f.run(['export', await f.file('txt'), '--output', output], {
    progress: () => {
      writeFileSync(output, 'created by another process', { flag: 'wx' });
      created = true;
    },
  });
  assert(created);
  assert.equal(result.status, 'error');
  assert.equal(await fs.readFile(output, 'utf8'), 'created by another process');
  assert(f.requests.some((request) => request.path.endsWith('/download')));
  assert(!(await fs.readdir(f.root)).some((n) => n.includes('.part-')));
});

test('copy failure cleans the verified temporary download without reporting success or raw errors', async (t) => {
  const f = await fixture(t),
    output = path.join(f.root, 'failed.mp3');
  const failure = t.mock.method(
    operations,
    'copyFile',
    /** @type {typeof operations.copyFile} */ (
      async (source, target, mode) => {
        assert.equal((await fs.readFile(source)).subarray(0, 3).toString(), 'ID3');
        assert.equal(target, output);
        assert.equal(mode, operations.constants.COPYFILE_EXCL);
        throw Object.assign(new Error(PRIVATE), { code: 'ENOSPC' });
      }
    ),
  );
  const result = await f.run(['export', await f.file('txt'), '--output', output]);
  assert.equal(failure.mock.callCount(), 1);
  assert.equal(result.code, 'operation_failed');
  assert(!JSON.stringify(result).includes(PRIVATE));
  await assert.rejects(fs.stat(output), { code: 'ENOENT' });
  assert(!(await fs.readdir(f.root)).some((n) => n.includes('.part-')));
});
for (const state of ['paused', 'interrupted', 'failed', 'canceled', 'running'])
  test(`export ${state} retains its recoverable job and reports no completed output`, async (t) => {
    const f = await fixture(t);
    f.model.jobStates = [state];
    const out = path.join(f.root, 'out.mp3');
    const result = await f.run([
      'export',
      await f.file('txt'),
      '--output',
      out,
      '--wait-seconds',
      '0',
    ]);
    assert.equal(result.status, 'user_action_required');
    assert.equal(result.jobId, JOB);
    await assert.rejects(fs.stat(out));
  });
test('job recovery actions and downloads reuse the existing export endpoints', async (t) => {
  const f = await fixture(t);
  assert.equal((await f.run(['job', 'cancel', JOB])).code, 'cancel_confirmation_required');
  assert.equal(f.requests.length, 0);
  for (const action of ['pause', 'resume', 'cancel'])
    assert.equal((await f.run(['job', action, JOB, '--confirm-cancel'])).code, 'job_updated');
  assert.equal((await f.run(['job', 'status', JOB])).code, 'job_status');
  assert.equal(
    (await f.run(['job', 'download', JOB, '--output', path.join(f.root, 'job.mp3')])).code,
    'export_downloaded',
  );
  f.model.jobStates = ['paused'];
  assert.equal(
    (await f.run(['job', 'download', JOB, '--output', path.join(f.root, 'later.mp3')])).code,
    'export_not_ready',
  );
});
test('missing models, voice IDs, ffmpeg and file limits cause no upload', async (t) => {
  const f = await fixture(t),
    file = await f.file('txt'),
    out = path.join(f.root, 'x.mp3');
  assert.equal((await f.run(['read', file, '--voice', 'unknown'])).code, 'invalid_voice');
  const voice = f.model.voices[0];
  assert(voice);
  voice.available = false;
  assert.equal((await f.run(['read', file, '--voice', 'kokoro:test'])).code, 'voice_unavailable');
  assert.equal((await f.run(['read', file])).code, 'models_required');
  voice.available = true;
  f.model.ffmpeg = false;
  assert.equal(
    (await f.run(['export', file, '--format', 'm4b', '--output', out])).code,
    'ffmpeg_required',
  );
  f.model.maxUploadBytes = 1;
  assert.equal((await f.run(['read', file])).code, 'upload_too_large');
  assert(!f.requests.some((r) => r.path === '/documents/upload'));
});
test('local validation rejects missing/unsupported files, unsafe paths and invalid options', async (t) => {
  const f = await fixture(t);
  for (const args of [
    ['read'],
    ['read', path.join(f.root, 'missing.pdf')],
    ['read', await f.file('doc')],
    ['read', '\\\\server\\book.txt'],
    ['read', await f.file('txt'), '--pace', 'NaN'],
    ['job', 'oops', JOB],
    ['status', '--instance', '../'],
  ])
    assert.notEqual((await f.run(args)).status, 'success');
  const empty = await f.file('txt');
  await fs.writeFile(empty, '');
  assert.equal((await f.run(['read', empty])).code, 'invalid_file_size');
  assert.throws(() => localPath('https://example.com/book.txt'));
  assert.throws(() => localPath('a\0b'));
  for (const url of [
    'https://127.0.0.1',
    'http://localhost',
    'http://192.168.1.1',
    'http://u:p@127.0.0.1',
    'http://127.0.0.1/?x=1',
    'http://127.0.0.1/a',
  ])
    assert.throws(() => loopback(url));
  assert.equal(loopback('http://[::1]:3456'), 'http://[::1]:3456');
  assert(
    discoveryRoot({ XDG_STATE_HOME: '/tmp/state' }, 'linux').endsWith(
      path.join('state', 'ttsnative', 'agent'),
    ),
  );
});
for (const route of ['/status', '/documents/upload', '/exports/' + JOB + '/download'])
  test(`refuses redirects at ${route} without following or leaking credentials`, async (t) => {
    const f = await fixture(t);
    f.model.failPath = route;
    f.model.httpCode = 307;
    const result = await f.run([
      'export',
      await f.file('txt'),
      '--output',
      path.join(f.root, 'out.mp3'),
    ]);
    assert.notEqual(result.status, 'success');
    assert(!JSON.stringify(result).includes(TOKEN));
    assert(!JSON.stringify(result).includes(PRIVATE));
    assert(!f.requests.some((r) => r.path === '/private'));
  });
test('ambiguous authenticated instances require explicit selection and source roots never cross', async (t) => {
  const f = await fixture(t),
    other = await fixture(t, '1'.repeat(32));
  await writeDescriptor(f.discovery, other.data);
  assert.equal((await f.run(['status'])).code, 'ambiguous_instance');
  assert.equal(
    (await f.run(['status', '--instance', f.data.instanceId])).instanceId,
    f.data.instanceId,
  );
  assert.equal(
    (await f.run(['status', '--source-root', other.sourceRoot])).instanceId,
    other.data.instanceId,
  );
  assert.equal((await f.run(['status', '--source-root', f.root])).code, 'launch_required');
});
test('stale, wrong-identity, malformed and proxy settings never bypass authentication', async (t) => {
  const f = await fixture(t);
  f.model.identity = '0'.repeat(32);
  assert.equal((await f.run(['status'])).code, 'launch_required');
  f.model.identity = f.data.instanceId;
  const before = process.env.HTTP_PROXY;
  process.env.HTTP_PROXY = 'http://127.0.0.1:1';
  try {
    assert.equal((await f.run(['status'])).code, 'ready');
  } finally {
    if (before === undefined) delete process.env.HTTP_PROXY;
    else process.env.HTTP_PROXY = before;
  }
  f.model.badJson = true;
  assert.equal((await f.run(['status'])).code, 'launch_required');
  await writeDescriptor(f.discovery, { ...f.data, pid: 2_147_483_647 });
  assert.equal((await f.run(['status'])).code, 'launch_required');
});
test('the shipped file runs alone from another temporary location', async (t) => {
  const f = await fixture(t),
    standalone = path.join(f.root, 'standalone.mjs');
  await fs.copyFile(
    new URL(
      '../../integrations/agent-skills/ttsnative-reader/scripts/ttsnative.mjs',
      import.meta.url,
    ),
    standalone,
  );
  const result = await promisify(execFile)(
    process.execPath,
    [standalone, 'status', '--discovery-dir', f.discovery],
    { cwd: f.root },
  );
  assert.equal(JSON.parse(result.stdout).code, 'ready');
  assert(!result.stdout.includes(TOKEN));
  assert.equal(result.stderr, '');
});
test('CLI errors are structured and never echo input data', async () => {
  const result = await main(['--not-a-real-option', PRIVATE]);
  assert.equal(result.status, 'error');
  assert(!JSON.stringify(result).includes(PRIVATE));
});

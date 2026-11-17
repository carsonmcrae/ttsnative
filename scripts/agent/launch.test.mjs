// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Verify the standalone launcher without starting the user's app or a server.
 * Scope: Installation metadata, prepared source prerequisites, selection and spawn failures.
 * Does NOT belong: Installation or live application activation.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { ChildProcess, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { workspace as temporary } from './test-workspace.mjs';
import {
  main,
  installationExecutable,
} from '../../integrations/agent-skills/ttsnative-reader/scripts/launch.mjs';

/** @param {import('node:test').TestContext} t */
async function workspace(t) {
  return temporary(t, 'ttsnative-launch-');
}

test('quoted NSIS metadata and unquoted Store metadata resolve the real executable name', () => {
  assert.equal(
    installationExecutable('"C:\\Program Files\\TTSNative"'),
    'C:\\Program Files\\TTSNative\\TTSNative.exe',
  );
  assert.equal(
    installationExecutable('C:\\Program Files\\WindowsApps\\TTSNative'),
    'C:\\Program Files\\WindowsApps\\TTSNative\\TTSNative.exe',
  );
});

test('missing/invalid installations require action without spawning', async (t) => {
  const root = await workspace(t);
  let spawns = 0;
  const hooks = {
    platform: /** @type {NodeJS.Platform} */ ('win32'),
    query: () => [path.join(root, 'missing.exe')],
    start: /** @type {typeof import('node:child_process').spawn} */ (
      () => {
        spawns++;
        throw new Error('must not run');
      }
    ),
  };
  assert.equal((await main([], hooks)).code, 'installation_required');
  assert.equal(
    (await main(['--app', '\\\\server\\TTSNative.exe'], hooks)).code,
    'installation_detection_unavailable',
  );
  assert.equal(
    (await main(['--source-root', root, '--app', root], hooks)).code,
    'choose_one_installation',
  );
  assert.equal(spawns, 0);
  assert.equal(
    (await main(['--source-root', path.join(root, 'missing')], hooks)).code,
    'installation_detection_unavailable',
  );
});

test('detection deduplicates real executable paths and refuses ambiguous installations', async (t) => {
  const root = await workspace(t),
    app = path.join(root, 'TTSNative.exe');
  await fs.writeFile(app, 'synthetic executable placeholder; never executed');
  const hooks = { platform: /** @type {NodeJS.Platform} */ ('win32'), query: () => [app, app] };
  assert.equal((await main(['--detect-only'], hooks)).code, 'installed');
  const second = path.join(root, 'second', 'TTSNative.exe');
  await fs.mkdir(path.dirname(second));
  await fs.writeFile(second, 'synthetic');
  assert.equal(
    (await main([], { ...hooks, query: () => [app, second] })).code,
    'ambiguous_installation',
  );
});

for (const event of ['spawn', 'error'])
  test(`installed launch reports ${event} without claiming protocol/playback success`, async (t) => {
    const root = await workspace(t),
      app = path.join(root, 'TTSNative.exe'),
      child = new ChildProcess();
    await fs.writeFile(app, 'synthetic; never executed');
    const start = /** @type {typeof import('node:child_process').spawn} */ (
      (file, args, options) => {
        assert.equal(file, app);
        assert.deepEqual(args, []);
        assert.equal(options?.stdio, 'ignore');
        assert.equal(options?.detached, true);
        queueMicrotask(() => child.emit(event, new Error('PRIVATE path/recording')));
        return child;
      }
    );
    const result = await main(['--app', app], { start });
    assert.equal(result.code, event === 'spawn' ? 'app_started' : 'app_launch_required');
    assert.equal(result.integrationVerified, event === 'spawn' ? false : undefined);
    assert(!JSON.stringify(result).includes('PRIVATE'));
  });

test('prepared source is checked but cannot silently start another database owner', async (t) => {
  const root = await workspace(t);
  const args = ['--source-root', root];
  assert.equal((await main(args)).code, 'source_setup_required');
  const python = path.join(
    root,
    'apps/server/.venv',
    process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
  );
  const web = path.join(root, 'apps/web/dist/index.html');
  await fs.mkdir(path.dirname(python), { recursive: true });
  await fs.mkdir(path.dirname(web), { recursive: true });
  await fs.writeFile(python, 'synthetic; never executed');
  await fs.writeFile(web, 'synthetic');
  const result = await main(args, {
    start: /** @type {typeof import('node:child_process').spawn} */ (
      () => {
        throw new Error('must not start');
      }
    ),
  });
  assert.equal(result.code, 'source_start_required');
  assert.equal(result.prepared, true);
  assert.equal(result.status, 'user_action_required');
});

test('the launcher runs alone from an unrelated file and rejects unknown options as JSON', async (t) => {
  const root = await workspace(t),
    standalone = path.join(root, 'independent.mjs');
  await fs.copyFile(
    new URL('../../integrations/agent-skills/ttsnative-reader/scripts/launch.mjs', import.meta.url),
    standalone,
  );
  const { stdout, stderr } = await promisify(execFile)(
    process.execPath,
    [standalone, '--unknown', 'PRIVATE'],
    { cwd: root },
  );
  assert.equal(JSON.parse(stdout).code, 'installation_detection_unavailable');
  assert.equal(stderr, '');
  assert(!stdout.includes('PRIVATE'));
});

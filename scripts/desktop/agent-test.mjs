// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Exercise the shipped agent CLI against the actual Windows app installed by smoke-test.
 * Scope: Native private discovery, available voices, real desktop reader activation and its playing
 *   acknowledgement, and a completed MP3 export from public fixture text. Every command is a separate
 *   Node process running the standalone helper. Output never includes credentials, tickets or stderr.
 *   Invoked only by smoke-test.mjs on its disposable installer runner; this module installs nothing.
 * Does NOT belong: Browser mocks, test-only playback hooks, or driving a personal installed app.
 */
import { execFile } from 'node:child_process';
import { copyFile, mkdtemp, rm, stat } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { repoRoot } from '../lib/paths.mjs';

/** @typedef {{status?:string,code?:string,instanceId?:string,kind?:string,version?:string,
 *   voices?:{id:string,available:boolean}[],output?:string,bytes?:number}} Result */
const helper = path.join(
  repoRoot,
  'integrations',
  'agent-skills',
  'ttsnative-reader',
  'scripts',
  'ttsnative.mjs',
);
const TEMP_PREFIX = 'ttsnative-agent-smoke-';

/** @param {boolean} condition @param {string} message */
function check(condition, message) {
  if (!condition) throw new Error(`FAILED: ${message}`);
  console.log(`✓ ${message}`);
}

/** Keep child output private, including errors that could quote a URL or capability.
 * @param {string[]} args @param {number} [timeout] @returns {Promise<Result>} */
function command(args, timeout = 30_000) {
  return new Promise((resolve, reject) => {
    execFile(
      process.execPath,
      [helper, ...args],
      { cwd: repoRoot, windowsHide: true, timeout, maxBuffer: 1024 * 1024 },
      (error, stdout) => {
        if (error) {
          reject(new Error('FAILED: the installed agent CLI did not complete successfully'));
          return;
        }
        try {
          resolve(/** @type {Result} */ (JSON.parse(stdout)));
        } catch {
          reject(new Error('FAILED: the installed agent CLI returned invalid JSON'));
        }
      },
    );
  });
}

/** The caller has already installed and warmed this copy on a disposable Windows runner.
 * @param {string} version */
export async function installedAgentJourney(version) {
  check(process.platform === 'win32', 'the installed agent test runs on Windows');
  const ready = await command(['status']);
  check(
    ready.status === 'success' &&
      ready.code === 'ready' &&
      ready.kind === 'desktop' &&
      ready.version === version &&
      /^[0-9a-f]{32}$/.test(ready.instanceId ?? ''),
    'the standalone agent discovers this installed desktop version privately',
  );
  const selector = ['--instance', /** @type {string} */ (ready.instanceId)];
  const voices = await command(['voices', ...selector]);
  const voice = 'kokoro:af_heart';
  check(
    voices.status === 'success' &&
      voices.code === 'voices' &&
      !!voices.voices?.some((entry) => entry.id === voice && entry.available),
    'the standalone agent finds the installed bundled voice available',
  );

  const temporaryRoot = path.resolve(os.tmpdir());
  const folder = await mkdtemp(path.join(temporaryRoot, TEMP_PREFIX));
  try {
    const fixture = path.join(folder, 'publicsample.txt');
    await copyFile(path.join(repoRoot, 'tests', 'fixtures', 'documents', 'sample.txt'), fixture);
    const reading = await command(
      ['read', fixture, '--voice', voice, '--pace', '1', '--wait-seconds', '120', ...selector],
      150_000,
    );
    check(
      reading.status === 'success' && reading.code === 'playback_started',
      'the installed reader acknowledges actual playback after agent activation',
    );

    const output = path.join(folder, 'publicsample.mp3');
    const exported = await command(
      [
        'export',
        fixture,
        '--voice',
        voice,
        '--format',
        'mp3',
        '--output',
        output,
        '--wait-seconds',
        '240',
        ...selector,
      ],
      270_000,
    );
    check(
      exported.status === 'success' &&
        exported.code === 'export_completed' &&
        exported.output === output,
      'the standalone agent completes a real installed-app MP3 export',
    );
    const saved = await stat(output);
    check(
      saved.isFile() && saved.size === exported.bytes && saved.size > 5_000,
      'the verified MP3 is saved in the requested owned temporary folder',
    );
  } finally {
    // Delete only the exact, synthetic fixture/output folder created by this invocation.
    check(
      path.dirname(path.resolve(folder)) === temporaryRoot &&
        path.basename(folder).startsWith(TEMP_PREFIX),
      'agent smoke cleanup stays inside its own temporary folder',
    );
    await rm(folder, { recursive: true, force: true });
  }
}

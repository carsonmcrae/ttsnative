// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Independently detect/start the installed Windows app, or check a prepared source tree.
 * Scope: Static read-only installation queries and explicit application launch, without downloads.
 * Does NOT belong: Starting another source server against a possibly active database or API requests.
 */
import path from 'node:path';
import { realpath, stat } from 'node:fs/promises';
import { execFileSync, spawn } from 'node:child_process';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';

/** @returns {string[]} */
export function windowsApplications() {
  const query =
    "$r=@();Get-AppxPackage -Name 'CarsonMcRae.TTSNative' -ErrorAction SilentlyContinue|%{$r+=$_.InstallLocation};Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -ErrorAction SilentlyContinue|?{$_.DisplayName -eq 'TTSNative' -and $_.InstallLocation}|%{$r+=$_.InstallLocation};ConvertTo-Json -Compress -InputObject @($r|Select-Object -Unique)";
  const executable = path.join(
    process.env.SystemRoot || 'C:\\Windows',
    'System32',
    'WindowsPowerShell',
    'v1.0',
    'powershell.exe',
  );
  const result = JSON.parse(
    String(
      execFileSync(executable, ['-NoProfile', '-NonInteractive', '-Command', query], {
        encoding: 'utf8',
        timeout: 10_000,
        windowsHide: true,
        stdio: ['ignore', 'pipe', 'ignore'],
      }),
    ),
  );
  return Array.isArray(result)
    ? result.filter((item) => typeof item === 'string').map(installationExecutable)
    : [];
}
/** @param {string} folder */
export function installationExecutable(folder) {
  return path.win32.join(folder.replace(/^"(.*)"$/, '$1'), 'TTSNative.exe');
}
/** @param {string} value */
function checkedPath(value) {
  if (
    !value ||
    /^[\\/]{2}|^[a-z]+:\/\//i.test(value) ||
    [...value].some((letter) => letter.charCodeAt(0) < 32)
  )
    throw new Error('invalid_local_path');
  return path.resolve(value);
}
/** @param {string} source @param {NodeJS.Platform} platform */
async function prepared(source, platform) {
  const root = await realpath(checkedPath(source));
  const python = path.join(
    root,
    'apps',
    'server',
    '.venv',
    platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
  );
  const web = path.join(root, 'apps', 'web', 'dist', 'index.html');
  if (
    !(await stat(python).catch(() => null))?.isFile() ||
    !(await stat(web).catch(() => null))?.isFile()
  )
    return { status: 'user_action_required', code: 'source_setup_required' };
  return {
    status: 'user_action_required',
    code: 'source_start_required',
    prepared: true,
    sourceRoot: root,
    action:
      'Check that no server for this source tree is running, then explicitly start its prepared Python server; use the source setup reference. This helper will not create a second server.',
  };
}
/** @param {string[]} candidates */
async function applicationPaths(candidates) {
  const apps = new Set();
  for (const candidate of candidates) {
    const file = await realpath(checkedPath(candidate)).catch(() => '');
    if (file) checkedPath(file);
    if (
      path.basename(file).toLowerCase() === 'ttsnative.exe' &&
      (await stat(file).catch(() => null))?.isFile()
    )
      apps.add(file);
  }

  return [...apps];
}
/** @param {string[]} args @param {{platform?:NodeJS.Platform,query?:()=>string[],start?:typeof spawn}} [hooks] @returns {Promise<Record<string,unknown>>} */
export async function main(args, hooks = {}) {
  try {
    const platform = hooks.platform || process.platform;
    const { values } = parseArgs({
      args,
      options: {
        app: { type: 'string' },
        'source-root': { type: 'string' },
        'detect-only': { type: 'boolean' },
      },
    });
    if (values.app && values['source-root'])
      return { status: 'error', code: 'choose_one_installation' };
    if (values['source-root']) return await prepared(values['source-root'], platform);
    if (platform !== 'win32' && !values.app)
      return { status: 'unsupported', code: 'windows_detection_only' };
    const candidates = values.app ? [values.app] : (hooks.query || windowsApplications)();
    const apps = await applicationPaths(candidates);
    if (!apps.length)
      return { status: 'user_action_required', code: 'installation_required', installed: false };
    if (apps.length > 1)
      return {
        status: 'user_action_required',
        code: 'ambiguous_installation',
        installations: apps,
      };
    if (values['detect-only'])
      return { status: 'success', code: 'installed', installed: true, application: apps[0] };
    const child = (hooks.start || spawn)(apps[0], [], {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
    return await new Promise((resolve) => {
      child.once('error', () =>
        resolve({ status: 'user_action_required', code: 'app_launch_required' }),
      );
      child.once('spawn', () => {
        child.unref();
        resolve({ status: 'success', code: 'app_started', integrationVerified: false });
      });
    });
  } catch {
    return { status: 'user_action_required', code: 'installation_detection_unavailable' };
  }
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  void main(process.argv.slice(2)).then((result) => {
    process.stdout.write(JSON.stringify(result) + '\n');
    process.exitCode = result.status === 'error' ? 1 : 0;
  });
}

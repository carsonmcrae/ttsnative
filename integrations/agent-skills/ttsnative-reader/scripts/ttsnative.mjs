// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Local TTSNative client for Node 22.
 * Scope: Authenticated discovery, reading and verified exports.
 * Does NOT belong: Installation or synthesis.
 */
import { promises as fs, createWriteStream } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import net from 'node:net';
import { randomBytes } from 'node:crypto';
import { spawn } from 'node:child_process';
import { pipeline } from 'node:stream/promises';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
/** @typedef {{protocolVersion:number,instanceId:string,pid:number,origin:string,uiUrl:string,kind:string,token:string,launcher?:string,sourceRoot?:string}} D */
/** @typedef {{protocolVersion:number,instanceId:string,version:string,uiUrl:string,maxUploadBytes:number,ffmpegAvailable:boolean,formats:string[],engines:object[]}} S */
/** @typedef {{id:string,available:boolean}} V */
/** @typedef {ReturnType<typeof argumentsFor>} Args */
/** @typedef {{id:string,status:string,progress:number}} J */
/** @typedef {{job:J,format:string}} E */
/** @typedef {(file:string,args:string[])=>Promise<boolean>} L */
/** @typedef {{launch:L,sleep:(ms:number)=>Promise<void>,progress:(value:object)=>void}} H */
const ID = /^[0-9a-f]{32}$/;
const FORMATS = ['pdf', 'epub', 'docx', 'md', 'markdown', 'txt'];
const AUDIO = ['mp3', 'wav', 'm4b'];
const BASE = '/api/agent/v1';
const ACTION = 'user_action_required',
  BAD = 'invalid_response',
  ARGS = 'invalid_arguments';
export class ClientError extends Error {
  /** @param {string} code @param {string} [status] */
  constructor(code, status = 'error') {
    super(code);
    this.code = code;
    this.status = status;
  }
}
/** @param {string} code @param {string} [status] @returns {never} */
function fail(code, status) {
  throw new ClientError(code, status);
}
/** @param {string} code @param {Record<string,unknown>} [extra] */
const success = (code, extra = {}) => ({ status: 'success', code, ...extra });
/** @param {string} code @param {Record<string,unknown>} [extra] */
const needsUser = (code, extra = {}) => ({ status: ACTION, code, ...extra });
/** @param {string} value */
export function localPath(value) {
  if (
    !value ||
    [...value].some((c) => c.charCodeAt(0) < 32) ||
    /^[\\/]{2}|^[a-z]+:\/\//i.test(value)
  )
    fail('invalid_local_path');
  return path.resolve(value);
}
/** @param {string} value @param {boolean} [ui] */
export function loopback(value, ui = false) {
  let url;
  try {
    url = new URL(value);
  } catch {
    return fail('invalid_instance');
  }
  const host = url.hostname.replace(/^\[|\]$/g, '');
  const ipv4 = net.isIP(host) === 4 && host.startsWith('127.');
  if (
    url.protocol !== 'http:' ||
    !(ipv4 || host === '::1' || (ui && host === 'localhost')) ||
    [url.username, url.password, url.search, url.hash].some(Boolean) ||
    url.pathname !== '/'
  )
    fail('invalid_instance');
  return url.origin;
}
/** @param {NodeJS.ProcessEnv} [env] @param {NodeJS.Platform} [platform] */
export function discoveryRoot(env = process.env, platform = process.platform) {
  return platform === 'win32'
    ? path.join(
        env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'),
        'com.ttsnative.desktop',
        'agent',
      )
    : path.join(
        env.XDG_STATE_HOME || path.join(os.homedir(), '.local', 'state'),
        'ttsnative',
        'agent',
      );
}
/** @param {string} file */
export async function descriptor(file) {
  const stat = await fs.lstat(file);
  const parent = await fs.stat(path.dirname(file));
  if (
    !stat.isFile() ||
    stat.size > 16_384 ||
    (process.platform !== 'win32' && (parent.mode & 0o077 || parent.uid !== process.getuid?.()))
  )
    fail('insecure_descriptor');
  const d = /** @type {D} */ (JSON.parse(await fs.readFile(file, 'utf8')));
  if (
    d.protocolVersion !== 1 ||
    !ID.test(d.instanceId) ||
    !Number.isInteger(d.pid) ||
    d.pid < 1 ||
    typeof d.token !== 'string' ||
    !/^[0-9a-f]{64}$/.test(d.token) ||
    !['desktop', 'source'].includes(d.kind)
  )
    fail('invalid_instance');
  d.origin = loopback(d.origin);
  d.uiUrl = loopback(d.uiUrl, true);
  return d;
}
/** @param {D} d @param {string} route @param {string} [method] @param {object|Buffer} [body] */
export async function request(d, route, method = 'GET', body) {
  const bytes = body && (Buffer.isBuffer(body) ? body : Buffer.from(JSON.stringify(body)));
  const res = await new Promise(
    /** @param {(value:import('node:http').IncomingMessage)=>void} resolve */ (resolve, reject) => {
      const req = http.request(
        new URL(BASE + route, d.origin),
        {
          method,
          agent: false,
          headers: {
            Authorization: `Bearer ${d.token}`,
            'X-LTTS-Client': 'agent-skill',
            'Content-Length': bytes ? bytes.length : 0,
            'Content-Type': Buffer.isBuffer(body) ? 'application/octet-stream' : 'application/json',
          },
        },
        resolve,
      );
      req.setTimeout(30_000, () => req.destroy(new ClientError('request_timeout')));
      req.on('error', () => reject(new ClientError('connection_failed')));
      req.end(bytes);
    },
  );
  const status = Number(res.statusCode);
  if (Math.floor(status / 100) === 2) return res;
  if (status < 400) {
    res.resume();
    fail('redirect_refused');
  }
  const payload = /** @type {{error?:{code?:unknown}}} */ (
    await readJson(res, 32768).catch(() => ({}))
  );
  const candidate = payload?.error?.code;
  let code =
    typeof candidate === 'string' && /^[a-z][a-z0-9_]{0,63}$/.test(candidate)
      ? candidate
      : 'server_request_failed';
  if (status === 401) code = 'authentication_failed';
  if (status === 404 && ['http_error', 'server_request_failed'].includes(code))
    fail('integration_unavailable', 'unsupported');
  const unsupported = /^(no_text|unsupported_document|unsupported_format)$/.test(code);
  const action =
    /^(engine_(not_installed|unavailable)|model_missing|ffmpeg_missing|insufficient_disk_space|export_queue_full)$/.test(
      code,
    );
  fail(code, unsupported ? 'unsupported' : action ? ACTION : 'error');
}
/** @template T @param {import('node:http').IncomingMessage} res @param {number} [limit] @returns {Promise<T>} */
async function readJson(res, limit = 2_000_000) {
  const parts = [];
  let size = 0;
  for await (const chunk of res) {
    size += chunk.length;
    if (size > limit) {
      res.destroy();
      fail(BAD);
    }
    parts.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(parts).toString('utf8'));
  } catch {
    return fail(BAD);
  }
}
/** @template T @param {D} d @param {string} route @param {string} [method] @param {object|Buffer} [body] @returns {Promise<T>} */
async function json(d, route, method, body) {
  return readJson(await request(d, route, method, body));
}
/** @param {string} root @param {string|undefined} instance @param {string|undefined} sourceRoot */
export async function discover(root, instance, sourceRoot) {
  /** @type {{descriptor:D,status:S}[]} */ const found = [];
  const entries = await fs.readdir(root, { withFileTypes: true }).catch(() => []);
  for (const entry of entries) {
    if (!entry.isDirectory() || !ID.test(entry.name) || (instance && instance !== entry.name))
      continue;
    try {
      const d = await descriptor(path.join(root, entry.name, 'instance.json'));
      if (
        d.instanceId !== entry.name ||
        (sourceRoot && (!d.sourceRoot || (await fs.realpath(d.sourceRoot)) !== sourceRoot))
      )
        continue;
      process.kill(d.pid, 0);
      const status = /** @type {S} */ (await json(d, '/status'));
      if (
        status.protocolVersion === 1 &&
        status.instanceId === d.instanceId &&
        loopback(status.uiUrl, true) === d.uiUrl
      )
        found.push({ descriptor: d, status });
    } catch {
      continue;
    }
  }
  if (found.length > 1) fail('ambiguous_instance', ACTION);
  return found[0];
}
/** @type {L} */
export function launch(file, args) {
  return new Promise((resolve) => {
    const child = spawn(file, args, { detached: true, stdio: 'ignore', windowsHide: true });
    child.unref();
    child.once('error', () => resolve(false));
    child.once('spawn', () => resolve(true));
  }).catch(() => false);
}
/** @param {Args} a */
async function connect(a) {
  const root = localPath(a.values['discovery-dir'] || discoveryRoot());
  const selected = a.values['source-root'];
  const source = selected ? await fs.realpath(localPath(selected)) : undefined;
  const found = await discover(root, a.values.instance, source);
  return found || fail('launch_required', ACTION);
}
/** @param {string[]} args */
export function argumentsFor(args) {
  const a = parseArgs({
    args,
    allowPositionals: true,
    options: {
      instance: { type: 'string' },
      'discovery-dir': { type: 'string' },
      'source-root': { type: 'string' },
      voice: { type: 'string' },
      pace: { type: 'string' },
      format: { type: 'string' },
      output: { type: 'string' },
      overwrite: { type: 'boolean' },
      'confirm-cancel': { type: 'boolean' },
      'wait-seconds': { type: 'string' },
    },
  });
  if (a.values.instance && !ID.test(a.values.instance)) fail('invalid_instance');
  const pace = Number(a.values.pace || 1),
    wait = Number(a.values['wait-seconds'] ?? (a.positionals[0] === 'export' ? 3600 : 15));
  if (![pace, wait].every(Number.isFinite) || pace < 0.5 || pace > 2 || wait < 0 || wait > 86_400)
    fail(ARGS);
  return { ...a, pace, wait };
}
/** @param {string|undefined} file */
export async function inputFile(file) {
  if (!file) fail('file_required');
  const resolved = await fs.realpath(localPath(file)).catch(() => fail('file_unavailable'));
  localPath(resolved);
  const stat = await fs.stat(resolved);
  if (!stat.isFile()) fail('file_unavailable');
  if (!FORMATS.includes(path.extname(resolved).slice(1).toLowerCase()))
    fail('unsupported_document', 'unsupported');
  if (!stat.size || stat.size > 128 * 1024 * 1024) fail('invalid_file_size');
  return { path: resolved, size: stat.size };
}
/** @param {D} d @param {string|undefined} wanted */
async function voice(d, wanted) {
  const voices = /** @type {V[]} */ (await json(d, '/voices'));
  if (!Array.isArray(voices)) fail(BAD);
  const selected = wanted ? voices.find((v) => v.id === wanted) : voices.find((v) => v.available);
  if (!selected) fail(wanted ? 'invalid_voice' : 'models_required', wanted ? 'error' : ACTION);
  if (!selected.available) fail('voice_unavailable', ACTION);
  return selected.id;
}
/** @param {D} d @param {string} ticket @param {H} hooks */
async function reader(d, ticket, hooks) {
  if (!/^[0-9a-f]{64}$/.test(ticket)) fail(BAD);
  if (
    d.kind === 'desktop' &&
    d.launcher &&
    path.isAbsolute(d.launcher) &&
    path.basename(d.launcher).toLowerCase() === 'ttsnative.exe'
  ) {
    if (await hooks.launch(localPath(d.launcher), [`--agent-read=${ticket}`])) return true;
  }
  const url = `${loopback(d.uiUrl, true)}/agent-read#${ticket}`;
  if (process.platform === 'win32')
    return hooks.launch(
      path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'rundll32.exe'),
      ['url.dll,FileProtocolHandler', url],
    );
  return hooks.launch(process.platform === 'darwin' ? '/usr/bin/open' : '/usr/bin/xdg-open', [url]);
}
/** @param {string|undefined} output @param {boolean} overwrite @param {string} format */
async function outputPath(output, overwrite, format) {
  if (!output) fail('output_required');
  const target = localPath(output);
  if (path.extname(target).toLowerCase() !== `.${format}`) fail('output_extension_mismatch');
  localPath(
    await fs.realpath(path.dirname(target)).catch(() => fail('output_directory_unavailable')),
  );
  if (!overwrite && (await fs.lstat(target).catch(() => null))) fail('output_exists', ACTION);
  return target;
}
/** @param {D} d @param {string} id @param {string} target @param {boolean} overwrite @param {string} format */
export async function download(d, id, target, overwrite, format) {
  const temp = `${target}.part-${randomBytes(8).toString('hex')}`;
  let handle;
  try {
    const res = await request(d, `/exports/${encodeURIComponent(id)}/download`);
    await pipeline(res, createWriteStream(temp, { flags: 'wx' }));
    handle = await fs.open(temp, 'r');
    const size = (await handle.stat()).size,
      head = Buffer.alloc(16);
    await handle.read(head, 0, 16, 0);
    const valid =
      format === 'wav'
        ? head.toString('ascii', 0, 4) === 'RIFF' && head.toString('ascii', 8, 12) === 'WAVE'
        : format === 'm4b'
          ? head.toString('ascii', 4, 8) === 'ftyp'
          : head.toString('ascii', 0, 3) === 'ID3' ||
            (head[0] === 255 && ((head[1] || 0) & 224) === 224);
    const length = Number(res.headers['content-length'] || size);
    if (size < 16 || size !== length || !valid) fail('invalid_audio');
    await handle.close();
    handle = undefined;
    if (overwrite) await fs.rename(temp, target);
    else await fs.copyFile(temp, target, fs.constants.COPYFILE_EXCL);
    return size;
  } finally {
    await handle?.close();
    await fs.unlink(temp).catch(() => {});
  }
}
/** @param {E} item */
function jobSummary(item) {
  const { id: jobId, status: jobStatus, progress } = item.job;
  return { jobId, jobStatus, progress };
}
/** @param {Args} a @param {D} d @param {H} hooks */
async function jobCommand(a, d, hooks) {
  const action = a.positionals[1],
    id = a.positionals[2];
  if (
    !id ||
    !ID.test(id) ||
    !['status', 'pause', 'resume', 'cancel', 'download'].includes(action || '')
  )
    fail(ARGS);
  if (['pause', 'resume', 'cancel'].includes(action || '')) {
    const job = /** @type {J} */ (await json(d, `/exports/${id}/${action}`, 'POST', {}));
    return success('job_updated', jobSummary({ job, format: '' }));
  }
  const item = /** @type {E} */ (await json(d, `/exports/${id}`));
  if (action === 'status') return success('job_status', jobSummary(item));
  if (!AUDIO.includes(item.format)) fail('unsupported_export', 'unsupported');
  const target = await outputPath(a.values.output, !!a.values.overwrite, item.format);
  if (item.job.status !== 'succeeded') return needsUser('export_not_ready', jobSummary(item));
  const bytes = await download(d, id, target, !!a.values.overwrite, item.format);
  hooks.progress({ jobId: id, progress: 1 });
  return success('export_downloaded', { output: target, bytes, ...jobSummary(item) });
}
/** @param {Args} a @param {D} d @param {string} id @param {string} target @param {string} format @param {H} hooks */
async function waitExport(a, d, id, target, format, hooks) {
  const deadline = Date.now() + a.wait * 1000;
  let previous = -1;
  for (;;) {
    const item = /** @type {E} */ (await json(d, `/exports/${id}`));
    if (previous !== item.job.progress) {
      previous = item.job.progress;
      hooks.progress({ jobId: id, progress: previous });
    }
    if (item.job.status === 'succeeded')
      return {
        status: 'success',
        code: 'export_completed',
        jobId: id,
        output: target,
        bytes: await download(d, id, target, !!a.values.overwrite, format),
      };
    if (['failed', 'canceled', 'paused', 'interrupted'].includes(item.job.status))
      return needsUser('export_stopped', jobSummary(item));
    if (Date.now() >= deadline) return needsUser('export_running', jobSummary(item));
    await hooks.sleep(500);
  }
}
/** @param {Args} a @param {D} d @param {string} id @param {H} hooks */
async function waitReader(a, d, id, hooks) {
  const deadline = Date.now() + a.wait * 1000;
  for (;;) {
    const result = /** @type {{status:string}} */ (await json(d, `/read-requests/${id}`));
    if (result.status === 'playing') return success('playback_started');
    if (a.positionals[0] === 'open' && result.status === 'opened') return success('reader_opened');
    if (result.status === 'failed') fail('playback_failed');
    if (result.status === ACTION || Date.now() >= deadline)
      return needsUser('press_play_in_reader');
    await hooks.sleep(250);
  }
}
/** @param {Args} a @param {D} d @param {S} status @param {Awaited<ReturnType<typeof inputFile>>} file @param {H} hooks */
async function documentCommand(a, d, status, file, hooks) {
  const command = a.positionals[0],
    voiceId = await voice(d, a.values.voice);
  if (file.size > status.maxUploadBytes) fail('upload_too_large');
  const format = a.values.format || 'mp3';
  if (command === 'export' && (!AUDIO.includes(format) || !status.formats.includes(format)))
    fail('unsupported_export', 'unsupported');
  if (command === 'export' && format === 'm4b' && !status.ffmpegAvailable)
    fail('ffmpeg_required', ACTION);
  const target =
    command === 'export' ? await outputPath(a.values.output, !!a.values.overwrite, format) : '';
  /** @type {{id:string}} */ const document = await json(
    d,
    `/documents/upload?filename=${encodeURIComponent(path.basename(file.path))}`,
    'POST',
    await fs.readFile(file.path),
  );
  if (!ID.test(document.id)) fail(BAD);
  if (command === 'export') {
    /** @type {J} */ const started = await json(d, '/exports', 'POST', {
      documentId: document.id,
      voiceId,
      pace: a.pace,
      format,
      layout: 'single',
    });
    if (!ID.test(started.id)) fail(BAD);
    return {
      documentId: document.id,
      ...(await waitExport(a, d, started.id, target, format, hooks)),
    };
  }
  /** @type {{requestId:string,ticket:string}} */ const opened = await json(
    d,
    '/read-requests',
    'POST',
    {
      documentId: document.id,
      voiceId,
      pace: a.pace,
      autoplay: command === 'read',
    },
  );
  if (!ID.test(opened.requestId)) fail(BAD);
  const result = (await reader(d, opened.ticket, hooks))
    ? await waitReader(a, d, opened.requestId, hooks)
    : needsUser('open_reader');
  return { ...result, documentId: document.id, requestId: opened.requestId };
}
/** @param {string[]} args @param {Partial<H>} [overrides] */
export async function main(args, overrides = {}) {
  const hooks = {
    launch,
    sleep: (/** @type {number} */ ms) => new Promise((resolve) => setTimeout(resolve, ms)),
    progress: (/** @type {object} */ event) => process.stderr.write(JSON.stringify(event) + '\n'),
    ...overrides,
  };
  try {
    const a = argumentsFor(args),
      command = a.positionals[0] || '';
    if (!['status', 'voices', 'open', 'read', 'export', 'job'].includes(command)) fail(ARGS);
    const file = ['open', 'read', 'export'].includes(command)
      ? await inputFile(a.positionals[1])
      : undefined;
    if (command === 'job' && a.positionals[1] === 'cancel' && !a.values['confirm-cancel'])
      fail('cancel_confirmation_required', ACTION);
    const { descriptor: d, status } = await connect(a);
    if (command === 'status')
      return success('ready', {
        instanceId: d.instanceId,
        version: status.version,
        kind: d.kind,
        formats: status.formats,
        ffmpegAvailable: status.ffmpegAvailable,
        engines: status.engines,
      });
    if (command === 'voices') return success('voices', { voices: await json(d, '/voices') });
    if (command === 'job') return await jobCommand(a, d, hooks);
    if (file) return await documentCommand(a, d, status, file, hooks);
    return fail(ARGS);
  } catch (error) {
    if (error instanceof ClientError) return { status: error.status, code: error.code };
    return { status: 'error', code: 'operation_failed' };
  }
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  const result = await main(process.argv.slice(2));
  process.stdout.write(JSON.stringify(result) + '\n');
  process.exitCode = result.status === 'error' ? 1 : 0;
}

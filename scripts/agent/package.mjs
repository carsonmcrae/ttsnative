// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Build and validate the one-skill, text-only TTSNative distribution ZIP.
 * Scope: An explicit file allowlist, simple string YAML metadata, deterministic stored ZIP records
 *   with CRC-32, and validation of every directory/header/content against the canonical files.
 * Does NOT belong: Uploading a listing, installing dependencies or running TTSNative.
 */
import { readFileSync, readdirSync, lstatSync, mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { crc32 } from 'node:zlib';
import { createHash } from 'node:crypto';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
import { repoRoot } from '../lib/paths.mjs';

export const FILES = [
  'SKILL.md',
  'LICENSE',
  'references/setup.md',
  'references/commands.md',
  'scripts/ttsnative.mjs',
  'scripts/launch.mjs',
];
export const SKILL = path.join(repoRoot, 'integrations', 'agent-skills', 'ttsnative-reader');
const utf8 = new TextDecoder('utf-8', { fatal: true });
/** @param {unknown} condition @param {string} reason @returns {asserts condition} */
function requireThat(condition, reason) {
  if (!condition) throw new Error(reason);
}

/** Parse only the skill's deliberately small YAML string/mapping subset, failing on other syntax.
 * @param {string} markdown @param {string} directory */
export function metadata(markdown, directory) {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  requireThat(lines[0] === '---', 'SKILL.md needs YAML frontmatter');
  const end = lines.indexOf('---', 1);
  requireThat(end > 1, 'Unclosed frontmatter');
  /** @type {Record<string,string>} */ const fields = Object.create(null);
  const keys = new Set();
  let inMetadata = false;
  for (const line of lines.slice(1, end)) {
    if (!line.trim()) continue;
    if (line === 'metadata:') {
      requireThat(!keys.has('metadata'), 'Duplicate metadata');
      keys.add('metadata');
      inMetadata = true;
      continue;
    }
    const match = /^( {2})?([a-z][a-z0-9_-]*):\s+(.+)$/.exec(line);
    requireThat(match && (!match[1] || inMetadata), 'Use simple YAML string fields');
    const nested = !!match[1],
      key = `${nested ? 'metadata.' : ''}${match[2]}`;
    requireThat(!keys.has(key), 'Duplicate frontmatter key');
    keys.add(key);
    if (!nested) inMetadata = false;
    const raw = match[3] || '';
    const value = scalar(raw);
    if (!nested) {
      requireThat(
        ['name', 'description', 'license', 'compatibility'].includes(match[2] || ''),
        'Unsupported frontmatter field',
      );
      fields[match[2] || ''] = value;
    }
  }
  checkMetadata(fields, directory, lines.slice(end + 1).join('\n'));
  return fields;
}

/** @param {Record<string,string>} fields @param {string} directory @param {string} body */
function checkMetadata(fields, directory, body) {
  requireThat(
    fields.name === directory &&
      /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(fields.name) &&
      fields.name.length <= 64,
    'Skill name must match its directory',
  );
  requireThat(
    fields.description && fields.description.length <= 1024,
    'Description required, at most 1024 characters',
  );
  requireThat(
    !fields.compatibility || fields.compatibility.length <= 500,
    'Compatibility exceeds 500 characters',
  );
  requireThat(body.trim(), 'Skill instructions required');
}
/** @param {string} raw @returns {string} */
function scalar(raw) {
  if (raw.startsWith("'")) {
    requireThat(raw.endsWith("'") && raw.length > 2, 'Invalid quoted YAML string');
    return raw.slice(1, -1).replaceAll("''", "'");
  }
  const value = raw.startsWith('"') ? JSON.parse(raw) : raw;
  requireThat(typeof value === 'string' && value.length > 0, 'YAML strings required');
  requireThat(!/^[>|[\]{}&*!#]/.test(raw) && !/(?:^|\s)#/.test(raw), 'Use simple YAML strings');
  requireThat(
    raw.startsWith('"') || !/^(?:true|false|null|~|[-+]?\d+(?:\.\d+)?)$/i.test(raw),
    'Quote non-string YAML values',
  );
  return value;
}
/** @param {string} root @param {string} [prefix] @returns {string[]} */
function paths(root, prefix = '') {
  return readdirSync(path.join(root, prefix), { withFileTypes: true }).flatMap((entry) => {
    const name = prefix ? `${prefix}/${entry.name}` : entry.name;
    const stat = lstatSync(path.join(root, name));
    requireThat(!stat.isSymbolicLink(), 'Skill symlinks are forbidden');
    return stat.isDirectory() ? paths(root, name) : [name];
  });
}
/** @param {string} root */
export function readSkill(root) {
  const names = paths(root).sort();
  requireThat(
    JSON.stringify(names) === JSON.stringify([...FILES].sort()),
    'Skill contents differ from the explicit allowlist',
  );
  const files = names.map((name) => ({
    name: `${path.basename(root)}/${name}`,
    data: readFileSync(path.join(root, name)),
  }));
  for (const file of files) {
    const text = utf8.decode(file.data);
    requireThat(!text.includes('\0'), 'Only UTF-8 text belongs in the skill');
    if (file.name.endsWith('.mjs')) {
      requireThat(file.data.length < 20_000, 'Every standalone script must be below 20 KB');
      requireThat(
        !/\bfrom\s*['"](?!node:)|\bimport\s*\(\s*['"](?!node:)/.test(text),
        'Scripts may import only Node standard libraries',
      );
    }
  }
  const info = metadata(
    utf8.decode(files.find((file) => file.name.endsWith('/SKILL.md'))?.data),
    path.basename(root),
  );
  requireThat(
    files.reduce((sum, file) => sum + file.data.length, 0) <= 500_000,
    'Skill text exceeds the local package limit',
  );
  return { files, info };
}

/** @param {{name:string,data:Buffer}[]} files */
export function zip(files) {
  const local = [],
    central = [];
  let offset = 0;
  for (const file of files) {
    const name = Buffer.from(file.name),
      checksum = crc32(file.data);
    const header = Buffer.alloc(30);
    header.writeUInt32LE(0x04034b50);
    header.writeUInt16LE(20, 4);
    header.writeUInt16LE(0x800, 6);
    header.writeUInt16LE(33, 12);
    header.writeUInt32LE(checksum, 14);
    header.writeUInt32LE(file.data.length, 18);
    header.writeUInt32LE(file.data.length, 22);
    header.writeUInt16LE(name.length, 26);
    local.push(header, name, file.data);
    const directory = Buffer.alloc(46);
    directory.writeUInt32LE(0x02014b50);
    directory.writeUInt16LE(0x0314, 4);
    header.copy(directory, 6, 4, 30);
    directory.writeUInt32LE((0o100644 * 65_536) >>> 0, 38);
    directory.writeUInt32LE(offset, 42);
    central.push(directory, name);
    offset += header.length + name.length + file.data.length;
  }
  const directory = Buffer.concat(central),
    end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50);
  end.writeUInt16LE(files.length, 8);
  end.writeUInt16LE(files.length, 10);
  end.writeUInt32LE(directory.length, 12);
  end.writeUInt32LE(offset, 16);
  return Buffer.concat([...local, directory, end]);
}
/** @param {Buffer} archive @param {{name:string,data:Buffer}[]} expected */
export function validateZip(archive, expected) {
  requireThat(archive.length >= 22 && archive.length <= 600_000, 'Invalid ZIP size');
  const end = archive.length - 22;
  requireThat(archive.readUInt32LE(end) === 0x06054b50, 'Invalid ZIP end');
  requireThat(
    archive.readUInt32LE(end + 4) === 0 && archive.readUInt16LE(end + 20) === 0,
    'ZIP must be single-volume without comments',
  );
  const count = archive.readUInt16LE(end + 10),
    start = archive.readUInt32LE(end + 16);
  requireThat(
    count === expected.length && archive.readUInt16LE(end + 8) === count,
    'Unexpected ZIP entry count',
  );
  requireThat(start + archive.readUInt32LE(end + 12) === end, 'Invalid ZIP directory bounds');
  let cursor = start,
    local = 0;
  for (const file of expected) {
    requireThat(
      cursor + 46 <= end && archive.readUInt32LE(cursor) === 0x02014b50,
      'Invalid ZIP directory entry',
    );
    const length = archive.readUInt16LE(cursor + 28),
      extra = archive.readUInt16LE(cursor + 30),
      comment = archive.readUInt16LE(cursor + 32);
    const name = archive.subarray(cursor + 46, cursor + 46 + length);
    requireThat(
      utf8.decode(name) === file.name && !extra && !comment,
      'Unexpected ZIP path or metadata',
    );
    requireThat(
      archive.readUInt32LE(cursor + 42) === local && archive.readUInt16LE(cursor + 10) === 0,
      'ZIP offsets/method differ',
    );
    requireThat(
      archive.readUInt16LE(cursor + 8) === 0x800 &&
        archive.readUInt32LE(cursor + 38) === (0o100644 * 65_536) >>> 0,
      'ZIP flags or file mode differ',
    );
    const size = archive.readUInt32LE(cursor + 24);
    const data = checkedLocal(archive, local, start, name, size);
    requireThat(
      size === file.data.length &&
        data.equals(file.data) &&
        archive.readUInt32LE(cursor + 20) === size,
      'ZIP content differs',
    );
    requireThat(archive.readUInt32LE(cursor + 16) === crc32(data), 'ZIP checksum differs');
    local += 30 + length + size;
    cursor += 46 + length;
  }
  requireThat(cursor === end && local === start, 'ZIP has trailing or unreferenced bytes');
}
/** @param {Buffer} archive @param {number} local @param {number} start @param {Buffer} name @param {number} size */
function checkedLocal(archive, local, start, name, size) {
  requireThat(
    local + 30 <= start && archive.readUInt32LE(local) === 0x04034b50,
    'Invalid ZIP local header',
  );
  requireThat(
    archive.readUInt16LE(local + 26) === name.length && archive.readUInt16LE(local + 28) === 0,
    'Invalid ZIP local name',
  );
  requireThat(
    archive.subarray(local + 30, local + 30 + name.length).equals(name),
    'ZIP names disagree',
  );
  const data = archive.subarray(local + 30 + name.length, local + 30 + name.length + size);
  requireThat(archive.readUInt32LE(local + 14) === crc32(data), 'ZIP checksum differs');
  requireThat(
    archive.readUInt32LE(local + 18) === size &&
      archive.readUInt32LE(local + 22) === size &&
      archive.readUInt16LE(local + 8) === 0 &&
      archive.readUInt16LE(local + 6) === 0x800,
    'ZIP local sizes/flags differ',
  );
  return data;
}
/** @param {string[]} args */
export function main(args) {
  const { values } = parseArgs({
    args,
    options: { out: { type: 'string' }, check: { type: 'string' } },
  });
  const { files, info } = readSkill(SKILL);
  const output = path.resolve(
    values.check || values.out || path.join(repoRoot, '.tools', 'agent', 'ttsnative-reader.zip'),
  );
  const archive = values.check ? readFileSync(output) : zip(files);
  validateZip(archive, files);
  if (!values.check) {
    mkdirSync(path.dirname(output), { recursive: true });
    writeFileSync(output, archive);
  }
  return {
    name: info.name,
    output,
    entries: files.map((file) => file.name),
    bytes: archive.length,
    sha256: createHash('sha256').update(archive).digest('hex'),
  };
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  try {
    console.log(JSON.stringify(main(process.argv.slice(2))));
  } catch (error) {
    console.error(error instanceof Error ? error.message : 'Package validation failed');
    process.exitCode = 1;
  }
}

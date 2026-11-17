// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Verify deterministic one-skill ZIP production and rejection of unsafe packages.
 * Scope: Real canonical files, metadata, CRCs, paths, text-only allowlists and isolated fixtures.
 * Does NOT belong: Marketplace uploads or application runtime testing.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import { metadata, readSkill, zip, validateZip, main, SKILL, FILES } from './package.mjs';
import { workspace } from './test-workspace.mjs';

const valid =
  '---\nname: ttsnative-reader\ndescription: Read local documents aloud.\nlicense: MIT\nmetadata:\n  version: "1.0.0"\n---\nRead only when instructed.\n';

/** @param {import('node:test').TestContext} t */
async function skillCopy(t) {
  const root = await workspace(t, 'ttsnative-package-'),
    skill = path.join(root, 'ttsnative-reader');
  await fs.cp(SKILL, skill, { recursive: true });
  return { root, skill };
}

test('canonical package is deterministic with exactly one skill and independently named text files', () => {
  const { files, info } = readSkill(SKILL),
    first = zip(files),
    second = zip(readSkill(SKILL).files);
  assert.equal(info.name, 'ttsnative-reader');
  assert.equal(files.length, 6);
  assert.equal(files.filter((f) => f.name.endsWith('/SKILL.md')).length, 1);
  assert.deepEqual(
    files.map((f) => f.name),
    [...FILES].sort().map((name) => 'ttsnative-reader/' + name),
  );
  assert(first.equals(second));
  validateZip(first, files);
});

test('builder output and check mode agree without changing an existing archive', async (t) => {
  const { root } = await skillCopy(t),
    out = path.join(root, 'review.zip');
  const built = main(['--out', out]),
    checked = main(['--check', out]);
  assert.equal(built.sha256, checked.sha256);
  assert.equal(built.bytes, (await fs.stat(out)).size);
  const original = await fs.readFile(out);
  main(['--check', out]);
  assert(original.equals(await fs.readFile(out)));
});

test('metadata is a strict supported YAML subset with bounded required strings', () => {
  assert.equal(metadata(valid, 'ttsnative-reader').description, 'Read local documents aloud.');
  assert.equal(
    metadata(valid.replace('"1.0.0"', "'1.0.0'"), 'ttsnative-reader').name,
    'ttsnative-reader',
  );
  for (const bad of [
    valid.replace('name: ttsnative-reader', 'name: other'),
    valid.replace('description: Read local documents aloud.', 'description: true'),
    valid.replace('description: Read local documents aloud.', 'description: ' + 'x'.repeat(1025)),
    valid.replace('license: MIT', 'license: MIT\nunknown: x'),
    valid.replace('license: MIT', 'name: ttsnative-reader'),
    valid.replace('metadata:', 'metadata:\nmetadata:'),
    valid.replace('description: Read local documents aloud.', 'description: |\n  hidden'),
    valid.slice(4),
    valid.replace('Read only when instructed.', ''),
  ])
    assert.throws(() => metadata(bad, 'ttsnative-reader'));
});

test('allowlist rejects additional skills, media and nested dependency files', async (t) => {
  const { skill } = await skillCopy(t);
  for (const name of ['other/SKILL.md', 'recording.wav', 'scripts/node_modules/pkg/index.js']) {
    const file = path.join(skill, name);
    await fs.mkdir(path.dirname(file), { recursive: true });
    await fs.writeFile(file, 'synthetic');
    assert.throws(() => readSkill(skill), /allowlist/);
    await fs.unlink(file);
  }
});

test('all scripts must fit the standalone size/import boundary and all files must be text', async (t) => {
  const { skill } = await skillCopy(t),
    client = path.join(skill, 'scripts/ttsnative.mjs');
  for (const content of [
    Buffer.alloc(20_000, 32),
    Buffer.from("import value from './sibling.mjs';"),
    Buffer.from("await import('third-party');"),
    Buffer.from([0xff]),
    Buffer.from('binary\0text'),
  ]) {
    await fs.writeFile(client, content);
    assert.throws(() => readSkill(skill));
  }
});

test('ZIP validation rejects corrupt data, CRCs, names, executable modes and structural ambiguity', () => {
  const { files } = readSkill(SKILL),
    archive = zip(files),
    end = archive.length - 22,
    central = archive.readUInt32LE(end + 16),
    data = 30 + archive.readUInt16LE(26);
  const mutations = [
    [data, archive.readUInt8(data) ^ 1],
    [14, archive.readUInt8(14) ^ 1],
    [30, '.'.charCodeAt(0)],
    [central + 46, '.'.charCodeAt(0)],
    [central + 38, archive.readUInt8(central + 38) ^ 1],
    [central + 10, 8],
    [end + 8, 0],
    [end + 20, 1],
  ];
  for (const [offset, value] of mutations) {
    assert(offset !== undefined && value !== undefined);
    const bad = Buffer.from(archive);
    bad[offset] = value;
    assert.throws(() => validateZip(bad, files));
  }
  assert.throws(() => validateZip(Buffer.concat([archive, Buffer.from('extra')]), files));
  assert.throws(() => validateZip(archive.subarray(0, 20), files));
  assert.throws(() => validateZip(archive, [...files].reverse()));
});

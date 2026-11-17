// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Give standalone-helper tests an owned temporary directory with checked cleanup.
 * Scope: Test fixtures only, never application data or the user's installation.
 * Does NOT belong: Production client or portable ZIP contents.
 */
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';

/** @param {import('node:test').TestContext} t @param {string} prefix */
export async function workspace(t, prefix) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), prefix));
  t.after(async () => {
    assert.equal(path.dirname(root), path.resolve(os.tmpdir()));
    await fs.rm(root, { recursive: true, force: true });
  });
  return root;
}

// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Tests for finding and clearing a PE file's certificate-table entry that points past the
 *   end of the file.
 * Scope: PE32+ and PE32 headers (lib/pe-fixture.mjs): a file with no signature, one whose signature
 *   lies inside it (left alone), one whose entry points past its end or straddles it (cleared, and
 *   nothing else changed), headers with too few directory entries, and files that aren't PE.
 * Does NOT belong: Walking a package's files (scripts/desktop/msix.test.mjs).
 */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  certificateTable,
  clearDanglingCertificateTable,
  hasDanglingCertificateTable,
} from './pe-certificates.mjs';
import { PE_LENGTH as LENGTH, peFile } from './pe-fixture.mjs';

for (const plus of [true, false]) {
  const kind = plus ? 'PE32+' : 'PE32';

  test(`${kind}: a file without a signature has nothing to clear`, () => {
    const { data, entry } = peFile({ plus });
    assert.deepEqual(certificateTable(data), { at: entry, offset: 0, size: 0 });
    assert.equal(hasDanglingCertificateTable(data), false);
    assert.equal(clearDanglingCertificateTable(data), false);
  });

  test(`${kind}: a signature inside the file is left alone`, () => {
    const { data } = peFile({ plus, offset: 0x600, size: 0x200 });
    const before = Buffer.from(data);
    assert.equal(hasDanglingCertificateTable(data), false);
    assert.equal(clearDanglingCertificateTable(data), false);
    assert.ok(data.equals(before));
  });

  test(`${kind}: an entry that points past the end is cleared and nothing else changes`, () => {
    for (const [offset, size] of [
      [LENGTH, 0x2f20], // a signature that was cut off the end, as in python-build-standalone's zlib1.dll
      [0x700, 0x200], // one that straddles the end
      [LENGTH * 4, 8],
    ]) {
      const { data, entry } = peFile({ plus, offset, size });
      const before = Buffer.from(data);
      assert.equal(hasDanglingCertificateTable(data), true);
      assert.equal(clearDanglingCertificateTable(data), true);
      assert.deepEqual(certificateTable(data), { at: entry, offset: 0, size: 0 });
      assert.equal(hasDanglingCertificateTable(data), false);
      const changed = [...data.keys()].filter((index) => data[index] !== before[index]);
      assert.ok(
        changed.length > 0 && changed.every((index) => index >= entry && index < entry + 8),
      );
    }
  });
}

test('a header with too few directory entries has no certificate table', () => {
  const { data } = peFile({ offset: LENGTH, size: 64, directoryCount: 4 });
  assert.equal(certificateTable(data), null);
  assert.equal(hasDanglingCertificateTable(data), false);
  assert.equal(clearDanglingCertificateTable(data), false);
});

test('files that are not PE are ignored', () => {
  for (const data of [
    Buffer.alloc(0),
    Buffer.from('not a program at all'),
    Buffer.concat([Buffer.from('MZ'), Buffer.alloc(200)]),
    Buffer.concat([Buffer.from('MZ'), Buffer.alloc(58), Buffer.from([0xff, 0xff, 0xff, 0x7f])]),
  ]) {
    assert.equal(certificateTable(data), null);
    assert.equal(hasDanglingCertificateTable(data), false);
    assert.equal(clearDanglingCertificateTable(data), false);
  }
});

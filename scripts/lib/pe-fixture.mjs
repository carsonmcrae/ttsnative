// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: A minimal Windows program header for tests that read or change certificate-table entries.
 * Scope: A buffer that starts like a PE file (PE32+ or PE32) with a data directory whose
 *   certificate-table entry is the one asked for; the rest is filler. Enough for
 *   lib/pe-certificates.mjs and the Store package's use of it, not a program Windows would run.
 * Does NOT belong: Import tables (pe-imports.test.mjs builds its own) or production code.
 */

export const PE_LENGTH = 0x800;

/**
 * @param {{ offset?: number, size?: number, plus?: boolean, directoryCount?: number }} [options] the
 *   certificate table's file offset and size, PE32+ (the default) or PE32, and how many directory
 *   entries the header declares
 * @returns {{ data: Buffer, entry: number }} the file and where its certificate-table entry is
 */
export function peFile({ offset = 0, size = 0, plus = true, directoryCount = 16 } = {}) {
  const data = Buffer.alloc(PE_LENGTH, 0x11);
  data.fill(0, 0, 0x200);
  data.write('MZ', 0, 'latin1');
  const pe = 0x40;
  data.writeUInt32LE(pe, 0x3c);
  data.write('PE\0\0', pe, 'latin1');
  const optional = pe + 24;
  data.writeUInt16LE(plus ? 0x20b : 0x10b, optional);
  data.writeUInt32LE(directoryCount, optional + (plus ? 108 : 92));
  const entry = optional + (plus ? 112 : 96) + 4 * 8;
  data.writeUInt32LE(offset, entry);
  data.writeUInt32LE(size, entry + 4);
  return { data, entry };
}

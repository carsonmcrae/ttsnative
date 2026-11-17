// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Find and clear a Windows program's or library's certificate-table entry when it points
 *   past the end of the file.
 * Scope: The security entry of a PE file's data directory (PE32 and PE32+): where the file says its
 *   Authenticode signature is. A file whose signature was removed without clearing that entry still
 *   claims one beyond its last byte. Windows loads such a file, but the Microsoft Store can't sign a
 *   package that holds one (its ingestion fails with 0x800700C1, "not a valid Win32 application"), so
 *   the entry is set to zero: the file then says, truthfully, that it carries no signature. Nothing
 *   else in the file changes, and a table that lies inside the file is never touched.
 * Does NOT belong: Walking folders or deciding which files to check (scripts/desktop/signatures.mjs).
 */

const SECURITY_ENTRY = 4;

/**
 * Where a PE file's certificate-table entry is and what it says, or null when it isn't a PE file or
 * has no such entry.
 * @param {Buffer} data
 * @returns {{ at: number, offset: number, size: number } | null}
 */
export function certificateTable(data) {
  if (data.length < 64 || data.readUInt16LE(0) !== 0x5a4d) return null;
  const pe = data.readUInt32LE(0x3c);
  if (pe + 24 > data.length || data.readUInt32LE(pe) !== 0x4550) return null;
  const optional = pe + 24;
  if (optional + 2 > data.length) return null;
  const plus = data.readUInt16LE(optional) === 0x20b;
  const count = optional + (plus ? 108 : 92);
  const at = optional + (plus ? 112 : 96) + SECURITY_ENTRY * 8;
  if (at + 8 > data.length || data.readUInt32LE(count) <= SECURITY_ENTRY) return null;
  return { at, offset: data.readUInt32LE(at), size: data.readUInt32LE(at + 4) };
}

/**
 * True when the file claims a certificate table that isn't wholly inside it.
 * @param {Buffer} data
 */
export function hasDanglingCertificateTable(data) {
  const table = certificateTable(data);
  if (!table || (table.offset === 0 && table.size === 0)) return false;
  return table.offset + table.size > data.length;
}

/**
 * Sets a dangling certificate-table entry to zero, in place. Returns whether the data changed.
 * @param {Buffer} data
 */
export function clearDanglingCertificateTable(data) {
  if (!hasDanglingCertificateTable(data)) return false;
  const table = /** @type {{ at: number }} */ (certificateTable(data));
  data.writeUInt32LE(0, table.at);
  data.writeUInt32LE(0, table.at + 4);
  return true;
}

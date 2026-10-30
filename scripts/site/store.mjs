// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Whether ttsnative.com offers TTSNative's Microsoft Store listing, and where it is.
 * Scope: Reads the identity in apps/desktop/store/identity.json: the listing is offered only once
 *   `listed` is true (set when Partner Center shows the app as live) and a Store ID is recorded. Pages
 *   then show their `<!-- if:store -->` blocks with %STORE_URL% filled in; otherwise their
 *   `<!-- if:no-store -->` blocks.
 * Does NOT belong: Packaging (scripts/desktop/msix.mjs) or the GitHub release lookup (releases.mjs).
 */
import { applyConditions } from './releases.mjs';

/**
 * @param {{ storeId?: string, listed?: boolean }} identity
 * @returns {{ id: string, url: string } | null}
 */
export function storeListing(identity) {
  const id = identity.storeId?.trim() ?? '';
  if (identity.listed !== true || !/^[0-9A-Z]{12}$/.test(id)) return null;
  return { id, url: `https://apps.microsoft.com/detail/${id}` };
}

/**
 * @param {string} html
 * @param {{ url: string } | null} listing
 */
export function fillStore(html, listing) {
  return applyConditions(html, { store: Boolean(listing), 'no-store': !listing }).replaceAll(
    '%STORE_URL%',
    listing?.url ?? '',
  );
}

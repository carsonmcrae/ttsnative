// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Tests for offering the Microsoft Store listing on the website.
 * Scope: The listing only once it is marked live and has a well-formed Store ID, and the store and
 *   no-store blocks with the listing's address.
 * Does NOT belong: The rest of the site build (releases.test.mjs).
 */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fillStore, storeListing } from './store.mjs';

test('the Store listing is offered only when it is live and its ID is a Store ID', () => {
  assert.deepEqual(storeListing({ storeId: '9PP3BKBDJP9R', listed: true }), {
    id: '9PP3BKBDJP9R',
    url: 'https://apps.microsoft.com/detail/9PP3BKBDJP9R',
  });
  assert.equal(storeListing({ storeId: '9PP3BKBDJP9R', listed: false }), null);
  assert.equal(storeListing({ storeId: '9PP3BKBDJP9R' }), null);
  assert.equal(storeListing({ storeId: '', listed: true }), null);
  assert.equal(storeListing({ listed: true }), null);
  assert.equal(storeListing({ storeId: '9pp3bkbdjp9r', listed: true }), null);
});

test('pages show the store blocks with the address, or the no-store blocks', () => {
  const html =
    '<!-- if:store --><a href="%STORE_URL%">Store</a><!-- /if:store --><!-- if:no-store -->Installer<!-- /if:no-store -->';
  assert.equal(
    fillStore(html, { url: 'https://apps.microsoft.com/detail/9PP3BKBDJP9R' }),
    '<a href="https://apps.microsoft.com/detail/9PP3BKBDJP9R">Store</a>',
  );
  assert.equal(fillStore(html, null), 'Installer');
});

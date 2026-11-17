// @ts-check
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Evaluate nested website conditional comments without exposing unpublished content.
 * Scope: Matches opening and closing markers with a stack, decides every nested flag, and preserves
 *   unknown wrappers for later passes. Malformed marker pairs fail the build instead of leaking text.
 * Does NOT belong: Choosing release, installer or Store flags, or rendering the rest of the website.
 */

/** @typedef {{ name: string, opening: string, parts: string[] }} Frame */

/**
 * @param {Frame} frame
 * @param {Frame[]} parents
 * @param {string} name
 * @param {string} closing
 * @param {(name: string) => boolean | undefined} decide
 */
function closeCondition(frame, parents, name, closing, decide) {
  const parent = parents.pop();
  if (!parent || frame.name !== name) {
    throw new Error(`Website conditional has an unmatched closing marker: /if:${name}`);
  }
  const body = frame.parts.join('');
  const keep = decide(name);
  if (keep === undefined) parent.parts.push(frame.opening, body, closing);
  else if (keep) parent.parts.push(body);
  return parent;
}

/**
 * Evaluate all nested markers in one pass, including children of an undecided wrapper. A false
 * parent discards its whole body; an unknown one keeps its original markers around the decided body.
 * @param {string} html
 * @param {(name: string) => boolean | undefined} decide
 */
export function renderConditions(html, decide) {
  /** @type {Frame} */
  const root = { name: '', opening: '', parts: [] };
  /** @type {Frame[]} */
  const parents = [];
  let current = root;
  let cursor = 0;
  const markers = / *<!-- if:([a-z0-9.-]+) -->|<!-- \/if:([a-z0-9.-]+) -->\n?/g;
  for (const marker of html.matchAll(markers)) {
    current.parts.push(html.slice(cursor, marker.index));
    if (marker[1]) {
      parents.push(current);
      current = { name: marker[1], opening: marker[0], parts: [] };
    } else current = closeCondition(current, parents, marker[2] ?? '', marker[0], decide);
    cursor = marker.index + marker[0].length;
  }
  if (parents.length) {
    throw new Error(`Website conditional is never closed: if:${current.name}`);
  }
  root.parts.push(html.slice(cursor));
  return root.parts.join('');
}

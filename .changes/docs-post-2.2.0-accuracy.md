---
bump: none
desktop: unchanged
browser: unchanged
phone: unchanged
website: unchanged
docs: changed
---

## Technical

- README and wiki: the Windows installer is described as published (since 2.1.0, at ttsnative.com/download), not as coming. The README no longer names the newest version in its text; it points at the badge, which stays right on its own. The hand check of the interactive installer and SmartScreen is described as done before each major or minor release.
- `docs/guides/testing.md`, "What the coverage numbers mean": states the two `# pragma: no cover` comments and what the coverage settings exclude, the Chatterbox worker at about 930 lines, the Node scripts at about 9,600 lines, and the 16 `*.test.mjs` files that `npm run test:scripts` runs in CI. `docs/guides/windows-distribution.md` says which version its download check used.

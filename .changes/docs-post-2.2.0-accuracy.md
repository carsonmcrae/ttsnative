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
- `docs/releases/2.2.0.md`: `date` corrected from 2026-10-30, when the notes were prepared, to 2026-11-06, the UTC date GitHub published the release, with `revised: 2026-11-06`. The release history pages now match the home and download pages. Copies already installed and the published `latest.json` keep the old date, and the `[2.2.0]` heading in `CHANGELOG.md` still says 2026-10-30, because only a release pull request writes that file.

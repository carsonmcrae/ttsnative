---
bump: none
desktop: unchanged
browser: unchanged
phone: unchanged
website: unchanged
docs: unchanged
---

## Technical

- The release-readiness gate reads a wrapped acceptance check whole: its indented lines belong to it, so a "verified:" note on a later line counts (`scripts/lib/gate.mjs`, tested). Before, only an item's first line was read, so the wrapped checks in `docs/readiness/X.Y.Z/acceptance.md` could never pass.

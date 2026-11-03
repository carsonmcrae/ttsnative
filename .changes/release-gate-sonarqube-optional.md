---
bump: none
desktop: unchanged
browser: unchanged
phone: unchanged
website: unchanged
docs: changed
---

## Technical

- The release-readiness gate no longer requires a SonarQube result: the maintainer runs SonarQube when they choose. `qualityVerdict` is optional, so a missing, failed or out-of-date `docs/readiness/X.Y.Z/quality.json` is shown with `!` and never fails `npm run release:gate` or the Release workflow; `unmet()` counts only the required verdicts. A recorded result is still judged against the project's policy. The release process guide and the wiki say so.

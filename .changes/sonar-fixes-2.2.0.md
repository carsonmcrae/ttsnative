---
bump: none
desktop: unchanged
browser: unchanged
phone: unchanged
website: unchanged
docs: unchanged
---

## Technical

- SonarQube findings in code merged since the 2.2.0 quality review, fixed without changing behaviour: `scripts/desktop/cpp-runtime.mjs` and `scripts/lib/pe-imports.mjs` use `toSorted` instead of sorting in place inside an expression; the Visual C++ runtime pattern in `pe-imports.mjs` reads `\d\w*` (the same names) so it can't backtrack; `DeleteMyData` names its caught error `error_` like the rest of the web app.

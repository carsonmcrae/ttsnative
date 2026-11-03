---
bump: patch
desktop: changed
browser: changed
phone: changed
website: unchanged
docs: changed
---

## Technical

- Re-applies Dependabot #83–#90 by hand, each proposed after the cool-downs in `.github/dependabot.yml`: Tauri 2.12.3, tauri-build 2.7.3 (which adds the `static_vcruntime` build dependency), tauri-plugin-opener 2.7.2, tauri-plugin-updater 2.14.0 and serde_json 1.0.154 in the Windows shell, with `Cargo.lock` combined from Dependabot's five locks (tauri-utils 2.10.2, tauri-codegen and tauri-macros 2.7.2); @tanstack/react-query 5.104.4, @tauri-apps/api 2.12.4, lucide-react 1.59.0, radix-ui 1.8.1, react and react-dom 19.3.1, and the development tools @axe-core/playwright 4.14.0, @playwright/test 1.64.1, @tauri-apps/cli 2.12.3, eslint 10.13.0, knip 6.42.0, typescript-eslint 8.71.2, @testing-library/user-event 14.6.8, vitest and @vitest/coverage-v8 5.0.5 and jsdom 30.1.3; fastapi 0.146.0, starlette 1.9.0, pydantic-settings 2.16.0 and httpx2 2.14.0, with the server's lower bounds raised to match; and `github/codeql-action` v4.39.1 (`9b3254085494b55a0f7c4c2b3d2d52cc712ce370`). The licence inventory is regenerated; no licence changes.

---
bump: patch
desktop: changed
browser: changed
phone: changed
website: unchanged
docs: changed
---

## Technical

- Re-applies Dependabot #94, #95 and #99–#105 by hand, each proposed after the cool-downs in `.github/dependabot.yml`: Tauri 2.12.4, tauri-build 2.7.4, tauri-plugin-updater 2.14.1 and tauri-plugin-single-instance 2.5.5 in the Windows shell, with `Cargo.lock` combined from Dependabot's four locks (tauri-codegen and tauri-macros 2.7.4, tauri-runtime 2.12.2, tauri-runtime-wry 2.12.3 and ico 0.6.0, which no longer needs png 0.17); @tanstack/react-query 5.105.1, lucide-react 1.66.0, react-router 8.5.1 and vite 8.3.5 in the web app, and the development tools @tauri-apps/cli 2.12.4, eslint 10.14.0, globals 17.14.0, jscpd 5.4.2, knip 6.44.1 and typescript-eslint 8.72.1; fastapi 0.162.0, starlette 1.10.0, pydantic 2.14.2, pydantic-settings 2.16.2 and onnxruntime 1.31.1, and the development tools pytest 9.2.0, ruff 0.17.3, mypy 2.4.1 and httpx2 2.16.0, with the server's lower bounds raised to match; opentelemetry-api 1.45.2 in the server's and the voice-cloning worker's locks; and `github/codeql-action` v4.39.3 (`33d7b85da1a04171e211befe2c739303b9a4c066`). The licence inventory is regenerated; no licence changes.

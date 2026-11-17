---
bump: minor
desktop: changed
browser: changed
phone: limited: voices are created, and the voice-cloning engine installed, on the computer running TTSNative
website: unchanged
docs: changed
---

## New

- When the voice-cloning engine can't be installed on a PC, Voice Studio can make a matched voice instead: a stand-in mixed from TTSNative's own voices at the pitch of your recording, ready straight away. It isn't a copy of the voice, and your recording is kept for when the engine can be installed.

## Improved

- When installing the voice-cloning engine fails, TTSNative says why: Windows blocked the download, the network couldn't reach a server (and which one), the network replaced a security certificate, or the disk filled up.
- Installing the voice-cloning engine tries again by itself when the connection drops, waits longer on a slow connection, and works on networks that inspect secure connections.
- On Windows in S mode, TTSNative says up front that the voice-cloning engine can't be installed there, instead of failing after a long download.

## Technical

- Microsoft's Store certification of 2.2.0 failed (10.1.2.10) because the reviewer's install of the voice-cloning engine ended with "Installing the Chatterbox runtime failed": `uv sync` exited non-zero on their PC, and the reason stayed in a log there. `engines/install_errors.py` now sorts uv's last lines into `install_blocked` (Windows error 4551, 1260, 1625, 225 or 226, or the matching wording), `install_certificate`, `install_network` (with the host from the failing address) and `install_disk_full`; anything else keeps `install_failed` / `update_failed` and quotes uv's last `error:` or `Caused by:` line with the home folder shortened to `~`.
- `chatterbox_env.sync_environment` runs uv again after 5 s and 15 s when the failure was a dropped or stalled connection, and once with `UV_SYSTEM_CERTS=1` when a certificate was replaced; it sets `UV_HTTP_TIMEOUT=120` unless the environment already has one. `modelstore` builds its HTTPS client with `httpx.create_ssl_context()` plus the computer's own store (`load_default_certs`), and a failed download names the host.
- `engines/device_policy.py` reads `SkuPolicyRequired` under `HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy`: 1 is Windows in S mode. `EngineInfo.blockedReason` then carries the sentence the engine panel shows in place of the install button, and `install` refuses with `install_blocked`.
- Store build, found while tracing the failure: inside a packaged app Windows does not search `PATH` for DLLs, so putting the runtime's folder first on `PATH` (2.2.0's fix for PCs without the Visual C++ redistributable) did nothing there. The server now names the folder in `LTTS_VC_RUNTIME_DIR` and the worker loads `vcruntime140_1.dll`, `msvcp140.dll` and `msvcp140_1.dll` from it by full path before anything imports PyTorch (`compat.preload_vc_runtime`). Checked in a process with a package identity on Windows 11 26200: a load by name through `PATH` fails, and a load by name after a full-path preload succeeds.
- Store build: the worker is started as `python -I -c <bootstrap> <project>/src` (`engines/worker_launch.py`) instead of `-m ltts_chatterbox_worker`, so it no longer depends on the path uv recorded for the editable install. The Store installs each version in a new folder, which would have broken every cloned voice at the first update.
- Matched voice: `POST /api/voice-profiles/{id}/matched-voice` (`{"tone": "deeper" | "lighter" | null}`) measures the median pitch of the profile's reference (normalized autocorrelation on a 16 kHz copy, `voices/matching.py`), picks the two US English Kokoro voices that bracket it in `voices/builtin_pitch.json` and saves them as a blend named `<profile> (matched)`, replacing an earlier one of that name. A Kokoro blend's pitch follows the log-linear mix of its parts' pitches; with the real model the result lands within about a semitone of the target between the built-in voices' own pitches (86 to 204 Hz). `npm run test:inference` checks the table against the model and rewrites it with `LTTS_WRITE_BUILTIN_PITCH=1`.
- `scripts/desktop/msix.mjs` clears, in the package's own copy, a PE certificate-table entry that points past the end of its file (`scripts/lib/pe-certificates.mjs`). python-build-standalone's `zlib1.dll` ships that way, and the Store's signing step rejected the first 2.2.0 package for it (0x800700C1). The direct-download runtime is not changed.
- The voice-cloning worker's lock changed with the dependency update below, so an installed engine offers its one-click update after this release.
- Re-applies Dependabot #94, #95 and #99–#105 by hand, each proposed after the cool-downs in `.github/dependabot.yml`: Tauri 2.12.4, tauri-build 2.7.4, tauri-plugin-updater 2.14.1 and tauri-plugin-single-instance 2.5.5 in the Windows shell, with `Cargo.lock` combined from Dependabot's four locks (tauri-codegen and tauri-macros 2.7.4, tauri-runtime 2.12.2, tauri-runtime-wry 2.12.3 and ico 0.6.0, which no longer needs png 0.17); @tanstack/react-query 5.105.1, lucide-react 1.66.0, react-router 8.5.1 and vite 8.3.5 in the web app, and the development tools @tauri-apps/cli 2.12.4, eslint 10.14.0, globals 17.14.0, jscpd 5.4.2, knip 6.44.1 and typescript-eslint 8.72.1; fastapi 0.162.0, starlette 1.10.0, pydantic 2.14.2, pydantic-settings 2.16.2 and onnxruntime 1.31.1, and the development tools pytest 9.2.0, ruff 0.17.3, mypy 2.4.1 and httpx2 2.16.0, with the server's lower bounds raised to match; opentelemetry-api 1.45.2 in the server's and the voice-cloning worker's locks; and `github/codeql-action` v4.39.3 (`33d7b85da1a04171e211befe2c739303b9a4c066`). The licence inventory is regenerated; no licence changes.

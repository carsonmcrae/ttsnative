# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/). See [docs/guides/release-process.md](docs/guides/release-process.md).

## [2.2.0] - 2026-10-30

### Added

- **Immersive** reading experience for the six curated books: the characters' voices, the book's sound effects placed in the Sounds panel, and the recommended music track chosen for this device. Sound effects and music still stay off until you turn them on in the player.
- Six more background music tracks: three piano pieces (a Chopin nocturne and two Beethoven sonata movements) and three nature recordings (gentle ocean waves, rain in a forest and a small stream), each running about five to eight minutes before it repeats.
- Select text in a document and choose Sound effect to place a sound at those sentences.
- A **Sounds** tab in the reader can suggest a few sound effects for the chapter you are viewing where the text describes a sound, such as a creaking door or distant thunder; you hear each one, then accept, dismiss or swap it.
- You can add any sound from a bundled library at the sentence being read, choose when it plays and how loud, turn it off or remove it, and your arrangement stays with the document.
- Sound effects play beside the narration with their own volume and an intensity setting, and are off at the start of every narration until you turn them on.
- You can delete everything TTSNative keeps for you from **Settings → About → Delete my data…** in the Windows app. It asks you to confirm, then closes and removes your library, voices, recordings, settings and logs.

### Changed

- The reading experience no longer says sound effects arrive with a later version: it says how many it placed, and the Sounds panel marks them "From the reading experience". Adjust one and it becomes yours; remove one and it stays gone until you choose the experience again.
- Background music uses the same small amount of memory however long a track is, and passes from one part of a track to the next without a click, also on phones.
- The Voice Studio's Import a voice and Create voice buttons sit side by side instead of stacked.
- In a curated book's reading experience, the recommended background music track is named the way the player names it, and **Use this track** makes it this device's choice in the player at the recommended level. Music still stays off until you turn it on there.
- Eight sound effects whose synthesis is not convincing yet (the dog, owl, wolf, horse, birdsong, crowd, breaking glass and clashing swords) are marked **Experimental** in the library: they are never suggested automatically and a reading experience leaves them out, but you can still add one by hand.
- Sound effects never play louder than the narration: by default they sit well under it, and at the loudest settings an effect only reaches the narration's own level.
- Each voice card now shows a one-line credit naming the model behind the voice, its licence and that the voice is synthetic, with a Credits link to the full wording, given once at the end of the Voices page.

### Fixed

- Copy diagnostics no longer does nothing on a phone: when the browser can't copy, the details appear so you can select and copy them yourself.
- The reading experience no longer says that background music recommendations arrive with a later version: they are here.
- In the Voice Studio, a reading recorded far too quietly is now called too quiet, instead of being reported as having no speech at all.
- In a noisy room, the Voice Studio no longer says a take was cut off mid-word when the reading ended normally.
- The Windows installer checks that the drive has room for the new version before it touches anything, and says so plainly when it doesn't; an update that can't go ahead for lack of space reopens the version you have.
- When no update has been published yet, the app says so instead of blaming your internet connection.
- The uninstaller's question about deleting your data now names everything it would remove: the data folder, the remembered window position and the entry the installer keeps for its folder.
- Background music no longer clicks each time a track starts over in the Windows app, Chrome and Edge: newer versions of their audio decoder dropped a fraction of a millisecond from the start of each track.
- In windows between 768 and 1023 pixels wide, such as a tablet or a narrow window beside the sidebar, the player bar no longer pushes its voice, speed and export buttons past the edge: it uses the two-row layout there, with the audio mixer beside the play button.
- On phones the position slider is no longer squeezed between the buttons. It gets a line of its own, and on touch screens every slider responds to a 44-pixel-tall area, not just the thin track.
- Removing a voice from a blend no longer moves the other voices' choices, or your keyboard focus, onto the wrong row.
- In the library, drop documents on a folder's name to move them there; the whole row still lights up while you drag.
- On very narrow phone screens, the Voices page no longer scrolls sideways.
- A voice that can't be used yet is no longer greyed out, which made its card hard to read; it has a dashed outline and still says its engine isn't installed.

### Security

- Security updates for libraries in the optional voice-cloning engine, among them a critical fix for decoding compressed downloads.
- If you installed voice cloning, the app offers a quick update to it.
- Updated libraries throughout the app, including the speech engine's runtime and the Windows app's shell.
- A security update for one of the local server's libraries.
- If you installed voice cloning, the app offers a quick update to it: its list of components now names the same library's fixed version, though that library was never installed.
- A paired phone or tablet can no longer remove a saved cast; like other deletions, that is done on the computer, and the phone says so.
- A phone or tablet may ask for voice previews and alternative takes of a sentence in moderation; after a burst it is asked to wait a few minutes, and told why.
- Settings and the guides now say plainly that on macOS and Linux the Audiobookshelf key is kept in a file only your user account can read, not encrypted as it is on Windows.

### Technical

- Presets: `NOT_YET` and the 409 `component_unavailable` path are gone (every component is `available`); `PresetService._apply_effects` resolves anchors and places rows through `SoundEffectStore.apply_preset` (origin `preset`, status `accepted`, detector `preset:<id>@<version>`, volume `round(gain × preset volume)`, `until` from the end anchor or `duration_s / 4` sentences), records `{placed, skipped}` in `components_json` (skipped by reason: occupied, experimental, invalid, limit, unresolved), and `remove_preset` takes the rows out; the report gains `effectsPlaced`; `PresetStores` groups the service's stores. Store: `Origin` gains `preset`, `PresetEffectIn`, `apply_preset`, `remove_preset`; a PATCH makes a preset row `manual`. Web: Immersive offered, an effects line, "From the reading experience" in `EffectRows`, sound-effects queries invalidated on apply and remove. `persistence-test.mjs` applies the whole experience. No migration.
- Music is chunked. `npm run music:build` cuts each prepared loop into chunks of about 20 s (`public/music/<id>/01.webm`, …) that each carry 960 frames (20 ms) of their neighbours, checks every chunk by decoding it with FFmpeg, and limits true peaks at four times the rate over the loop wrapped in its own end and start. `library.json` tracks list `chunks` (file, frames, bytes, SHA-256) and `edgeFrames` instead of one `file` and `sha256`.
- `MusicEngine` plays a track as its chunks on one frame-exact timeline (a 48 kHz `AudioContext` where the browser allows it): the chunk playing and the next one per track, plus three recently used chunks decoded. It finds each chunk's music from the decoded length (Chromium 156 trims 24 frames from the start, Firefox 157 0–1) and crossfades every join, the loop point included, over 10 ms. This replaces the whole-buffer loop for music, and the 30 ms whole-track seam crossfade that first fixed Chromium 156's trim. `dispose()` also disconnects the master gain.
- Measured in Chromium (the page's private memory, after a forced garbage collection): +24, +31 and +40 MB for 2, 10 and 20-minute tracks walked to the end, +55 MB during a crossfade between two 20-minute tracks; decoding the whole track at once, as before: +52, +243 and +493 MB.
- `tests/e2e/music.spec.ts` (with `music-probe.ts`) measures every chunk join and loop point of all 17 tracks as the player schedules them, in Chromium 156 and Firefox 157: at most 0.92 against the limit of 1 (cut without the crossfade, up to 2.83), each next chunk on the exact frame, copies aligned. It fails with the crossfade or the trim correction removed. Measured, not listened to.
- Six tracks added (the owner's approved selection; the library test caps the library at these 17): Musopen recordings on Wikimedia Commons (public domain or CC0, with the compositions in the public domain) and Freesound CC0 field recordings (their high-quality previews), licences checked on the live and archived pages on 2026-10-22 and credited in `CREDITS.md`. The bundled music grows from 13.3 MB in 11 files to 33.5 MB in 200 (the web build from about 16 MB to 36 MB).
- Engine tests split into `engine.test.ts` (chunks and joins) and `engine.lifecycle.test.ts`, with `test/musicEngine.ts`; the shared loop helpers' tests moved to `lib/audio/webAudio.test.ts`.
- `SelectionStyler` gains a "Sound effect" button that opens `SoundLibraryDialog` (now with an optional `error`) and posts a manual effect at the first selected sentence; a looping sound's `untilSegment` is the last selected sentence. `PageHeader` actions no longer shrink beside a long description.
- Server: `ltts.sfx` (vocabulary, deterministic lexicon detector, validation gate with intensity limits, store, router) with `sound_effects` and `sound_analyses` tables (one migration at the end of the list) and the catalogue `ltts/sfx/library.json`; endpoints under `/api/sound-effects/library` and `/api/documents/{id}/sound-effects` (list, add, change, remove, review, analyse). ADR-22.
- Web: `features/sfx` (Web Audio engine with a limiter, scheduler, session following the player, provider, Sounds panel, library and adjust dialogs), a `data-effect` marker on sentences, and 36 synthesised MP3 sounds under `public/sfx/` (1.3 MB) built by `scripts/media/sound-library.py`.
- Docs: `docs/research/sound-effects.md`, `docs/research/sound-effects-research.md`, wiki `Sound-Effects.md`.
- Microsoft Store build (ADR-26): the desktop shell's `store` Cargo feature leaves out the updater plugin, answers update checks with `store` and reports `updates: "store"` in `desktop_info`, so About says the Microsoft Store keeps TTSNative up to date and hides the GitHub checks. `npm run desktop:store` builds the program with that feature and packs `TTSNative-<version>.msix` with `scripts/desktop/msix.mjs`: a full-trust Windows 11 package whose user folder is excluded from file-system virtualisation, logos made from the brand icon, identity from `apps/desktop/store/identity.json` (a test identity until Partner Center's is recorded). The Desktop workflow lints and tests the shell with the feature too, and a new "Microsoft Store package (MSIX)" job builds the package with the runner's Windows SDK and keeps it as an artifact for sideloading.
- `delete_user_data` (`erase.rs`): refuses any folder not named after the app's identifier, stops the server, and a hidden `cmd.exe` removes `%LOCALAPPDATA%` and `%APPDATA%\com.ttsnative.desktop` with `rmdir /s` (links inside are removed, not followed) once the app has closed, retrying for 30 seconds; the folder paths reach it only through environment variables. `ConfirmDialog` takes `confirmDisabled`.
- Re-applies Dependabot #71–#77 by hand, every release past the 14-day cool-down: Tauri 2.12.2, tauri-build 2.7.2, tauri-plugin-opener 2.7.1, tauri-plugin-single-instance 2.5.3, tauri-plugin-updater 2.13.3 (with minisign-verify 0.3.0); @tauri-apps/cli 2.12.2, @tauri-apps/api 2.12.3, @tanstack/react-query 5.104.2, lucide-react 1.55.0, radix-ui 1.8.0, vite 8.3.4, jscpd 5.4.1, knip 6.41.0, prettier 3.9.10; fastapi 0.143.3, pydantic 2.14.1, numpy 2.5.4, onnxruntime 1.31.0 and ruff 0.17.1 (cap now <0.18).
- Security fixes for every open Dependabot alert: undici 8.12.2 (npm, web tests only; Dependabot's 8.12.3 is still inside the cool-down); filelock 4.2.1 in both Python locks, and setuptools 84.2.0, virtualenv 21.14.13 and brotli 1.2.1 in the worker, through `exclude-newer-package` security exceptions with removal dates (docs/security/supply-chain.md). The worker's expired omegaconf exception is gone. The worker lock's fingerprint changes, so existing voice-cloning installs are offered a one-time environment update.
- `AboutSection` always attempts `navigator.clipboard.writeText` (a missing clipboard on plain HTTP now rejects instead of short-circuiting) and on failure shows the report in a read-only, select-on-focus textarea.
- Presets: `music` leaves `NOT_YET`; the report's `music` (`trackId`, `volume`, `note`) replaces `musicTrackId`; applying `music` records the track and level in `document_presets.components_json` and writes nothing else (the track a device plays is the web app's own setting there); `tests/test_library_presets.py` keeps `KNOWN_TRACKS` equal to `features/music/library.json`; `ReadingExperience` names tracks from that library and chooses them through `useMusic()`.
- `take_checks`: when the fixed −45 dBFS speech threshold finds a take short or too quiet, the whole recording is measured against its own background (its quietest tenth of 30 ms frames). At least 3 s of voice 15 dB above that background, at under −40 dBFS, now gives `too_quiet` alone: previously `no_speech` or `no_sound`, or `too_quiet` plus `pauses`/`incomplete` that followed from it.
- `cut_off` also needs the edge frames 6 dB above that background, so steady noise within 15 dB of the speech no longer reads as a word cut off.
- A local benchmark of 540 clips edited from 48 studio takes: false warnings on complete clips fell from 27.9 % to 0 %, and incomplete-take detection is unchanged (65 %).
- `hooks.nsh`: `NSIS_HOOK_PREINSTALL` compares `${DriveSpace}` on the install drive with Tauri's `${ESTIMATEDSIZE}` plus a 200 MB margin, aborts with error level 3 (a message box unless silent) and in `/UPDATE` mode relaunches the installed `TTSNative.exe`; `scripts/desktop/space-test.mjs` proves it on a 256 MB virtual disk (diskpart; administrator). `updates.rs` maps `tauri_plugin_updater::Error::ReleaseNotFound` to a new `CheckResult::NoRelease` (the web app's `noRelease` status, "No update has been published yet."), logged but not remembered as a check. `update-test.mjs` also signs B with a second throwaway key and proves that signature is refused. `scripts/desktop/processes.mjs` lists every process under the install or data folder (server, WebView2, uv, the Chatterbox worker `python.exe`); the persistence test requires none after a close or a crash. `build.mjs` takes the `TTSNATIVE_TAURI_CONFIG` overlay only for a test build (`TTSNATIVE_TEST_HOOKS=1`) and only for `plugins.updater`; a release build refuses it (`build-config.mjs`, with tests).
- Chromium 156 decodes the bundled Opus/WebM tracks 24 samples short at the start (FFmpeg 9, Chrome 152 and Firefox 157 decode the full length), so the sample-exact whole-track loop jumped at its seam on 7 of the 11 tracks (seam ratio 1.05–3.85 against a limit of 1). The chunked player (see the long-tracks change) finds each chunk's music from its decoded length and crossfades every join and loop point over 10 ms; every join of all 17 tracks measures at most 0.92 in Chromium 156 and 0.91 in Firefox 157, and the e2e test fails when the crossfade or the trim correction is removed. Sound-effect loops (MP3) decode to full length in both browsers and are unchanged.
- `opentelemetry-api` 1.45.0 → 1.45.1 (via fastapi) in `apps/server/uv.lock` for CVE-2026-114603; released 2026-10-06, so within the 14-day cool-down, no exception needed. Only that package changed in the lock.
- The same bump in `apps/chatterbox-worker/uv.lock` (replacing Dependabot #66, whose lock was regenerated by another uv version). Not reachable there: gradio, fastapi and opentelemetry-api are `sys_platform == 'never'` in both exported extras, so nothing installs them; it keeps the lock free of the flagged version. The worker lock's fingerprint changes, so existing voice-cloning installs are offered a one-time environment update.
- Player bar: the compact layout runs up to `lg` (1024 px) instead of `md`; from `lg` the title shrinks (`max-w-64`) instead of keeping a fixed width. The position row wraps, with the slider group at least `basis-60`. `Slider` is `h-11` under `pointer-coarse`.
- `npm run perf:listening` names the minutes its closing rate covers ("last N minutes"), so a short run no longer claims ten.
- SonarQube review for 2.2.0: the server, web app, build scripts and website were brought back to no open findings (long functions split into named helpers, nested conditionals unpicked, repeated literals named once, statuses in `<output>`, sorts that feed generated files given an explicit code-unit comparator so their order can't move). Security hotspots were reviewed one by one, and each verdict is recorded in SonarQube with its reasoning.
- The update test gives every throwaway signing key its own random password instead of a fixed one in the source.
- A text selection longer than 1,000 characters is never searched for a word to fix, so the edge-trimming pattern only sees short strings.
- `lan/policy.py`: `DELETE /api/cast-presets/{id}` joins `_ON_THE_COMPUTER`; voice previews and segment takes (`_BRIEF`) draw on a second per-device `WorkBudget(BRIEF_PER_WINDOW)` (`LanService.previews`, 60 per 10 minutes) and are refused with 429 `lan_busy` and a previews-specific message; `WorkBudget` takes a `limit`. The reader hides a saved cast's remove control on a phone and says where casts are removed. The Audiobookshelf Settings copy, the wiki and the threat model describe the key file on macOS and Linux. Security review for 2.2.0 in `docs/security/review-2.2.0.md`; threat-model rows for web-page import, Audiobookshelf upload and the bundled book catalog; supply-chain.md states the real Dependabot cool-downs; the licence inventory lists the bundled books and sound effects.
- Store: adding or changing an effect refuses a looping sound with no end sentence (`effect_span`), so an ambience can never be left to loop until the narration pauses.
- Catalogue: `experimental` and `qualityNote` per sound in `ltts/sfx/library.json` (the switch is `EXPERIMENTAL` in `scripts/media/sfx_recipes.py`, one line per sound; the generator writes both fields); `catalogue.suggestable(event)` and a `default_sound` that prefers a credible sound; analysis drops proposals for events without a credible sound. The listening page shows the flag and the note.
- Engine: the per-effect gain cap (`MAX_GAIN`) is 1 instead of 1.5, so no effect plays above its mastered level, which is the narration's own.
- Tests: `tests/test_sound_mix.py` measures every bundled sound (mastered at or below −19 dBFS loud, −4.5 dBFS peak) and asserts the default and worst-case margins against the measured Kokoro narration level (−20.5 dBFS), re-measured by an inference test; the web tests play music and effects together under the narration, check the default levels and that no gain is above 1, and that a pause stops both and leaving the page closes both contexts.
- `VoiceInfo.credit` (one line for the card) beside `VoiceInfo.attribution` (the full wording), both from `ltts.engines.credits` (`KOKORO`, `CHATTERBOX`, `CLONED`, `BLEND`). The full Kokoro wording credits everything `apps/desktop/licenses/kokoro/README.txt` credits (StyleTTS 2 by yl4579, Koniwa by tnc under CC BY 3.0, SIWIS under CC BY 4.0, no affiliation), and a test keeps the two in step.
- `VoiceCredits` shows each distinct attribution once with the voices it covers and where the licence texts are; a card's Credits link scrolls to it and moves focus there without changing the address.
- The voice grid is `grid-cols-1` below `sm`, so a Mandarin voice's truncated language line no longer widens the implicit column past a 320 px screen.
- An unavailable voice card is `border-dashed` instead of `opacity-70`: the dimming took its avatar initials and badges to 3.1–4.3:1, which axe flagged as `color-contrast` on `/voices` in both themes (`tests/e2e/states.spec.ts`).
- `github/codeql-action` pinned to v4.39.0 (`6f2ac81f5cd81fe351a197ba0b00d91d03cd2aee`, released 2026-10-15) in `.github/workflows/codeql.yml`, replacing Dependabot's #51. GitHub Actions follow the 7-day cool-down in `.github/dependabot.yml` (the 14-day rule covers Python, npm and the Tauri crates), which this release passed on 2026-10-22; its release notes list no security fix.
- The Windows runtime ships the Microsoft Visual C++ runtime (`msvcp140.dll`, `msvcp140_1.dll`, `vcruntime140.dll`, `vcruntime140_1.dll`; Microsoft-signed, 14.40 or later) next to `python.exe`, copied from Visual Studio's redistributable folder (or `TTSNATIVE_VC_REDIST_DIR`) and recorded with its SHA-256 in `runtime-manifest.json`. ONNX Runtime and espeak-ng need it and a clean Windows 11 PC doesn't have it, so the default voice failed to load there; GitHub's runners have it installed, so no automated check had noticed. 2.1.0 is released from the commit with this fix, so nothing changes for anyone who installed it.
- `npm run desktop:build` fails if any program or library in the runtime loads a DLL that neither ships with it nor comes with Windows (`scripts/desktop/cpp-runtime.mjs`, import tables read by `scripts/lib/pe-imports.mjs`).
- Change files declare each surface's impact (`desktop`, `browser`, `phone`, `website`, `docs`: `changed`, `unchanged`, `limited: <why>` or, for the website, `pending-release`). `lib/changes.mjs` rejects undeclared surfaces, app surfaces that diverge without a stated limitation, `none` changes that alter the app, user-facing bumps that reach no surface and undocumented New features; `check-changes.mjs --base` checks `website`/`docs` against the files the pull request changes. `npm run change` writes placeholders CI refuses. New `AGENTS.md`; CONTRIBUTING, the PR template and `.changes/README.md` describe the rule.
- The Desktop workflow's smoke test proves the installed app serves the installer's own web build byte for byte (every file under `apps/web/dist`), opens every page in `scripts/lib/app-routes.mjs` and reports the build's version; `app-routes.test.mjs` keeps that list in step with the router.
- Development wiki page: contributors add a change file (`npm run change -- <bump>`, with the five surface keys) instead of editing `CHANGELOG.md`; coverage gates are 100 % lines and branches for the web app and the server; the worker uses PyTorch 2.11; the version lives in 11 places; current code layout (`apps/desktop`, `site/`, `.changes/`, the server's `library`, `sfx`, `lan`, `speech_api` and `pronunciation` packages); links to the working rules and the release readiness gate.
- Exporting Audio: exports carry the document's own title, album and track tags (and the M4B details), never a comment or tag naming the app; where the Windows app keeps exports; the Windows app ignores `LTTS_FFMPEG`.
- Privacy and Security: the Windows app's data folder and bundled runtime, web page import and Audiobookshelf connections, the one remaining (ignored, unreachable) `torch` advisory in place of the fixed `setuptools` and reduced `torch` ones, and the unsigned installer.
- FAQ: every connection to the internet and when it happens (setup, model and engine downloads, web page import, Audiobookshelf, the Windows app's update check and update download); platform claims limited to what CI tests; phones don't import voice recordings.
- Local speech API guide: the Windows app's ports (8770 to 8789) and where to find the port in use.
- Getting Started: five pages (Library, Voices, Voice Studio, Exports, Settings), the Explore tab, current formats and web page import, and the player's bookmark, sleep timer and mixer controls.
- README: what the published 2.0.0 has against `main`, the installer not published yet (SmartScreen warning, update signature), platform testing as CI does it, the Windows app's size and data folder.
- Windows App and Installation: requirements, what the installer bundles against optional downloads (voice cloning sizes, ffmpeg), where data lives, backing up and moving it, how updates are verified, and uninstalling with data kept unless deletion is confirmed twice (naming the data folder, the window position and the installer's registry entry).
- Troubleshooting (wiki and guide): a Windows app section (log folder, SmartScreen, start-up failures, ports 8770 to 8789, the installer's free-space check, "No update is available right now", failed updates).
- New wiki page What Works Where: features against the Windows app, the browser on the computer, phones on the home network and the website, with the reason for each limit (including the per-device allowances and saved casts staying on the computer), taken from `lan/policy.py` and the interface; linked from Home and the sidebar.
- Settings and Models, Other Devices, configuration guide: the Windows app's update check, ports, `LTTS_*` handling and phone permissions; `LTTS_EXTRA_ALLOWED_HOSTS` and `LTTS_FFMPEG` listed.
- Bug report form: where it happened, install type, app version (Settings → About) and logs location.
- Architecture overview: the desktop shell, LAN mode, music and sound effects, the included books, exports and the speech API, with links to the ADRs.
- `npm run lint:repo` now fails when a file brings in a language, runtime or package manager the project has no security tooling for (PHP, Ruby, Go, the JVM, .NET, a second JavaScript or Python package manager, a container image and others). Adding one needs an architecture decision and, in the same pull request, its Dependabot entry, an audit in `npm run security` and scanner coverage (CONTRIBUTING.md, "Adding a language or package manager"). TTSNative uses no PHP today; this keeps it that way until its tooling arrives with it.
- `npm run perf:listening` (`tests/perf/long-listening.mjs`) measures a long listening session in Chromium: private memory per browser process every minute after a forced garbage collection, the JavaScript heap against the rest, and the page's DOM nodes and event listeners, then after a pause and under simulated memory pressure. It can run with background music, or play the same sentence audio on a bare page without the app.
- `docs/guides/performance.md` documents narration memory in long sessions (issue #44): it grows in the browser's media handling outside JavaScript, the same way without the app, about 5 MB a minute for the first 600 sentences and about 0.5 MB a minute after that. The app's own share is about 15 MB an hour, with the JavaScript heap and the DOM flat.
- The Desktop workflow builds the update test's versions A and B at the same time: one job makes the throwaway update key (`update-test.mjs --make-key`, passed to the builds as a one-day artifact of the run), two jobs build A and B in parallel (`--build old|new`), and the update test runs on their installers and signatures (`--test`). The key, its password, what the builds trust and what the test checks (wrong signature and broken download refused, verified update installed, document kept) are unchanged; `npm run desktop:update-test` with no arguments still does everything in one go.
- The release-readiness gate separates the acceptance list into **Before release** (each tick needs a "verified:" note; a **(required)** check can't be waived), **After publishing** (listed, and refused if marked before the release exists) and **Blockers** (ticked with "verified:"). The next version's gate requires the previous gated version's after-publishing checks, so post-release smoke tests can't be skipped. This removes the circular requirement that the website and download be verified before the release that creates them.
- The gate checks on GitHub that the previous release is published, not a draft, from a commit whose version files name it and that has no pending change file, so a tag on `main` by mistake is caught.
- SonarQube evidence must meet the project's policy (100 % line and branch coverage, no duplication, no bug, vulnerability or code smell, no unreviewed hotspot) whatever the server's gate allows; `npm run sonar:gate` sets the server's gate to the same thresholds on new code and the whole project. The SonarQube API calls are shared in `scripts/lib/sonar.mjs`.
- Release-readiness gate (`npm run release:gate -- X.Y.Z`, `scripts/lib/gate.mjs`): from 2.2.0 the Release workflow refuses a tag unless CI, Desktop, CodeQL and Inference & E2E passed on that exact commit, `docs/readiness/X.Y.Z/quality.json` records a passing SonarQube gate for it (or for a commit that differs only by that evidence), and `docs/readiness/X.Y.Z/acceptance.md` has every manual check done or waived with a reason and no open blocker. `npm run sonar:evidence` writes the SonarQube file from the server's API (token from `SONAR_TOKEN` only). Release builds download and verify the bundled Python and models afresh instead of restoring them from a cache.
- Website: every claim and screenshot that only holds for 2.1.0 (chapter fixes, the included books and library organisation, study aids, export subtitles, Studio noise cleanup, the ONNX telemetry note, the Library, Included books and Voice Studio screenshots) now sits in an `if:released-2.1.0` block, so the published site describes 2.0.0 until 2.1.0 is out; the download page carries `noindex` while no installer is published; the seven voice samples and both videos have accessible names, the French and Spanish quotes are language-tagged; the demo is described as 2½ minutes and the source install as the current development version. The download and release pages carry the same social metadata as the home page; the download page lists what the app needs (Windows 11 with WebView2, about 1.5 GB of disk, no graphics card); the Copy button keeps an accessible name through its states (`demo.js`); the sitemap lists `/download/` only while an installer exists; `build-site.mjs --expect-installer X.Y.Z` fails a build that would not advertise that installer, and `release.yml` passes the released version to the Pages dispatch (`pages.yml` input `expect_installer`). The head every page shares (social image, theme colours, icons, stylesheets) lives once in `site/partials/head.html`; `fillHead` inserts it where a page says `<!-- head:shared -->`, with icon and stylesheet links relative to the page's folder, and the link check resolves relative links from that folder. The website spec takes the newest finished notes file as the latest version instead of a version written into the test, and its type-check reads the module it imports for that.
- Server tests no longer time out waiting for a background job that is slow but still moving. The job manager counts every write to a job and wakes anyone waiting on it; the tests' `wait_job` sleeps on that signal instead of polling the API and fails only when a job stops changing for 10 seconds, with the job's state and every thread's stack. It removes the "job did not finish" failures of two export tests on a busy Windows runner, where each sentence's database commits waited for slow disk flushes.
- The sound-detection speed check measures its thread's CPU time instead of the wall clock, so other test workers sharing the CPUs no longer count against its budget.
- Vitest starts one worker per free CPU (at most one per core on big machines), sampled when it loads its configuration, so CPU-bound web tests keep their headroom on a busy machine; an idle CI runner keeps its usual count. The offline-server flow moves a fake clock past the retry backoff instead of waiting 3 s for it.
- ttsnative.com's installation steps describe both warnings an unsigned installer meets: Edge's "isn't commonly downloaded" (… → Keep, then Keep anyway) and SmartScreen's "Windows protected your PC" (More info → Run anyway).
- The download section leads with "Get TTSNative from the Microsoft Store" once `listed` is true in `apps/desktop/store/identity.json`, keeping the installer as the alternative (`scripts/site/store.mjs`, `<!-- if:store -->` / `<!-- if:no-store -->`, applied after the download section is decided).
- The code signing policy says the direct download is unsigned: SignPath Foundation declined on 2026-10-24 pending wider adoption (ADR-26 updated); the Microsoft Store version is signed by Microsoft.
- The Release workflow builds `TTSNative-X.Y.Z.msix` from the tag with the Partner Center identity and keeps it as the `ttsnative-store-package` artifact for 30 days; it publishes nothing. `docs/guides/windows-distribution.md` now walks through the Store submission: package, properties, listing text, screenshots, restricted-capability justifications and certification notes.
- ADR-26 and `docs/guides/windows-distribution.md`: Windows ships through the Microsoft Store as the main channel (MSIX, re-signed by Microsoft, so no SmartScreen warning) with the direct download kept and signed for free by SignPath Foundation. The guide lists the owner's account steps, the design of both packages and what is still open.
- ttsnative.com/code-signing/ is the code signing policy SignPath Foundation requires: what is signed and by whom, who approves a signature, what the app sends over the network and how to check a signature. It says plainly that 2.1.0 and earlier are unsigned. The home page footer and the download page link to it as "Code signing policy", and it is in the sitemap and the website's end-to-end tests (desktop and phone, axe).

## [2.1.0] - 2026-10-22

### Added

- **Model integrity checks and repair.** Every model file is checked against its published SHA-256
  checksum before an engine loads it, including files installed long ago. A missing, incomplete or
  mismatched file puts the engine in a **Needs repair** state that names the file, and **Repair**
  downloads only the damaged files again. `npm run setup`, `npm run doctor` and `ltts models verify`
  report and fix damaged files too, and speech that comes back empty or invalid is refused with a
  clear message instead of a server error.
- **Project website** rebuilt for TTSNative: features, the overview and demo videos, screenshots,
  privacy, install steps, how it is built and a FAQ, plus a speech demo that uses the browser's own
  voices (clearly labelled as not TTSNative's, with online voices flagged). Built and link-checked by
  `npm run site:build`, tested in Chromium and on phones, and published to GitHub Pages.
- **Studio voices:** a guided, resumable session for your most faithful voice. A microphone check
  (including a thin, "tinny" microphone), 48 passages in six styles recorded losslessly or imported
  from a long recording, then a build that averages the speaker over the session, tests five candidate
  voices and lets you pick by ear. Quick voices are unchanged.
- **Delivery** for custom voices: Steady, Natural or Expressive.
- **Microphone tone checks** (bright or thin, measured on vowels so "s" sounds don't count) in every
  voice-recording check. In a studio session, the microphone check plays your recording back, picks
  your USB/XLR microphone, and can correct the tone automatically, with a before-and-after preview.
- **Chatterbox updates in place:** when the worker's locked packages change, Settings → Engines &
  models offers "Update available" instead of a reinstall.
- **Recording cleanup** for quick and studio voices: background noise reduction, a low-rumble filter
  and treble and low-end controls, with a suggestion measured from the recording, a before-and-after
  preview, and your last choice remembered for the next recording. Noise reduction follows the
  approach of [noisereduce](https://github.com/timsainb/noisereduce) (MIT), re-implemented without
  new dependencies.
- **Adjust this section** in the reader: rename a chapter or move where it starts, sentence by
  sentence.
- **Pronunciation dictionary** (Settings → Pronunciation): whole-word rules such as "Kael" → "Kale",
  optionally case-sensitive, heard before saving, applied to reading, previews and exports; only
  sentences containing a changed word are regenerated.
- **Bookmarks and notes**: bookmark the sentence being read (button or `B`), a Bookmarks tab beside
  Contents, notes on each bookmark, and an export of all notes as Markdown.
- **Search** inside a document, with matches marked and a jump to the sentence; **library search and
  sort** (title, date added, least listened).
- **Sleep timer**: stop after 5–60 minutes or at the end of the section, always between sentences.
- **Reading text settings**: text size, line spacing and typeface, per device.
- **Export subtitles and tags**: optional sentence-timed SRT subtitles, and title, album and track
  tags in exported audio.
- **Attribution**: [ATTRIBUTION.md](ATTRIBUTION.md) (what the MIT License requires and what is only
  asked) and [CITATION.cff](CITATION.cff); SPDX licence and copyright lines in every source file, checked
  by `npm run lint:repo`; the author and licence in Settings → About, the API description and package
  metadata. The built web app now ships the licences of the packages and fonts it bundles
  (`THIRD-PARTY-LICENSES.md`). Exported audio carries only the document's own title, album and track
  tags.
- Play quiet background music under the narration: turn it on from the music button in the player, choose from eleven free tracks (ambient, fantasy, cinematic, lo-fi, focus and nature), and preview any of them before you pick.
- Music has its own volume, separate from the narration, and follows it: it pauses when you pause, carries on when you play, and fades gently in and out.
- Set the narration and the music volumes side by side in the new audio mixer in the player.
- Music is off at the start of every new narration. TTSNative remembers your track and volume on each device, but you always choose when the music plays.
- Organise your library: put documents in folders (nested as deep as you like), gather them in collections (a document can be in several), mark favourites, give each one a type and genres, and add your own tags.
- The library has a rail of views: all documents, continue reading, favourites, recently added, your collections and your folders, with a matching menu on phones.
- Search finds authors, file names and tags as well as titles; filter by genre, type and progress; sort by author too.
- Select several documents at once to move, tag, favourite, add to a collection or delete them together, or drag a document onto a folder.
- Poems and other verse keep their lines: a line break is read with a short pause and shown as a line break, not as a new paragraph.
- Explore: 25 public-domain books come with TTSNative (Alice, Frankenstein, Pride and Prejudice, Sherlock Holmes, Poe, Dickinson, Whitman, Douglass, Thoreau and more), grouped by kind, each with a cover, a description and content notes.
- Every included book says where it is public domain: always the United States, and elsewhere by its author's death year, naming the countries where a longer term still runs.
- Open an included book and it joins your library like any other document; hide the ones you don't want to see. The credits name every edition, cover artist and source.
- Reading experiences: six of the included books come with a curated cast. In the reader, choose **Multi-voice** to give Alice, Scrooge, Holmes, Elizabeth Bennet and the rest their own voices and to hand untagged lines such as the Raven's "Nevermore" to their speaker.
- **Standard** takes an experience out again and keeps every voice you chose yourself. Sound effects and music are described but arrive with a later version; nothing starts playing on its own.
- Record a guided studio session for your most faithful custom voice: a microphone check, short passages to read or a long recording to import, then pick the best of five candidate voices by ear.
- Choose how a custom voice delivers its lines: steady, natural or expressive.
- Clean up a voice recording with background noise reduction, a rumble filter and tone controls, with a before-and-after preview.
- Teach TTSNative how to say names and words with a pronunciation dictionary.
- Bookmark the sentence being read, add notes to bookmarks, and export all your notes.
- Search inside a document and jump to a match; search and sort your library.
- Set a sleep timer that stops between sentences, after a set time or at the end of the section.
- Adjust the reading text's size, line spacing and typeface.
- Rename a chapter or move where it starts.
- Export subtitles timed to each sentence, with the title, album and track filled in on exported audio.
- Read HTML pages, FB2 and MOBI books, and import a public web page by its address.
- Running headers, page numbers, footnotes and citation markers are skipped when reading aloud and exporting; they stay visible, marked as skipped, and you can read them all again or skip any sentence by hand.
- Fix how a word is said from the reader: select it, write it the way it sounds (gnocchi → NYOH-kee), hear both versions, and keep the fix for this document or for all documents.
- Export M4B audiobooks with chapters, a description and a cover, and read-along EPUB books whose text is highlighted as the audio plays.
- Pause and resume audiobook exports, even after a crash or restart; the new Exports page lists them, shows each one's place in line, and lets you resume, cancel, download or delete them.
- Send a finished export to your own Audiobookshelf server.
- Give characters their own voices, read quoted speech in a dialogue voice, and read chosen sentences as an announcement, a phone call, a radio broadcast, from far away, as a robot, quietly or as a memory.
- Mix two to four built-in voices into a new voice.
- Paste text with speech marks for pauses, voices, effects, styles, sounds and pronunciations.
- Share a custom voice as a file and import one shared with you; the file is checked completely and previewed before anything is imported, and an import never replaces one of your voices.
- Pair a phone or tablet on your home Wi-Fi to read and listen from it, with the computer doing the work (optional, off by default and after every restart; home networks only).
- Let other programs on this computer use TTSNative's voices, including OpenAI-style voice names (optional, off until you turn it on; Settings shows the exact address to use).
- Fine-tune a studio voice on its takes with an NVIDIA graphics card, and keep it only after hearing it against the voice as it is (experimental; in a blind test it didn't sound clearly better).
- Rebuilding a studio voice's speaking styles keeps the ones from before, and you can switch back.
- A high-contrast option, wider letter and word spacing for the reading text, and support for Windows high-contrast themes.
- The app's screens open even while the server can't be reached and say so, and a Reconnecting bar shows until it answers again.
- Install TTSNative on Windows 11 like any other app: it opens in its own window from the Start menu or an optional desktop shortcut, with nothing else to set up.
- The default voice comes with the app, so you can start listening right after installing.
- TTSNative lets you know when a new version is available, shows what's new, and installs it for you once you agree. You can turn these checks off.
- See what changed in every version under Settings, About, even without an internet connection.

### Changed

- **Renamed to TTSNative** (formerly Local TTS), with a new identity: an N drawn as five waveform bars,
  the app icon and favicon, logos and a brand guide (`brand/`). The repository is now
  `carsonmcrae/ttsnative`; old GitHub links redirect. Internal identifiers are unchanged, so existing
  installations keep working: the `ltts` package and command, `LTTS_*` settings, the `data/` folder and
  saved browser preferences. Releases are now named `TTSNative <version>`, with `ttsnative-*` files.
- PDF chapters now start at their heading line, not at the top of the page the outline points to, so
  the end of one chapter no longer appears at the start of the next.
- API: `POST /api/voice-profiles/analyze` returns `{report, suggested}`;
  `POST /api/voice-sessions/tone-preview` is replaced by `POST /api/voice-profiles/cleanup-preview`;
  a studio session's `tone` is now `cleanup`. New: `PATCH /api/documents/{id}/sections/{index}`,
  `GET /api/documents/{id}/search`, `/api/documents/{id}/bookmarks` and `/api/pronunciations`;
  exports accept `captions`. Database migration 5 adds the
  `pronunciations` and `bookmarks` tables.
- **Node.js 22.22 or newer** is now required (React Router 8 and jsdom 30 need it).
- Dependencies: React Router 8, radix-ui 1.7, Vitest 5, jsdom 30.
- Development tooling: ESLint 10 (ESLint 9 is no longer supported). eslint-plugin-jsx-a11y has not
  yet published ESLint 10 support, so an npm override accepts it; its rules run unchanged. The server
  tests use httpx2, which Starlette's test client now prefers; the app itself still uses httpx.
- Local TTS is now called TTSNative, with a new look. Your documents, voices and settings carry over.
- Voice recordings tell you when a microphone sounds too bright or thin, and a studio session can correct its tone automatically.
- PDF chapters now begin at their heading, so the end of one chapter no longer appears at the start of the next.
- A shorter studio session: about 15 passages instead of 48, tiers that follow what the voice uses (Foundation, Developing, Complete), a suggested next passage, and progress that weighs how clean and long your takes are.
- Studio takes name the background noise when it matters, point out a take cut off mid-word, keep the previous take to compare and restore, and say what to do about microphone problems.
- Listening times count only what is read aloud, and follow skipped sentences and the cleanup.
- The Steady delivery of custom voices is steadier, and their audio is generated again once.
- Background noise in a studio take is advice, not an error.
- Selecting text in the reader no longer starts playback from the sentence you clicked.
- English voices read money, clock times and phone numbers the way a narrator does where the meaning is clear: £1,284.50 is "1,284 pounds 50", "at 4:45 p.m." is "at 4 45 PM", and a phone number is read digit by digit. Code, formulas, ratios and lists of numbers are read as before.
- English voices read years and abbreviations naturally too: "in 1998" is "in nineteen ninety-eight", Chapter IV is "Chapter 4", and Lt. Col., Rev., Mt., Rd., Ave., Ms. and approx. become words. The text you see never changes, and a pronunciation you saved still wins.
- Every voice card says where its voice comes from and under what licence, and that it is synthetic speech rather than a recording of a person.
- Updating keeps your documents, voices and settings, and uninstalling asks twice before deleting them.
- Release history shows one version at a time: pick a version from the list or step to the older or newer one, see when it came out and what changed, and find the version you're running marked.
- The version you're running is shown at the bottom of the sidebar and leads to About, where What's new and Release history are.
- On the website, every version has its own release notes page with links to the older and newer versions, and the home page names the latest version.

### Fixed

- **Website on phones:** the install commands scroll sideways on narrow screens and can now be reached
  and scrolled with a keyboard (a labelled, focusable region). The phone tests now run axe.
- Pausing or cancelling an export never ends it as failed, and cancelling removes everything it made; after a crash, half-built files are tidied and finished sentences are kept for Resume.
- Custom voices keep a faint, steady room tone through pauses instead of dropping to dead silence, never louder than the background just before the pause.
- Numbers in brackets, such as array[3] or [0, 1], are read as written; superscripts in equations are no longer taken for footnote markers.
- Reading progress reaches 100 % at the last sentence that is read.
- Library cards no longer push the page sideways on phones.
- Importing a long studio recording, or a shared voice file larger than 25 MB, works again; before, the upload stopped with a general error.
- A file or request over the size limit is answered with a clear "too large" message instead of a general error.
- An audiobook whose title is a name Windows reserves for devices (such as NUL or CON) is exported under a usable file name.
- A paired phone's name is shown with visible characters only.

### Security

- **ONNX Runtime telemetry is now switched off.** Official ONNX Runtime builds send usage telemetry
  to Microsoft by default (Windows TraceLogging, or HTTPS on other platforms). TTSNative now sets
  `ORT_DISABLE_TELEMETRY` and calls `disable_telemetry_events()` before Kokoro loads, so the
  "no telemetry" promise holds.
- **certifi 2026.10.19** in the server and the Chatterbox worker, fixing GHSA-6q48-6c7w-9gw2. It is
  one day old, so it comes in through a documented exception to the 14-day release cool-down.
- **Pillow 13.0.0** in the Chatterbox worker, fixing nine advisories in 12.3.0 (one critical, six
  high). The worker never opens images, so none was reachable; the release is four days old and also
  comes in through a documented cool-down exception.
- The optional Chatterbox worker moved to torch 2.11, transformers 5.11 and setuptools 84, clearing
  its open advisories; the one remaining, in code the worker never calls, is documented in
  [docs/security/supply-chain.md](docs/security/supply-chain.md).
- Voice model files are checked before every use; a damaged file is named, and Repair downloads only that file again.
- The speech engine's built-in usage reporting is switched off, so TTSNative sends no usage data.
- Security updates for the optional voice-cloning engine.
- Requests passed on by a proxy, tunnel or port forward are refused, and only a page opened as localhost or 127.0.0.1 counts as the person at this computer.
- A paired phone works only from the address it paired from and for 30 days at most (14 days unused); paired devices reach only an explicit list of features, and phone access turns itself off when the computer's network changes or after it slept.
- On Windows, phones can connect only on a network marked private; on macOS and Linux you confirm each time that it's a home network you trust.
- Other programs' use of the voices is off by default, needs a token shown once and stored only as a hash, refuses web pages, and has limits on length, size, rate and time per request.
- The switch the automated tests use to look inside the Windows app's window is no longer built into released versions, and a release can't be built with it.
- Security update for the optional voice-cloning engine.
- A request that reaches the computer's own address from another device is refused outright unless network mode is on; phones and tablets come in through LAN mode.

### Technical

- Web: features/music (Web Audio engine with fades, crossfades and sample-accurate loops; a session that follows PlaybackController; per-device `ltts.music` preference), features/mixer (audio mixer in PlayerBar: narration volume `ltts.narrationVolume`, music channel, room for sound effects), `PlaybackController.setVolume` and `state.volume`, lib/deviceSettings, ADR-18 and docs/architecture/background-music.md.
- Player: a sentence that plays to its end no longer reports a brief pause (the `pause` fired just before `ended` is ignored); the music, play button and lock-screen state all follow that status between sentences.
- 11 CC0/public-domain tracks as Opus/WebM loops in apps/web/public/music (13.3 MB) with CREDITS.md; library.json records sources, licences, edits and SHA-256; `npm run music:build` rebuilds them from the checked originals.
- Tests: engine, session, preferences, library-licence and UI tests; tests/e2e/music.spec.ts.
- Server: migration 14 (`folders`, `document_shelf`, `document_genres`, `document_tags`, `collections`, `collection_documents`; `CREATE TABLE IF NOT EXISTS` so parallel branches merge in any order), `documents/shelf.py`, `folders.py`, `collections.py`, `shelf_router.py` (`/api/library/*`, `PUT /api/documents/{id}/shelf`), library summaries carry `author`, `hasCover` and `shelf`; paired LAN devices may use `/api/library`.
- Verse: the `line` boundary (`structures.Boundary`, `audio.PAUSE_SECONDS`, `SegmentOut`), set by `html_text.BlockBuilder` for `<br>` inside a paragraph and carried by the HTML page extractor, the segmenter and the read-along EPUB export (`<br/>`). It applies to documents imported from now on; existing documents keep their sentence numbering, so bookmarks, styling and progress are untouched.
- Migrations 14–16 belong to this branch (1–13 are main's); the sound-effects branch takes 17 next (`docs/architecture/literary-library.md` section 2). `tests/test_db_migrations.py` upgrades databases at versions 1, 5 and 13.
- Web: `api/libraryQueries.ts`, `features/library/{LibraryRail,LibraryFilters,OrganizeDialogs,RailDialogs,views,vocabulary}`, the reader draws `<br>` after a `line` boundary. ADR-24 and ADR-25; `docs/architecture/literary-library.md`.
- Catalog: package data in `ltts/library/` (`catalog.json`, 25 text-only EPUBs, 22 covers, `CREDITS.md`, about 4 MB) checked against recorded SHA-256 hashes at load and built by `scripts/library/build_catalog.py` from `scripts/library/sources.json`; migration 15 (`bundled_documents`, `hidden_works`); `GET /api/library/works`, `POST …/{work_id}/open`, `GET …/{work_id}/cover`, `PUT …/{work_id}/hidden`, `GET …/credits`; `features/explore/`.
- Presets: `ltts/library/presets.py` (schema `ttsnative.immersive-preset/1`, 16-hex sentence-hash anchors shared with the sound-effects work, frozen music track ids), six presets in `ltts/library/presets/`, migration 16 (`document_presets`), the `speaker` sentence annotation kind the planner reads as a tagged line, `GET|DELETE /api/documents/{id}/preset` and `POST …/preset/apply`; `api/presetQueries.ts`, `features/reader/ReadingExperience.tsx`; `scripts/library/anchor_tool.py` prints anchors for writing presets.
- These features merged to main after 2.0.0 and are described for developers under Unreleased in CHANGELOG.md; this file carries them into the next release's notes and version.
- Server: an OpenAI-compatible local speech API under `/v1` (`POST /v1/audio/speech`, `GET /v1/models`, `GET /v1/voices`; `speech_api_*` settings); LAN mode (`lan/`: a second listener on one private address, pairing codes, device cookies, `lan/policy.py` allow-list, per-device limits, Windows network-category check); `SecurityMiddleware` refuses forwarding headers, loopback requests under a non-loopback Host, and changes without a loopback `Origin`; new routers for styling, document details, integrations (Audiobookshelf, encrypted `SecretStore`), speech API settings and LAN.
- Exports: resumable per-sentence working folders, an export queue (one running, four waiting) with disk-space checks, M4B and read-along EPUB 3 (ffmpeg), Audiobookshelf upload; `JobStatus.PAUSED`.
- Documents: HTML, FB2 and MOBI extractors, pinned web-page import, running-header/footnote/citation cleanup, speech marks (`{pause}`, `{voice}`, `{effect}`, `{style}`, `{sound}`, `{say}`), spoken-word counts; sentence styling, casting and document-scoped pronunciation rules.
- Voices: speaking styles with a kept previous expression, voice blends (`blend:` prefix), `.ttsvoice` sharing and preview (docs/reference/ttsvoice-format.md), fine-tuning (`voices/tuning.py`, ADR-16), smarter take checks and tiers; `ltts voice-ab` and `ltts voice-panel` for blind listening tests; worker engine revision `worker-5` (seeds, retries, polish and styles, then steady capped room tone; temperature 0.7, top-k 600 for Steady).
- Web: `public/sw.js` (app shell only, never `/api` or `/v1`) with a web app manifest, `ConnectionBanner`, an Exports page, LAN and speech API settings, high-contrast and forced-colours styles; `npm run start` reads `LTTS_API_PORT`; the website build adds a content security policy.
- Docs: ADR-11 to ADR-17, guides for the local speech API and the phone checklist, research notes (studio voice audit, engine comparison, voice quality, LAN HTTPS options), threat-model rows.
- `synthesis/english.py`: bounded regular-expression rewrites applied to English voices of every engine after the pronunciation dictionary, skipped for sentences that look like code or a formula; times, years and digit-by-digit numbers need context; idempotent. The spoken text is part of the audio cache key, so the sentences it changes render again once. 219 rule cases and path tests (dictionary precedence, written text and subtitles unchanged, playback, export, regeneration, preview and speech API saying the same words).
- `VoiceInfo.attribution` on the voices API; web types regenerated.
- `tests/perf/narration_benchmark.py` and `narration_corpus.json`: thirteen held-out passages read through the real synthesis path; cold and warm starts, memory, GPU and signal measurements with a recorded environment; refuses to write audio where Git would track it; blind listening packs.
- `tests/perf/g2p_compare.py` and `g2p_corpus.json`: a blind espeak-ng versus misaki comparison with catch trials, confidence intervals and a pre-registered decision rule (misaki is not installed in the app). Narrator programme proposal in `docs/legal/narrator-programme.md`. Research and proposals in `docs/research/voice-library.md`; `ltts voice-panel score --pair A,B` pairs voice ids that contain colons.
- Chatterbox worker: virtualenv 21.14.7 for CVE-2026-113725 (security exception; unreachable, as virtualenv is never run).
- uv 0.13.4 (security exception for GHSA-hq85-5cpj-mr62: a compromised root CA removed from uv's bundled store), verified against the published checksums; the installer bundles it.
- apps/desktop: Tauri 2 shell (single instance, window state, navigation allowlist, kill-on-close Job Object for the server, loopback port from 8770), splash screen and per-user NSIS installer with hooks; runtime assembled by scripts/desktop/build-runtime.mjs (python-build-standalone 3.12 via the pinned uv, hash-checked server packages, byte-compiled, Kokoro bundled); `npm run desktop:build`.
- Signed updates with tauri-plugin-updater (minisign) from GitHub Releases `latest.json`; Authenticode signing hooks ready for when a certificate exists.
- Server: `ltts serve --exit-with-stdin`, `LTTS_BUNDLED_MODELS_DIR` (read-only models, repair copies intact files), `LTTS_WORKER_PROJECT_DIR`, `LTTS_UV_PYTHON_DIR`, and no console windows for helper processes on Windows.
- Release tooling: change files (.changes/), `npm run change`, `release:status`, `release:prepare`, check-changes in CI, user-facing notes in docs/releases/ (backfilled for 1.0.0 and 2.0.0), build identifiers for development builds, and version files listed once (scripts/lib/version-files.mjs).
- Web: update notice, release history and What's new in Settings → About; website download and release history pages generated from docs/releases.
- Dependency updates past the 14-day cool-down, replacing Dependabot's proposals: tauri-plugin-updater 2.13.2 (Windows app), fastapi 0.142.4 (server), and the development tools @playwright/test 1.64.0 and knip 6.40.0. Held until 2026-10-29: github/codeql-action v4.39.0 (released 2026-10-15).
- Website build: one page per release (`releases/<version>/`, plus `releases/` for the latest), a title and canonical address per version, `%LATEST_*%` placeholders behind an `if:release` block, and a link check that follows the base URL into folders.
- apps/desktop: a `test-hooks` Cargo feature gates `--remote-debugging-port=N`; `build.mjs` compiles it only with `TTSNATIVE_TEST_HOOKS=1`, refuses it for a release version, and checks the binary for the switch text either way (`scripts/desktop/check-test-hooks.mjs`); the Desktop workflow sets it for its installer and update builds and checks a plain release build; release.yml leaves it unset. The app drops `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` from its environment at start.
- release.yml fails closed: the `release` environment must exist with a required reviewer, and both signing secrets must be present.
- Dependabot: a cargo entry for the Windows shell with a 14-day cool-down; `glib` (Linux-only, not compiled for Windows) is ignored so its security-update job stops failing.
- Chatterbox worker: virtualenv 21.14.10 for CVE-2026-113716, -113722 and -113724 (security exception; virtualenv is never run). Only virtualenv changes in the lock.
- The Windows app test checklist covers the release history one version at a time and the sidebar version link; the website's phone test covers the release history pages as well as the home page.
- CONTRIBUTING.md states the cross-surface consistency rule (app, website, documentation and release information change together), and the pull request template asks for it.
- The server tests run in parallel with pytest-xdist (one worker per CPU, at most eight; `-n 0` runs them serially, and `npm run test:inference` always does), taking well under half as long. Tests made deterministic for it: two parametrized cases named by zip bytes that embed the build time; the idle-unload test, which now waits for the watcher to release the worker lock; the speech API's log-secrets test, which now checks what the log handler writes (at debug and normal levels, with tests proving it catches a leaked token or text) instead of each record's clock and thread numbers; and two CLI tests that left the app's logging setup in place for later tests.
- CI runs the web unit tests in their own job beside the web checks, and Validate requires it.
- Desktop workflow: the installer and update-path jobs no longer wait for the shell checks; the installer job saves the Cargo and runtime caches right after its build (so a failing test still leaves them warm) and the update job only restores them; a lockfile change starts from the newest cache for the same toolchain; the Cargo cache leaves out the copied runtime and the built installer.
- Every CI and Desktop job has a timeout well above its real run time (30 minutes for CI jobs and the desktop shell checks, 45 for the installer job, 60 for the update path), so a hung job fails instead of running for GitHub's six-hour default.
- Website: a `<!-- if:released-X.Y.Z -->` block for a version that has no notes yet (the next release, before `release:prepare`) was left in place because no flag existed for it; such blocks are now dropped, so the published site never shows a card for an unreleased version.
- Website: a "Background music" feature card, gated on `<!-- if:released-2.1.0 -->`, so it stays out of the published site until GitHub lists 2.1.0 as released and appears on release day by itself. Local builds show it.
- Website: `<!-- if:released-X.Y.Z -->` blocks in `site/index.html` stay out of the published site until GitHub lists that version as a released version (`scripts/site/releases.mjs` `releasedFlags`), so a feature card can merge with its feature and appear on release day by itself. Local builds show them.
- The voice library report (`docs/research/voice-library.md`) now matches what was merged in #45: the narrowed English reading rules, the benchmark method (cold and warm starts, recorded environment, privacy) with the second run's measurements, the blind listening packs, the misaki decision rule fixed before listening, and a link to the narrator programme proposal. It no longer describes clips as heard, or Kokoro's run-to-run differences as inaudible: nobody has listened yet. The benchmark's README says the same.
- `SecurityMiddleware` applies per-route body caps (`ROUTE_BODY_CAPS`: voice-session import 600 MB, voice-profile import and preview 40 MB) above the general `max_upload_mb` and records a cut-off body in `scope["state"]` (`BODY_TOO_LARGE`), which the HTTP error handler answers with 413 `payload_too_large`; `_check_here` refuses non-loopback clients when `allow_network` is off; `safe_filename` suffixes Windows reserved device names; `plain_text` moves to `ltts.common` and is applied to paired device names.
- `npm run release:amend` folds change files that landed after a release was prepared into that version while it has no tag: `amendNotes` (releases.mjs) and `amendRelease` (changelog.mjs) append their entries to the matching sections of `docs/releases/X.Y.Z.md` and the `[X.Y.Z]` CHANGELOG entry, the change files are deleted and the version stays. `check-changes.mjs` accepts such an amendment pull request (same version, change files consumed and none added, none left, notes and entry in place, version untagged).

## [2.0.0] - 2026-10-19

A complete rebuild. v1 was a single Gradio script; v2 is a local-first document reader and voice
studio with a React UI and a hardened Python service. Nothing from v1 is required to upgrade — start
fresh with `npm install && npm run dev`.

### Added

- **Reader:** upload PDF, DOCX, EPUB, Markdown or TXT (or paste text), read along with sentence
  highlighting, navigate chapters/pages, resume where you left off, keyboard shortcuts and lock-screen
  media controls.
- **Progressive playback:** sentences are generated just ahead of the listener and cached, so long
  books start playing in about a second.
- **Voice Library:** 54 Kokoro voices with language, gender and upstream quality grades; compare voices
  on the same passage.
- **Voice Studio:** create a voice from a 10–20 s recording or an imported clip with live quality checks,
  explicit consent, a test generation, and permanent deletion (optional Chatterbox Turbo engine).
- **Export:** WAV or MP3, whole document or a chapter range, single file or one file per chapter with a
  playlist; interrupted exports resume using cached audio.
- **Settings:** theme, playback defaults, engine install/remove with sizes and hardware advice, storage
  usage and cache clearing, privacy summary, diagnostics and version information.
- **Engine updates:** when the voice-cloning worker's locked packages change (for example a security
  fix), existing installs show **Update available** and update in place with one click instead of a
  remove and reinstall.
- **One-command setup:** `npm run dev` provisions a checksum-verified `uv`, an isolated Python 3.12
  environment and the default voice model, then starts the API and UI together.
- Security hardening: loopback binding, Host/CSRF/cross-site checks, CSP, sandboxed document parsing,
  archive/XML attack defences, upload and processing limits, pinned and SHA-256-verified model downloads.
- Tests (pytest, Vitest, Playwright with real inference), CI workflows, documentation and license inventory.
- Releases: pushing a version tag checks it against the app version and this changelog, runs the full
  check suite, and publishes the source, the prebuilt web UI, CycloneDX SBOMs and `SHA256SUMS.txt`
  with signed build provenance.
- A user guide in the [wiki](https://github.com/carsonmcrae/local-tts-web-ui/wiki), kept in
  `docs/wiki/` and published automatically.
- A demo video recorded from the running app with its real narration, and a short showcase video whose
  voice-over is spoken by Local TTS (`docs/media/`, reproducible with `npm run media:demo` and
  `npm run media:promo`).
- Community files: code of conduct, support guide, issue labels and release-note categories.

### Changed

- Kokoro now runs in-process through `kokoro-onnx` 0.6 with the official v1.1 ONNX export instead of
  spawning the `kokoro-tts` CLI for every request.

### Removed

- Gradio UI, the "Text Prompts" folder workflow and batch mode (replaced by the library and export).
- AGPL-licensed transitive dependencies (PyMuPDF, EbookLib).

### Fixed

- PDFs without an outline produced no audio and no error in v1; text PDFs now always extract, and
  scanned PDFs are reported clearly.

## [1.0.0] - 2025

Initial Gradio prototype (`kokoro_tts_ui.py`), tagged `v1.0.0` at commit `1452251`. See
[docs/architecture/legacy-audit.md](docs/architecture/legacy-audit.md).

[2.2.0]: https://github.com/carsonmcrae/ttsnative/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/carsonmcrae/ttsnative/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/carsonmcrae/ttsnative/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/carsonmcrae/ttsnative/tree/v1.0.0

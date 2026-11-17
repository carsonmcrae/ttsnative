# Windows distribution: the Microsoft Store and the direct download

Why TTSNative ships two ways on Windows, what each needs, and where the work stands. The decision is
[ADR-26](../architecture/decisions.md#adr-26-windows-ships-through-the-microsoft-store-with-a-signpath-signed-direct-download-beside-it).

## What people see today (unsigned)

Checked with 2.1.0 on a clean Windows 11 VM on 2026-10-23, downloading from ttsnative.com in Edge:

1. Edge holds the download: "TTSNative-Setup-2.1.0.exe isn't commonly downloaded". The way on is
   **⋯ → Keep**, then a second screen ("Publisher: Unknown") whose main button is **Delete**; **Keep
   anyway** is behind its arrow.
2. Run from a browser that doesn't check downloads itself, Windows shows "Windows protected your PC";
   the way on is **More info → Run anyway**.
3. Where Smart App Control is on, an unsigned app can't run at all.

The website's installation steps describe both screens.

## The two channels

|                 | Microsoft Store (main)                 | Direct download (alternative)                         |
| --------------- | -------------------------------------- | ----------------------------------------------------- |
| Package         | MSIX, re-signed by Microsoft           | NSIS installer, no Authenticode signature             |
| Warnings        | None (Store installs skip SmartScreen) | Edge and SmartScreen, as above                        |
| Publisher shown | Carson McRae                           | Unknown                                               |
| Updates         | The Store                              | The app's own updater (GitHub Releases, minisign key) |
| Cost            | Free                                   | Free                                                  |

Both packages hold the same program and runtime from the same build. Both keep the user's files in
`%LOCALAPPDATA%\com.ttsnative.desktop`, so someone can switch from one to the other without losing
their library.

## Signing the direct download

SignPath Foundation declined the application on 2026-10-24: its free certificates go to open-source
projects that already show public adoption (stars, forks, contributors, articles, independent
discussion, sustained activity), and it invited a new application once TTSNative has that. Its paid
subscription, Azure Artifact Signing and OV certificates all cost money every month or year, and all
still warn until a file builds a reputation, so the direct download stays unsigned for now and the
website leads with the Store once the listing is live. Reapply to SignPath when the project has a
visible following; the plan for signing in `release.yml` (sign `TTSNative.exe`, bundle, sign the
installer, then make the update signature over the signed installer, and sign the uninstaller too)
is in ADR-26.

## How the Store package is built

- `scripts/desktop/msix.mjs` lays out the installed program (`TTSNative.exe`, `runtime\`), writes
  `AppxManifest.xml` from `tauri.conf.json` and `apps/desktop/store/identity.json`, generates the tile
  and Store logos from the app icon, and packs it with the Windows SDK's `makeappx`.
- **Every desktop change:** the Desktop workflow's "Microsoft Store package (MSIX)" job builds it as a
  development version (`X.Y.Z.0` of the next release) and keeps it for 14 days.
- **Every release:** the Release workflow's "Microsoft Store package (MSIX)" job builds
  `TTSNative-X.Y.Z.msix` from the tag and keeps it for 30 days as the `ttsnative-store-package`
  artifact. It never goes on the GitHub release: an unsigned MSIX can't be installed, and the Store
  signs what it distributes.
- **Full trust, Windows 11:** `runFullTrust`, minimum version 10.0.22000.0. WebView2 is part of
  Windows 11.
- **User folder:** excluded from MSIX file-system virtualisation (`unvirtualizedResources`), so it is
  the same folder the direct install uses and it survives an uninstall; **Settings → About → Delete my
  data…** removes it.
- **No updater:** the Store build is compiled with the `store` feature. The updater plugin isn't
  registered, the web UI says the Store keeps TTSNative up to date, and nothing reaches GitHub.
- **No pointers to removed signatures:** the Store signs every program and library in the package and
  rejects the whole package (0x800700C1) when one still points at a signature that was cut off it, as
  python-build-standalone's `zlib1.dll` does. The packaging step clears such a pointer in the
  package's copy and says which files it changed; the direct-download runtime is left as upstream
  ships it.

## What is different inside a Store package

A Store install runs the same server and web app as the direct install, in a package. Three
differences have already broken something, so anything that starts another program or loads a library
is checked against them:

- **Windows doesn't search `PATH` for DLLs** in a packaged app, nor in the programs it starts. A
  library is found next to the program that loads it, in a folder added with `AddDllDirectory`, or
  when it is already loaded. The voice-cloning worker loads the app's Visual C++ runtime by full path
  for this reason.
- **Each version is installed in a new folder** (`…\WindowsApps\CarsonMcRae.TTSNative_X.Y.Z.0_x64__…`),
  and the folder is read-only. Nothing may keep a path into it across an update; the worker's source
  folder is named each time the worker starts.
- **New folders under `%LOCALAPPDATA%` are redirected** to the package's own storage, except the
  user folder the manifest excludes. uv's download cache lands in the redirected place; the engine
  and the Python it runs on are in the user folder.

A PC can also refuse what the package downloads later: Windows in S mode, Smart App Control and
application-control policies run only approved software, and the voice-cloning engine (Python, PyTorch
and the model) arrives after install. TTSNative says so and offers a matched voice instead
([Voice Studio](../wiki/Voice-Studio.md#if-the-engine-cant-be-installed)).

## Submitting to the Store (the owner's part)

1. **The package:** after a release, open its run (Actions → Release), download the
   `ttsnative-store-package` artifact and unzip it: `TTSNative-X.Y.Z.msix` with the Partner Center
   identity. Check it against the `.sha256` file beside it.
2. **Partner Center → Apps and games → TTSNative → Start your submission.**
3. **Pricing and availability:** free, all markets, public audience, discoverable. This page can't be
   changed once a submission has been sent, even after it fails: to change the audience, delete the
   draft and start a new submission (the age rating and the notes for certification are kept; the
   package, listing and logos are entered again). A private audience can't be chosen after a public
   release.
4. **Properties:** category Productivity; the app accesses personal information, with the privacy
   policy at `https://github.com/carsonmcrae/ttsnative/wiki/Privacy-and-Security`; website
   `https://ttsnative.com`; support contact `https://github.com/carsonmcrae/ttsnative/issues`; Windows
   11, 64-bit, about 1.5 GB of disk. Declare that the app uses generative AI.
5. **Age ratings:** answer the questionnaire as it applies. TTSNative has no chat or social features;
   it imports web pages from addresses the user types and can send books to the user's own
   Audiobookshelf server.
6. **Packages:** upload `TTSNative-X.Y.Z.msix`; device family Desktop.
7. **Store listing (English):** check every line against the release's notes before pasting.
   - **Short description:** Private text-to-speech: your documents read aloud with natural voices,
     entirely on your own PC.
   - **Description:**

     > TTSNative reads your documents aloud with natural voices, right on your own PC. Open a PDF, Word
     > document, EPUB, Kindle (MOBI), FB2, HTML, Markdown or plain-text file, or import a web page, and
     > TTSNative reads it with natural neural voices, highlighting each sentence as it speaks. Your
     > place is saved, so you pick up exactly where you left off.
     >
     > Everything happens on your computer: no account, no subscription, no telemetry and no cloud.
     > The default voices come with the app and work offline.
     >
     > Voice Studio is optional: it creates a narration voice from your own recording, with the
     > speaker's consent. Cloning a voice downloads an extra speech engine (about 4 GB, or 8 GB with
     > an NVIDIA GPU) only when you turn it on, and needs a PC and a network that allow that download.
     > Where they don't, as on Windows in S mode, TTSNative says so and can make a matched voice
     > instead: a stand-in mixed from its own voices at the pitch of your recording.
     >
     > TTSNative is free and open source under the MIT licence: github.com/carsonmcrae/ttsnative

   - **Product features** (one per box): natural voices in eight languages; the sentence being spoken
     highlighted and kept in view; MP3 and WAV export, whole documents or chapters, with optional
     subtitles; public-domain classics included, some with a multi-voice cast; bookmarks, search, a
     pronunciation dictionary and a sleep timer; sound effects and background music, off until you
     turn them on; listening on a phone over the home Wi-Fi.
   - **Screenshots:** the library, the reader in light and in dark, the voices, Explore and Voice
     Studio (2880 × 1800), captured from the release with its version showing. Each upload box takes
     one file at a time.
   - **Store logos:** poster art 1440 × 2160, box art 2160 × 2160 and the app tile 300 × 300, made from
     the brand symbol on its gradient. The 150 × 150 and 71 × 71 boxes stay empty.
   - **Search terms:** text to speech, read aloud, TTS, PDF reader, audiobook, accessibility, offline
     voices. The box keeps a term only once you click away from it: click an empty part of the page
     before **Save**, then reload and check they are still there.
   - **Saving:** a page has saved when it returns to the overview.
8. **Submission options → restricted capabilities:**
   - **runFullTrust:** TTSNative is a desktop app (Tauri with a bundled Python runtime) that starts its
     local speech server as a child process listening only on this computer.
   - **unvirtualizedResources:** TTSNative keeps the user's library (imported documents, custom voices
     and recordings, exports) in `%LOCALAPPDATA%\com.ttsnative.desktop`, the folder the
     direct-download version also uses. Excluding only that folder keeps a person's documents and
     voices when they reinstall or switch versions; **Settings → About → Delete my data…** removes it.
9. **Notes for certification** (Supplemental info → Additional testing information; kept between
   submissions):

   > No account or sign-in is needed. To try TTSNative: open the app, choose Try a sample on the
   > Library page, then press Play. The default voices are in the package and work offline.
   >
   > Voice Studio is optional. Voice Studio → Create voice → Quick voice records a short clip with
   > the speaker's consent. Cloning it needs an engine that is downloaded only when the user presses
   > Install: Python packages and model files (about 3.4 GB) from pinned, checksum-verified addresses
   > at pypi.org, files.pythonhosted.org, download.pytorch.org, github.com and huggingface.co. If the
   > test PC or its network doesn't allow that download (Windows in S mode, Smart App Control or
   > another application-control policy, a firewall or a filtering proxy), the app says which of
   > these stopped it. The same screen then offers Create matched voice, which needs no download and
   > works on every PC: it mixes two built-in voices at the pitch of the recording.
   >
   > TTSNative starts its local speech server as a child process. The server listens only on this
   > computer unless the user turns on access for phones in Settings.

10. **When the listing is live:** set `"listed": true` in `apps/desktop/store/identity.json` (in a pull
    request). The website then leads with **Get TTSNative from the Microsoft Store** and keeps the
    installer as the alternative.

## Testing the Store build before it is submitted

Microsoft's review takes days and reports one screenshot, so the package is tried as a Store install
first. Neither failed submission below would have reached Microsoft with these checks.

1. **On a development PC, in a package's context** (no Developer Mode needed). Windows can start any
   program with the identity of an installed packaged app:

   ```powershell
   Invoke-CommandInDesktopPackage -PackageFamilyName Microsoft.WindowsTerminal_8wekyb3d8bbwe `
     -AppId App -Command <program> -Args '<arguments>' -PreventBreakaway
   ```

   The program and everything it starts then run as a packaged app does: no `PATH` search for DLLs,
   and new folders under `%LOCALAPPDATA%` redirected. It returns at once and shows no output, so the
   program writes a log. Run this way on 2026-11-17 (Windows 11 26200, the bundled Python from the
   2.2.0 runtime, this version's server and worker): the engine installed from nothing with the
   worker project in a read-only folder under a `Program Files\WindowsApps\…` path, a fresh
   redirected uv cache and a fresh Python download; the worker loaded the app's Visual C++ runtime;
   a cloned voice and a matched voice spoke; and the cloned voice still spoke after the app's folder
   was renamed to the next version's.

2. **On the clean VM, as a real install** (still to do for every Store submission): sign the release's
   MSIX with a test certificate, trust that certificate in the VM only, install the package, then
   run through the notes for certification as the reviewer would, including installing the
   voice-cloning engine and making a matched voice. The VM has no Visual C++ redistributable and no
   developer tools, which is what the review's PCs are like.
3. **What can't be tried here:** Microsoft's own PCs and network. If the engine can't be installed
   there, the reviewer now sees which limit stopped it and can make a matched voice.

## Open questions

- **Which limit stopped the 2.2.0 review's install.** The screenshot showed only that the runtime
  install failed. From the next version the message names the cause.
- **Windows in S mode.** Microsoft's packaging guidance asks Store apps to run there. TTSNative's
  reader does; the voice-cloning engine can't (S mode runs nothing downloaded after install) and says
  so. **Delete my data…** starts `cmd.exe`, which S mode also refuses; it needs another way to remove
  the folders after the app has closed.
- **LAN access in the Store build.** A full-trust package can listen on the network; check whether
  Windows' firewall prompt appears as it does for the direct install.

## Status

- [x] Decision recorded (ADR-26).
- [x] Store account and reserved name (owner): `CarsonMcRae.TTSNative`, Store ID 9PP3BKBDJP9R,
      recorded in `apps/desktop/store/identity.json`.
- [x] `store` channel build (no updater) and the in-app data deletion (`npm run desktop:store`,
      Settings → About → Delete my data…).
- [x] MSIX packaging script, manifest and logos (`scripts/desktop/msix.mjs`, unit-tested).
- [x] CI builds the package on every desktop change and on every release.
- [x] Website: installation steps for both warnings; the Store button, shown once `listed` is true.
- [x] SignPath application (submitted 2026-10-23, declined 2026-10-24 pending wider adoption).
- [x] First submission of 2.2.0 (private audience, 2026-11-06): failed Microsoft's signing step with
      0x800700C1, a pointer to a removed signature in `zlib1.dll`. The package was repacked with that
      pointer cleared; the packaging step now does it.
- [x] Second submission of 2.2.0 (public, 2026-11-07): passed signing, failed certification on
      2026-11-12 (10.1.2.10, "Missing Functionality: Chatterbox Turbo Installation"). The engine's
      runtime install failed on the reviewer's PC for a reason the app didn't show. This version
      names the reason, retries what is worth retrying, fixes two faults that only a Store install
      has, and offers a matched voice.
- [ ] The package installed on the clean VM (step 2 above).
- [ ] The next submission (owner), then `listed: true`.

# Windows distribution: the Microsoft Store and the direct download

Why TTSNative ships two ways on Windows, what each needs, and where the work stands. The decision is
[ADR-26](../architecture/decisions.md#adr-26-windows-ships-through-the-microsoft-store-with-a-signpath-signed-direct-download-beside-it).

## What people see today (2.1.0, unsigned)

Checked on a clean Windows 11 VM on 2026-10-23, downloading from ttsnative.com in Edge:

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

## Submitting to the Store (the owner's part)

1. **The package:** after a release, open its run (Actions → Release), download the
   `ttsnative-store-package` artifact and unzip it: `TTSNative-X.Y.Z.msix` with the Partner Center
   identity. Check it against the `.sha256` file beside it.
2. **Partner Center → Apps and games → TTSNative → Start your submission.**
3. **Pricing and availability:** free, all markets, public (or a private audience for a first look).
4. **Properties:** category Productivity; privacy policy `https://ttsnative.com/#privacy`; website
   `https://ttsnative.com`; support contact `https://github.com/carsonmcrae/ttsnative/issues`; Windows
   11, 64-bit, about 1.5 GB of disk.
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
     > speaker's consent, and downloads an extra speech engine (about 4.5 GB, or 8 GB with an NVIDIA
     > GPU) only when you turn it on.
     >
     > TTSNative is free and open source under the MIT licence: github.com/carsonmcrae/ttsnative

   - **Product features** (one per line): natural voices in nine languages; the sentence being spoken
     highlighted and kept in view; MP3 and WAV export, whole documents or chapters, with optional
     subtitles; public-domain classics included, some with a multi-voice cast; bookmarks, search, a
     pronunciation dictionary and a sleep timer; listening on a phone over the home Wi-Fi.
   - **Screenshots:** `docs/images/library.png`, `reader-light.png`, `reader-dark.png`,
     `voices.png`, `explore.png`, `studio.png` and `settings.png` (2880 × 1800).
   - **Search terms:** text to speech, read aloud, TTS, PDF reader, audiobook, accessibility, offline
     voices.
8. **Submission options → restricted capabilities:**
   - **runFullTrust:** TTSNative is a desktop app (Tauri with a bundled Python runtime) that starts its
     local speech server as a child process listening only on this computer.
   - **unvirtualizedResources:** TTSNative keeps the user's library (imported documents, custom voices
     and recordings, exports) in `%LOCALAPPDATA%\com.ttsnative.desktop`, the folder the
     direct-download version also uses. Excluding only that folder keeps a person's documents and
     voices when they reinstall or switch versions; **Settings → About → Delete my data…** removes it.
9. **Notes for certification:** no account is needed. To try it: open TTSNative, choose **Try a
   sample**, then **Play**. The optional voice-cloning engine downloads Python packages and model
   weights from pinned, checksum-verified addresses only after the user turns it on and records
   consent; nothing else is downloaded.
10. **When the listing is live:** set `"listed": true` in `apps/desktop/store/identity.json` (in a pull
    request). The website then leads with **Get TTSNative from the Microsoft Store** and keeps the
    installer as the alternative.

## Open questions

- **Store certification of voice cloning.** The consent flow, the disclosure and the optional download
  are described in the listing and the notes; certification may still ask questions.
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
- [ ] The package installed on the clean VM.
- [ ] First Store submission (owner), then `listed: true`.

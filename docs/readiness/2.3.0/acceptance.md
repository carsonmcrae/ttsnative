# Acceptance: 2.3.0

The release candidate is built from this release branch. This file records actual observations;
unticked items are outstanding, not assumed to pass. A matched voice is a pitch-matched mix of built-in
voices, not a copy of the speaker. Quick/imported profiles keep their original recording and can use
it as a cloned voice after the optional engine is installed. Guided studio builds still need the engine.

## Before release

- [ ] (required) **Clean Store install.** Preserve the current VirtualBox VM state, restore its clean
      Windows 11 baseline, trust a test signing certificate in the guest only, install the candidate
      MSIX and launch from Start. No Visual C++ redistributable or developer tools are installed.
- [ ] (required) **Bundled reading.** Import a document, play several sentences and export an MP3 in
      the installed Store app with the optional engine absent. Repeat reading without a network.
- [ ] (required) **Matched voice without a download.** Save a quick/imported voice, create its matched
      voice, play a sample, select it for reading, close and reopen. It remains usable without
      Chatterbox; the interface explains that it is a stand-in and that cloning is optional.
- [ ] (required) **Clone later from the saved recording.** Install Chatterbox in the packaged app,
      select the original saved voice, generate speech, close and reopen, and generate again. The
      matched blend remains available; no new recording is needed. Record timings and any failures.
- [ ] **Packaged update.** Verify the original cloned voice after a Store-version folder change.
      Unit coverage and the earlier package-context experiment are supporting evidence, not a
      replacement for an installed-package observation.
- [ ] **Release candidate checks.** CI, Desktop, CodeQL and Inference & E2E pass on the final candidate.
      The local full check, both 100% coverage gates, security audits and real-model tests are recorded
      in the pull request.

## After publishing

- [ ] (required) **The real signed update.** The published 2.2.0 direct-download app offers 2.3.0,
      verifies its signature, installs after consent and reopens with the user's data kept.
- [ ] (required) **The download.** The website serves the 2.3.0 installer; its hash matches the release
      manifest and it installs on the clean Windows machine.
- [ ] **Website and release notes.** The footer, download and release pages name 2.3.0 and describe
      matched voices accurately.

## Blockers

- [x] Restore desktop control for the existing clean VM. — verified: 2026-11-17, desktop control
      started after the maintainer unplugged the SanDisk USB device with an unreadable partition.
      Preserved the VM's original state as snapshot `34d3a3c1-6b10-4569-adf5-35c8a8aa4f99`, restored
      clean baseline `e393553b-8545-4210-b305-d180bd01e1a1`, and installed the test-signed candidate.
- [ ] Complete and record the before-release observations above. A successful MSIX build alone does
      not establish that Microsoft's reviewer can use optional cloning or the matched path.
      The first VM pass found paused local requests when offline and a Python-probe import failure
      during optional engine setup. Both require a rebuilt package and actual VM retests.
- [ ] Complete the still-open required after-publishing evidence for 2.2.0 in its acceptance record.
      The release gate checks that record before permitting the next version.

## Initial candidate observations

2026-11-17, `TTSNative-Win11-Clean`, Windows 11 Home, standard `reader` account, four CPUs, 8 GB RAM,
no NVIDIA GPU, no developer tools or Visual C++ redistributable. This pass uses PR #108 source
`ab4915d067346382d63229fcd4c6ee2563429345`, built by Desktop run `44132859459` from its synthetic merge
`4456af1c46`. These observations do not mark the replacement candidate as tested.

- The original VM state is preserved. Installed the MSIX from the read-only `TTSN230TEST` disc after
  the maintainer trusted a temporary public test certificate in the guest. The VM clock was an hour
  behind; installation became available after the certificate's start time passed. The test-signed
  MSIX SHA-256 is `679ff2b5817bbe01ace4586e19b800da06ae2bcb7bb1846dbb548ce73cea96a4`.
- The app reached an empty Library with **Voices ready**, without a console. About identifies the
  candidate as `2.3.0-dev.11+codex-release-2-3-0.4456af1c46`, Python 3.12.14, CPU mode, and says the
  Microsoft Store keeps the app up to date.
- Imported `sample.pdf`; narration advanced through three sections with sentence highlighting.
  Exported the whole document as `sample.mp3` (87.2 KB in Downloads). Windows Media Player opened it
  and progressed from 0:06 elapsed with 0:10 remaining. Audio was not audibly assessed.
- Imported a generated Kokoro reference, `synthetic.wav` (12 seconds, 9.6 seconds detected speech),
  as quick voice `test`. No personal recording was used. Created `test (matched)` without Chatterbox,
  generated its sample, selected **Use for reading**, then narrated freshly imported `sample.docx`
  through both sections. The original `test` profile remained **Not installed** in the voice picker.
- Closed the app and relaunched it from Start. The documents, original recording and selected matched
  voice survived. After the optional setup failed, freshly imported `sample.epub` still narrated both
  sections using `test (matched)`; the original profile was still **Not installed**.
- Disconnected the VM's virtual network cable and navigated to Library: three loading placeholders
  remained for more than 20 seconds. Reconnecting the cable resumed the request. TanStack Query's
  default network mode had paused same-origin local requests. Unit and real-browser regressions
  reproduce this failure; the physical cable test remains outstanding on the rebuilt MSIX.
- Optional CPU installation downloaded managed Python 3.11.17, then failed its interpreter probe with
  `ModuleNotFoundError: No module named 'python'`. Preserved the complete 683-byte `server.log` in
  the VM's Downloads folder before any restart. The app displayed the failure and retained the
  matched fallback. The replacement routes uv's cache into the existing unvirtualized app folder;
  installing the engine and cloning from the saved recording remain unverified until that build runs.

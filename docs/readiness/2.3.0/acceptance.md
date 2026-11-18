# Acceptance: 2.3.0

TTSNative 2.3.0 was published from `eaf4b05` on 2026-11-18. This file records actual observations;
unticked items are outstanding, not assumed to pass. A matched voice is a pitch-matched mix of built-in
voices, not a copy of the speaker. Quick/imported profiles keep their original recording and can use
it as a cloned voice after the optional engine is installed. Guided studio builds still need the engine.

Observations identify the source and package they actually exercised. Earlier clean-install and
cloning results retain their original scope; they are not renamed as tests of the agent amendment.
The amendment's installed Windows 11 observations are recorded separately below. Every required
workflow must also pass on the exact commit proposed for release.

## Before release

- [x] (required) **Local agent integration.** Verify discovery, opening and narration in the existing
      reader, a real MP3 export, missing prerequisites, output protection and the standalone skill
      package. Record installed Windows and source observations separately from mocks.
      — verified: 2026-11-18 UTC, amended source `7ca64f4`, test revision `2.3.0.8` on the preserved
      Windows 11 Store VM, standard `reader`, with the virtual network cable disconnected. The exact
      packaged skill cold-launched the installed app, discovered agent protocol 1, rejected missing
      and bad credentials and browser-origin access, imported synthetic text and acknowledged real
      playback. Highlights advanced and narration finished; a 54,872-byte MP3 was saved. Real missing
      prerequisites and existing-output preservation passed. Package hashes and limits are below.
      The exact-head workflow and release-gate checks remain separate requirements after this
      evidence is committed; this item does not claim a future commit has passed.
- [x] (required) **Clean Store install.** Preserve the current VirtualBox VM state, restore its clean
      Windows 11 baseline, trust a test signing certificate in the guest only, install the candidate
      MSIX and launch from Start. No Visual C++ redistributable or developer tools are installed.
      — verified: 2026-11-17, `TTSNative-Win11-Clean` restored to baseline `e393553b`, standard
      `reader` account. The maintainer imported the public test certificate in the guest; the rebuilt
      `2.3.0.1` MSIX installed and launched with the virtual network cable disconnected. The empty
      Library and **Voices ready** appeared without a console. Package identity and hashes are below.
- [x] (required) **Bundled reading.** Import a document, play several sentences and export an MP3 in
      the installed Store app with the optional engine absent. Repeat reading without a network.
      — verified: 2026-11-17, the same rebuilt MSIX and clean VM, with the cable disconnected and
      Chatterbox absent. A fresh TXT import narrated three sentences to 100%; its MP3 downloaded
      locally and Windows Media Player advanced through it. Audio was not audibly assessed.
- [x] (required) **Matched voice without a download.** Save a quick/imported voice, create its matched
      voice, play a sample, select it for reading, close and reopen. It remains usable without
      Chatterbox; the interface explains that it is a stand-in and that cloning is optional.
      — verified: 2026-11-17, the same rebuilt MSIX and clean VM, with the cable disconnected and
      Chatterbox absent. Imported a generated Kokoro WAV, saved `test`, made and previewed
      `test (matched)`, selected it for reading and narrated a fresh DOCX through both sections.
      After closing and reopening from Start, the documents and matched voice survived; a fresh
      EPUB narrated both sections with that voice. The original profile remained **Not installed**.
      No personal recording was used; playback progression was observed, not audible quality.
- [x] (required) **Clone later from the saved recording.** Install Chatterbox in the packaged app,
      select the original saved voice, generate speech, close and reopen, and generate again. The
      matched blend remains available; no new recording is needed. Record timings and any failures.
      — verified: 2026-11-17, source `3f1fb3d`, final CI payload in test revision `2.3.0.6` on the
      SSD-backed Windows 11 VM, four CPUs and 8 GB RAM, without an additional system redistributable.
      The packaged CPU installation verified in `.5` remained ready. Selected original profile
      `test`, kept separately from `test (matched)`, and generated fresh speech for a new 31-byte TXT.
      Closed and reopened from Start: five documents survived. A different, never-read 37-byte TXT
      generated and played with the original profile after restart, reaching 0:02 elapsed and 0:00
      remaining with the Play button returned and no error, observed within 250 seconds of Play.
      The saved synthetic recording was reused and the matched blend remained available. The
      single-sentence position label stayed at 0%; audio was not audibly assessed. Details are below.
- [x] **Packaged update.** Verify the original cloned voice after a Store-version folder change.
      Unit coverage and the earlier package-context experiment are supporting evidence, not a
      replacement for an installed-package observation.
      — verified: 2026-11-17, App Installer recognized the exact publisher and enabled **Update**
      from test revision `2.3.0.6` to `2.3.0.7`. The update installed and launched automatically,
      retaining six documents. Original profile `test` stayed selected and `test (matched)` remained
      ready separately. A never-read 37-byte TXT generated and played cloned speech to its end within
      112 seconds of Play, with 0:02 elapsed, 0:00 remaining, Play returned and no error. The
      single-sentence position label remained 0%; audio was not audibly assessed. Details are below.
- [x] **Release candidate checks.** CI, Desktop, CodeQL and Inference & E2E pass on the final candidate.
      The local full check, both 100% coverage gates, security audits and real-model tests are recorded
      in the pull request.
      — verified: 2026-11-18 UTC, amended source `7ca64f4dfc6f1dec015126c66971506cb34ab34a`:
      [CI](https://github.com/carsonmcrae/ttsnative/actions/runs/44231131807),
      [Desktop](https://github.com/carsonmcrae/ttsnative/actions/runs/44231136648),
      [CodeQL](https://github.com/carsonmcrae/ttsnative/actions/runs/44231131837) and
      [Inference & E2E](https://github.com/carsonmcrae/ttsnative/actions/runs/44231140096) all passed.
      Scripts passed 152 tests and web passed 697; web/server line and branch coverage were 100%.
      Windows server CI passed 1,500 tests with one missing-ffmpeg skip; Linux/macOS each passed
      1,499 with that skip plus the Windows-only loader test. Inference passed 15 with three optional
      Chatterbox skips; browser E2E passed 81 with the existing WebKit music-join skip. Production
      audits and the worker audits with their existing reviewed exception passed. The following
      evidence commit must pass all four workflows and the gate itself; no future-head result is
      claimed here. The earlier Voice Studio CI baseline is retained below with its original scope.

## After publishing

- [x] (required) **The real signed update.** The published 2.2.0 direct-download app offers 2.3.0,
      verifies its signature, installs after consent and reopens with the user's data kept.
      — verified: 2026-11-18, Windows 11 Home, standard `reader`, preserved upgrade VM. The actual
      published updater offered 2.3.0, installed after authorized consent and reopened with What's
      new; app and server report stable 2.3.0. Three documents, positions, bookmark note, imported
      voice, pronunciation, appearance, playback speed and the ready MP3 export survived.
- [x] (required) **The download.** The website serves the 2.3.0 installer; its hash matches the release
      manifest and it installs on the clean Windows machine.
      — verified: 2026-11-18, the actual live website link delivered the official installer; its hash,
      length, updater signature and GitHub attestation passed. Those unchanged bytes installed from
      read-only media on a fresh clean-baseline Windows 11 clone without extra prerequisites. App
      and server report stable 2.3.0; the empty Library and Voices ready appeared, and the bundled
      sample narrated with advancing highlighting. No guest browser or audible assessment is claimed.
- [x] **Website and release notes.** The footer, download and release pages name 2.3.0 and describe
      matched voices accurately.
      — verified: 2026-11-18, live HTTPS responses after the successful release-triggered Pages run.
      Footer, download, release history and 2.3.0 notes agree; the installer link resolves correctly
      and the matched-voice description distinguishes a stand-in from optional cloning.

All three observations occurred within one hour of publication. Exact hashes, machines, timing and
limits are recorded in [the post-publication evidence](post-publication.md).

## Blockers

- [x] Restore desktop control for the existing clean VM. — verified: 2026-11-17, desktop control
      started after the maintainer unplugged the SanDisk USB device with an unreadable partition.
      Preserved the VM's original state as snapshot `34d3a3c1-6b10-4569-adf5-35c8a8aa4f99`, restored
      clean baseline `e393553b-8545-4210-b305-d180bd01e1a1`, and installed the test-signed candidate.
- [x] Complete and record the before-release observations above. A successful MSIX build alone does
      not establish that Microsoft's reviewer can use optional cloning or the matched path.
      The first VM pass found paused local requests when offline and a Python-probe import failure
      during optional engine setup. The rebuilt package passed offline retests and the Python probe,
      then exposed blocked Visual C++ DLL loads. The runtime-copy prototype passed CPU verification
      and its first cloned narration; final CI revision `.6` passed fresh cloning before and after
      restart, and `.7` passed the package-folder update with fresh cloned speech.
      — verified: 2026-11-17, the earlier six before-release checks have recorded evidence: the first three
      use physical `.1` observations supported by the final payload comparison; cloning, restart,
      update and candidate workflows use source `3f1fb3d`. The release gate will separately enforce
      exact-head workflow results after this evidence is committed.
      — verified: 2026-11-18 UTC, the added local-agent item passed on the actual amended Store
      candidate `7ca64f4` in Windows 11, and all four required workflows passed on that source.
      All seven before-release items now have their explicitly scoped observations; exact-head
      automation is required again after recording them. No post-publication item is marked early.
- [x] Complete the required after-publishing evidence for 2.2.0 in its acceptance record.
      The release gate checks that record before permitting the next version.
      — verified: 2026-11-17, the published 2.1.0 app's signed updater installed 2.2.0 after consent,
      relaunched with app/server 2.2.0 and retained the checked private data and settings. The website
      download's hash and a separate clean-VM installation were verified; the optional homepage
      presentation gap has an explicit reasoned waiver. The previous-release acceptance verdict
      reports all three items done or waived with a reason.

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

## Rebuilt candidate observations

2026-11-17, the same `TTSNative-Win11-Clean` VM and clean baseline
`e393553b-8545-4210-b305-d180bd01e1a1`, standard `reader` account, four CPUs, 8 GB RAM, no NVIDIA GPU,
developer tools or Visual C++ redistributable. This pass uses PR #108 source
`5d403f703464960b4b5ca904460beca229033d49`, built by Desktop run `44156656546` from its synthetic merge
`72a1a79303981f176e3e78af9a0c792b9135fbc9`.

- The unsigned CI MSIX SHA-256 is
  `8a810ac4f1fe544930bc3a9f62af40c28fc9b561616071a57eafe01d8617c438`. Its test-signed revision
  `2.3.0.1`, supplied on the read-only `TTSN230C` disc, has SHA-256
  `5ec9df9e05d773b69bba08c31943970c5c1c627801ef4954e08bf0dbf79562fc`. The package audit records
  all 6,874 application/runtime ZIP entries unchanged; only the test manifest revision and generated
  signature metadata differ. This is a sideloaded test-signed package, not a Microsoft-signed Store
  distribution.
- The maintainer imported the new public test certificate in the guest. App Installer recognized the
  exact publisher and enabled **Install** for `2.3.0.1`. The VM's virtual network cable was
  disconnected while installation was still at 89%, before first launch. The installed app reached
  an empty Library with **Voices ready**, without a console; the sidebar build began
  `2.3.0-dev.12`.
- With the cable still disconnected and Chatterbox absent, imported
  `offline-local-request-check.txt` (121 bytes). Heart narrated all three sentences to 100%, with
  0:07 elapsed. Exported `offline-local-request-check.mp3` (58 KB in the app, 58.0 KB in Explorer)
  and downloaded it locally. Windows Media Player progressed to 0:07 elapsed with 0:01 remaining.
  Playback progression was observed; audio was not audibly assessed.
- Still offline, imported the generated 12-second `synthetic.wav`; local validation detected
  9.6 seconds of speech. Saved the quick profile `test`, created `test (matched)`, generated its
  sample without error and selected **Use for reading**, which changed to **Used for reading**.
  Imported the previously unread `sample.docx`: the picker selected `test (matched)`, while the
  original `test` profile remained **Not installed**. Narration advanced through both sections to
  100%, with 0:06 elapsed.
- Closed TTSNative and reopened it from Start with the cable still disconnected. The Library kept
  both completed documents. Imported the fresh `sample.epub` (**The Night Train**); the picker kept
  `test (matched)`, and the original `test` profile and Chatterbox default remained **Not installed**.
  Matched narration advanced through both sections to 100%, with 0:05 elapsed. No personal recordings
  were used and sound was not audibly assessed.
- Optional CPU installation ran from approximately 20:19 to 20:23 UTC. The managed Python 3.11.17
  probe and dependency installation passed; the app downloaded the 2,849 MB of model files and the
  server logged the artifact as installed. Verification then failed with **The voice engine reported
  an error (PermissionError)**. Preserved the complete 620-byte server log in the guest's Downloads
  before closing the app; the worker traceback is hidden at the normal production log level.
  Successful installation, cloning from the saved recording and the packaged update remain unverified.
- Two temporary diagnostic revisions, `2.3.0.3` and `2.3.0.4`, retained the application's loading
  behavior but enabled local diagnostic logging. The `.4` package confirmed that the parent and
  worker selected the current package's `runtime/python` folder and could see all four Visual C++
  DLLs. `vcruntime140.dll` was already loaded; loading `vcruntime140_1.dll`, `msvcp140.dll` and
  `msvcp140_1.dll` by full path each failed with `PermissionError`, errno 13, Windows error 5.
  PyTorch then failed loading `c10.dll` or its dependencies. The 620-byte initial failure log,
  2.00 KB traceback and 4.54 KB per-DLL diagnostic log are preserved in the guest's Downloads as
  `server.log`, `server (2).log` and `server (3).log`. These diagnostic packages are not submission
  candidates.
- The source fix copies the app's four bundled DLLs into the existing per-user engine folder,
  verifies exact bytes before reuse and publishes new sets into content-based directories so an
  update never overwrites a mapped DLL. It changes no Windows permissions or package capabilities.
  The production-logging functional prototype passed the installed-package experiment below; the
  final CI package's subsequent observations are recorded separately below.

## Functional prototype observations

2026-11-17, the same Windows 11 VM, standard `reader` account, four CPUs and 8 GB RAM, with its virtual
disk backed by the host's HDD. No NVIDIA GPU, system Visual C++ redistributable or developer tools were
added. This pass used the temporary `2.3.0.5` functional prototype, not the final CI package.

- The prototype used the earlier `5d403f7` CI binary/runtime payload with seven server/worker source
  files matching `3f1fb3de86270f69947632b6471e3423f901223a`, including the per-user DLL copy and
  sanitized diagnostics. Normal production logging was restored. Its test-signed MSIX SHA-256 is
  `aced46fd979b99061a8b1c2c5b520ea769558a78921e0000026ebb0f08994ae1`.
- Retrying optional CPU installation reused the downloaded runtime and models and successfully
  verified the engine. The 415-byte production server log records the model artifact installed at
  guest-local `15:04:26`, then **chatterbox loaded**, device **cpu**, at `15:09:40`: 314 seconds for
  model verification, approximately 342 seconds for the retry overall. The VM remained at four CPUs
  and 8 GB RAM throughout.
- Selected the original saved profile `test` in the voice picker; the separate `test (matched)`
  blend and Chatterbox default were also available. Imported a fresh 73-byte TXT document,
  `cloned-worker-update-check.txt`, with no previous narration for the original voice. Pressing
  **Play** generated and played its speech, reached 0:04 elapsed and 0:00 remaining, and returned the
  Play button within 108 seconds of the initial press. The single-sentence document's position label
  stayed at **0% listened**; this is not recorded as 100% progress. No new recording was needed and
  audio was not audibly assessed.
- The successful HDD-backed VM was powered off and preserved as snapshot `32b80166`. A full copy to
  SSD storage was then in progress with the same CPU and RAM allocation. Results from the completed
  SSD copy and final CI package follow; these prototype observations do not establish restart or
  update behavior themselves.

## Earlier Voice Studio CI candidate observations

Before the agent amendment, source `3f1fb3de86270f69947632b6471e3423f901223a` had all 21 reported
checks green: [CI](https://github.com/carsonmcrae/ttsnative/actions/runs/44174221062/attempts/2)
(macOS runner-capacity retry), [Desktop](https://github.com/carsonmcrae/ttsnative/actions/runs/44174221122),
[CodeQL](https://github.com/carsonmcrae/ttsnative/actions/runs/44174220986) and
[Inference & E2E](https://github.com/carsonmcrae/ttsnative/actions/runs/44174208391).
Its local check passed 95 script, 671 web and 1,457 server tests with 100% application line/branch
coverage. Production audits passed; worker audits retained their reviewed exceptions. Inference
passed 15 with three optional-engine skips; browser E2E passed 78 with one existing WebKit skip.
This is historical component evidence, not a test of a subsequent agent package.

Desktop run `44174221122` built source `3f1fb3de86270f69947632b6471e3423f901223a` through synthetic merge
`41e15797a6aacfa76121f6e5130b9b0d01dd18e2`. Its immutable unsigned CI MSIX SHA-256 is
`9022d6f09e3793f93099e9a2ea9d7d7e2cdd071832950111a5a86013415457fa`.

- Test-signed revisions `2.3.0.6` and `2.3.0.7` preserve all 6,877 application/runtime ZIP entries
  byte-for-byte; only the manifest test revision and generated package/signature metadata differ.
  Their SHA-256 values are `81d44b237c004b53f82c92887f1898626e866ea5ae976b599f5c9e8a777b5185` and
  `6b4c5369cc089ac22c229d43d647a6453e35d57c540fe481562e7a08af507cf8`, respectively.
- A comparison with the earlier `.1` package found all 1,106 fallback-related files byte-identical;
  the 286 logical web assets differed only in version metadata. This supports the earlier physical
  offline observations for bundled and matched voices; it is not another offline VM test on `.6`.
- Installed `.6` on the full SSD/NVMe-backed copy of the preserved VM, still with four CPUs, 8 GB RAM,
  standard `reader` account and no additional system Visual C++ redistributable. The app reached the
  Library with four documents retained; original profile `test` and the separate `test (matched)`
  blend were both ready. The app identified itself as `2.3.0-dev.13+codex-release-2-3-0.41e15797a6`.
- Imported `candidate-clone-first.txt`, a fresh 31-byte document containing "The dawn brings a quiet
  breeze." With the original `test` profile selected, pressed Play at `21:39:12.706 UTC`; the end
  state was observed at `21:46:24.835 UTC`: 0:02 elapsed, 0:00 remaining, Play returned and no error.
  Another VM was being observed while generation/playback completed, so no completion duration is
  claimed for this first run.
- Closed the app and reopened it from Start; the Library retained five documents. Imported the
  never-read `candidate-clone-restart.txt` (37 bytes), "A blue lantern rests beside the door." The
  picker confirmed the original `test` profile, with the matched blend available separately. Pressed
  Play at `21:51:29.081 UTC`; the end state was observed by `21:55:38.336 UTC`, within 250 seconds:
  0:02 elapsed, 0:00 remaining, Play returned and no error. These single-sentence documents retained
  a 0% position label; this is not claimed as 100% progress. No new recording was made and audio was
  not audibly assessed.
- App Installer recognized the exact publisher and enabled **Update** from `.6` to `.7`; installation
  started at `21:55:57.530 UTC`, and the automatically launched app was ready by `21:56:38.376 UTC`.
  The Library retained six documents. The original `test` profile remained selected, while the
  separate `test (matched)` blend was still ready.
- Imported the never-read `candidate-clone-update.txt` (37 bytes), "A green boat waits beside the
  bridge." Pressed Play with the original profile at `21:56:59.286 UTC`; the end state was observed at
  `21:58:50.018 UTC`, within 112 seconds: 0:02 elapsed, 0:00 remaining, Play returned and no error.
  The single-sentence position label stayed at 0%; audio was not audibly assessed. This verifies
  fresh cloned speech after the actual package-folder change, using the saved recording and keeping
  the matched blend separately available.
- The installed-package observations above are complete for source `3f1fb3d`. The documentation-only
  evidence commit that records them must still pass the release gate's exact-head workflow checks;
  no future-head workflow result is claimed here. The three after-publishing checks remain open.

## Local agent integration observations

Source `6fb6d47978bf48c905c98649e2f33c09ffd57c6a` was exercised on the Windows host using a separate
temporary data directory, the prepared source runtime and bundled Kokoro model. The personal app,
Store VM and existing recordings were not used. The integration reuses the existing document,
reader and export implementations; no cloud voice provider or marketplace upload was involved.

- The standalone helper was copied unchanged into unrelated temporary directories and used to
  export a PDF as WAV (905,400 bytes), a DOCX with the available British George voice as MP3
  (50,864 bytes), and an EPUB as M4B (64,432 bytes, two chapters: Opening and Arrival). Independent
  probing and full decoding confirmed finite, nonzero audio; the WAV also passed Python's wave
  reader. A separate Markdown-to-MP3 export produced 53,024 bytes. These are synthetic public
  fixtures. Audio quality and accent were not audibly assessed.
- Three real Chromium journeys verified narration with sentence highlighting, an autoplay rejection
  followed by manual Play recovery, and an open request remaining pending until the actual reader
  loaded. The autoplay rejection alone was simulated; document ingestion and synthesis were real.
- A real scanned-PDF import returned `scanned_pdf`; existing-output protection returned
  `output_exists` without changing the file. Read-only Windows installation detection succeeded
  without launching that app. An actual discovery-directory ACL inspection found no broad access.
- `npm run check`, whole web/server coverage and `npm run security` passed: 149 script tests,
  697 web tests and 1,501 server tests, with 100% application statement/branch coverage. Real-model
  inference passed 15 tests with three expected optional-Chatterbox skips. The complete browser
  suite passed 81 tests with the existing WebKit music-join skip, running separately from the
  production build. Ubuntu CI [Inference & E2E](https://github.com/carsonmcrae/ttsnative/actions/runs/44199978238)
  independently passed the same 15 inference tests and 81 browser tests with the same skips.
- The portable ZIP passed its builder/validator, independent Python ZIP reading and skill metadata
  validation. It contains one SKILL.md and five necessary text support files. ZIP SHA-256:
  `728d1f591cbd70cba3f0fa17e9c85b92030a2a04f7b0fe3291decc6e45dd62a5`.

The [Windows installer smoke step](https://github.com/carsonmcrae/ttsnative/actions/runs/44199981280/job/134451257594)
for the same source passed at `2026-11-17T23:43:34Z` on a disposable Windows Server 2025 runner. The
real standalone helper discovered the installed desktop instance, matched its version to the
expected installer build, found bundled Heart available, and imported a public TXT fixture. Its
native reader request returned `playback_started` after the actual reader acknowledgement. A second
helper process completed an MP3 export, verified the audio signature and saved a file larger than
5,000 bytes whose length matched the reported download. No test-only playback hook was used by
this agent journey. The surrounding smoke step also passed its normal speech, export, restart and
uninstall assertions. Audio was not audibly assessed.

The [Store package job](https://github.com/carsonmcrae/ttsnative/actions/runs/44199981280/job/134451257750)
compiled the Store-feature Rust release and created an unsigned CI MSIX. This is build evidence;
neither that job nor the NSIS smoke test establishes installed Microsoft Store activation. These
observations also do not establish a disconnected network test of this new integration. The required
integration item remains open for the Windows 11 Store check and exact-head release checks after
the pending change file is folded into the release with `release:amend`.

### Output compatibility follow-up

Final client review found that hard-link publication rejected otherwise writable
[FAT32/exFAT destinations](https://learn.microsoft.com/en-us/windows/win32/fileio/filesystem-functionality-comparison).
The helper now copies the verified download with `COPYFILE_EXCL`; an existing output,
including one created after preflight, stays protected. The final pathname can be visible while
copying, and completion is reported only after that copy finishes. Three focused regressions cover
unavailable hard links, a late-created destination, and temporary-download cleanup on copy failure.
All 57 focused client/launch/package tests passed. The complete `npm run check` passed again with
152 script tests, 697 web tests and 1,501 server tests. No physical FAT/exFAT drive was tested.

The revised standalone helper, SHA-256
`98cd52f9066018f1c06fe13b2b7b5f4eb0e7e8e87ca03ec3b540fd6994b9a409`, was copied into a fresh unrelated
temporary directory and exercised again against an isolated source instance. PDF-to-WAV produced
776,916 bytes (16.184 seconds); DOCX-to-MP3 with available British George produced 51,008 bytes
(11.051 seconds); EPUB-to-M4B produced 63,477 bytes (10.459 seconds) with Opening and Arrival intact.
Independent probing, full finite/nonzero audio decoding, WAV metadata and chapter timing passed.
These observations supersede the earlier helper/package for distribution; they do not add an audible
quality assessment or an installed Store observation. The rebuilt six-file ZIP passed its validator
and independent Python ZIP reading. Its SHA-256 is
`54fd275a685a77749e8a0e3e0d389d2fdb38a8e125b5289e995281feeb3a0aac`.

## Agent amendment: installed Windows 11 Store verification

2026-11-18 UTC, `TTSNative-Win11-Store-SSD`, Windows 11 Home, standard `reader`, four CPUs and 8 GB
RAM, with the virtual network cable disconnected. Snapshot `a7d66974-e13b-4bb1-b589-c6974e242995`
preserves the prior successful Store/voice state. This pass updated the existing `.7` installation;
it is not a fresh Windows baseline installation or a repeat of the earlier cloned-voice tests.

- [Desktop run 44231136648](https://github.com/carsonmcrae/ttsnative/actions/runs/44231136648)
  built amended source `7ca64f4dfc6f1dec015126c66971506cb34ab34a`. The immutable unsigned MSIX is
  `2.3.0.0`, exact Store name/publisher, SHA-256
  `d97c014552a320461f70040d5ea1e2076f2412d2dd7e52f6f5c2599fe3ec4c19`.
- The guest used test-signed revision `2.3.0.8`, SHA-256
  `01431386494b98313d52ac92dc561209ae8cb1c9353dacc1f88545d1ed71865d`.
  SDK unpack/repack and signature verification confirmed all **6,890 application entries** have
  identical bytes and raw/decoded paths; only the identity test revision and generated package/signature
  metadata differ. The existing guest-trusted test certificate was reused; host trust was not changed
  and no private key was copied to the media. This test copy is never a Store submission artifact.
- The maintainer manually started the reviewed temporary runner once. Codex-directed commands then
  executed locally in the guest with portable, already-available Node 24.19.0, using an unchanged
  extraction of the exact six-file skill ZIP `54fd275a…b3a0aac` and helper `98cd52f9…9a409` identified
  in full above. No developer tools, dependencies, trust settings or networking were installed/changed.
- The real packaged launcher started the app. Authenticated discovery returned `desktop`, protocol
  **1**, and version `2.3.0-dev.20+codex-release-2-3-0-agent-amend.7ca64f4dfc`. Missing/bad bearer
  requests returned **401**; a request with browser Origin returned **403**. Bearer credentials stayed
  out of reports, command lines and media. The one-use reader ticket passed through the app's strict
  activation argument; neither tickets nor ticket URLs were recorded in reports or media.
- The helper imported an eight-sentence synthetic TXT, selected bundled Heart at generation pace
  0.8 and returned `playback_started`. Host-UTC screenshots at `03:52:30` and `03:53:13` showed the
  third sentence highlighted at 0:13, then the final sentence at 0:47 with Pause present. A later
  observation showed 0:52 elapsed, 0:00 remaining and Play restored. No separate 100% position label
  or audible quality is claimed. The runner itself did not claim visual observation.
- A separate new synthetic input exported as MP3: **54,872 bytes**, completed job, MP3 signature and
  reported/saved length matched. An existing synthetic output returned `output_exists` and retained
  its original SHA-256. An actually unprepared source directory returned `source_setup_required`;
  the guest's absent ffmpeg returned `ffmpeg_required` for M4B without creating an output. No mock,
  dependency download, personal document, recording or destructive action was involved.
- The preserved guest report says `passed`, from `03:50:39.174Z` through `03:53:01.533Z`. It was read
  in Notepad through the VM UI; guest JSON/audio were not exported to the host. The host observation
  record is a transcription plus separate visual observations, not a claimed copy of that report.
- Two independent ZIP builds produced identical **37,836-byte** files with the full SHA-256 above;
  the package validator and Python ZIP reader passed. Current Agensi packaging and creator FAQ
  permit this free MIT skill and its standalone text scripts. Publication still requires a compatible
  release to be available and a submission-time listing-name check; no listing was published.

Any subsequent exact-head package confirmation is recorded in [PR #110](https://github.com/carsonmcrae/ttsnative/pull/110)
with its own source and artifact hashes, so the evidence commit does not silently relabel an earlier
package as a later test. These pre-publication observations left the three after-publishing items
open; their completed observations are recorded in [the post-publication evidence](post-publication.md).

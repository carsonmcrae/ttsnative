# Acceptance: 2.2.0

What a person checks on real machines and devices, in priority order. The release gate
(`npm run release:gate -- 2.2.0`, run again by the Release workflow) reads this file:

- **Before release** checks are done on the release candidate before the tag. Tick one only with
  evidence: `- [x] … — verified: <date>, <machine or device>, <what you saw>`. A check marked
  **(required)** can never be waived; any other can be `- [~] … — waived: <reason>`. A bare tick or a
  waiver without a reason counts as not done.
- **After publishing** checks test the published release, so the gate refuses the tag if any of them
  is marked: they can't have happened yet. Do them within an hour of publishing. 2.3.0's gate refuses
  its tag until they are ticked (with "verified:") or, if not required, waived with a reason. If a
  required one fails, follow "If the published release is broken" below.
- **Blockers** are owner steps; each is ticked with a "verified:" note.

The release candidate is the installer from the Desktop workflow's `ttsnative-windows-installer`
artifact on the release commit: the release's code, built with the test hooks the release build leaves
out. The update itself is tested after publishing, because the app only updates from a published GitHub
release.

## Before release

- [x] (required) **Clean install.** On a Windows 11 PC or VM that has never had TTSNative, Python or
      Node.js: run the candidate installer, accept SmartScreen's "More info → Run anyway" (no
      Authenticode yet), start from the Start menu, open a PDF, play it, export an MP3. Needs: a clean
      Windows 11 machine (a fresh VM is fine). — verified: 2026-10-30, VirtualBox VM restored to its
      clean-baseline snapshot (Windows 11 Home 10.0.26300, standard user; no Python, Node.js, Rust, uv
      or git; NAT only). Candidate `TTSNative-Setup-2.2.0-dev.123+release-v2-2-0.6d143506e6.exe` from
      PR #81's Desktop run 41098845013, built from 6d14350 (the same tree as 0fe28a5; the commits after
      it up to #81's merge, 49768af, touch only this folder), SHA-256 5eb43639…b426. Its copy in
      Downloads carried the Internet zone mark: SmartScreen said "Windows protected your PC" (Unknown
      publisher), More info → Run anyway; per-user install with no administrator prompt; started from
      the Start menu; Voices ready; a two-page PDF opened and played (highlight and progress moving;
      the VM's sound wasn't listened to); an MP3 export of 530 KB, one minute, downloaded to
      Downloads; About shows the build and What's new the 2.2.0 notes as plain text; the four Visual
      C++ DLLs (14.51, Microsoft-signed) are in runtime\python and none in System32. An earlier pass on
      b62219d's build found the notes' Markdown asterisks, fixed in f852e2d. Not repeated on the
      final build: the app changed after 49768af (#82's voice-cloning fix, #92's dependency updates
      from Dependabot #83–#90), and the maintainer chose on 2026-11-03 not to repeat the VM tests.
      CI's Desktop workflow builds and smoke-tests the final installer; #82's build was installed on
      this VM (next check).
- [x] (required) **Upgrade in place, private data kept.** On a PC with the published 2.1.0 installed
      and real data in it (documents with bookmarks and notes, a cloned or studio voice, pronunciation
      fixes, settings, an export): run the 2.2.0 candidate installer over it. Everything is still there,
      migration 17 ran (the Sounds tab opens), About shows 2.2.0. Then close, end the app in Task
      Manager, restart: still there. Uninstall keeping data, reinstall: still there. Needs: 2.1.0
      published. — verified: 2026-10-30, the same VM (standard user, no Visual C++ redistributable),
      from a snapshot with 2.1.0 installed from ttsnative.com and real data: a pasted excerpt, a PDF
      and an EPUB with reading positions, a bookmark with a note in each, a pronunciation fix for all
      documents, speed 1.25×, Relaxed spacing and Sans serif, an MP3 export and a custom voice made
      from a 30-second import. `TTSNative-Setup-2.2.0-dev.124+main.49768af4da.exe` (Desktop run
      41115979905 on 49768af), started by double-clicking, offered "Uninstall before installing", and
      its uninstaller left "Delete the application data" unticked. Afterwards every item was still
      there (positions, bookmarks and notes, the pronunciation, settings, the export, the voice);
      What's new showed once; the Sounds tab opened and saved an effect (migration 17); About showed
      2.2.0-dev.124; playback ran. Ended in Task Manager (no TTSNative process left), restarted from
      the desktop shortcut: all still there, the new effect included. Closed, then #82's build
      (`2.2.1-dev.129`, run 41130416289) installed the same way, uninstalling 2.2.0 with the data
      kept: the library was still there, and voice cloning installed and generated speech with the
      custom voice (the VM's sound wasn't listened to). Not repeated on the final build, which adds
      #91's test fixes and #92's dependency updates from Dependabot #83–#90: the maintainer chose on
      2026-11-03 not to repeat the VM tests. CI's Desktop workflow checks the final build's
      persistence across close, crash and update.
- [x] **Listen: background music** under narration with headphones: a few tracks, including two new
      long ones past their first 20-second join and their loop point; pause and resume; both sliders;
      music never louder than the voice. Clips of each new loop point and first join are in the music
      session's `.tools/music/listen/`.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **Listen: sound effects** at Minimal, Balanced and Immersive under narration and music; note
      which Experimental sounds could be promoted.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **Listen: an Immersive reading** of one curated book end to end, then switch it back to Standard.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **Real phones on the home network**: an iPhone with Safari and an Android phone with Chrome
      ([lan-phone-checklist.md](../../guides/lan-phone-checklist.md): pair, read, play, export,
      revoke). Needs: both phones on the same Wi-Fi as the PC.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **Voice cloning in the installed app**: install the engine, make a voice from a consented clip,
      restart, it still reads. Needs: several gigabytes of downloads.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
      Also on 2026-10-30, #82's build on the clean VM installed the engine and generated speech with a
      custom voice made in 2.1.0 (no new voice from a clip and no restart check there).
- [x] **A Studio Voice session** in the installed app (about 15 passages), usable after a restart.
      Needs: a microphone and a quiet room.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **Fine-tuning** (windows-app-testing.md step 5): runs as a background job, the A/B plays, Keep,
      Discard and Remove behave; a phone shows status only. Needs: an NVIDIA GPU computer.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **An M4B** in an audiobook player (chapters and cover) and **a read-along EPUB** in a reader
      with Media Overlays. Needs: ffmpeg installed for M4B; an EPUB 3 reader such as Thorium.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **Audiobookshelf**: send an export to a real server. Needs: an Audiobookshelf server.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.
- [x] **The local speech API** from an outside client (curl or the OpenAI SDK, per
      local-speech-api.md). — verified: 2026-10-30, the same clean VM and candidate, with Windows'
      own curl.exe: while off, POST /v1/audio/speech answered 404; turned on in Settings with a new
      token, the guide's request (kokoro:af_heart) answered 200 with audio/mpeg, 11,904 bytes; a
      wrong token answered 401; Settings then said "Last used less than a minute ago, with Heart. 1
      request served." The OpenAI SDK wasn't tried (no Python outside the app on that VM).
- [x] **A screen reader** (NVDA or Narrator) over the library, reader, Voice Studio and Settings.
      — verified: 2026-11-03, reported by the maintainer as done and passing; no details were recorded.

## After publishing

- [x] (required) **The real signed update.** On the PC upgraded above, reinstall 2.1.0 if needed, then
      About → Check for updates: 2.2.0 is offered with its notes, installs after you agree, the app
      reopens with your data, and About shows 2.2.0.
      — verified: 2026-11-17, `TTSNative-Win11-Upgrade-2.1-to-2.2`: the published 2.1.0 app offered
      2.2.0 with its real release notes. After consent to **Install and restart**, the actual signed
      in-app updater downloaded the update and relaunched automatically. About showed both app and
      server 2.2.0. The three documents remained, with the PDF at 55% and EPUB at 19%; the bookmark
      note was still exactly "Upgrade test note: the keeper counts 112 steps." The saved
      `Upgrade test voice` profile kept its 30-second imported clip and October 30 consent. Playback
      speed remained 1.25×; appearance remained System, Standard, Medium, Relaxed, Sans serif and
      Normal width. The all-document pronunciation `Morlocks` → `MOR-locks` remained, as did the
      Ready MP3 export (528 KB, one minute). The post-update About, PDF/bookmark, voice, appearance,
      pronunciation and export screenshots record these observations. Audio was not audibly assessed.
- [x] (required) **The download.** ttsnative.com/download/ starts the 2.2.0 installer; its SHA-256
      matches `SHA256SUMS.txt` on the release; it installs on the clean machine.
      — verified: 2026-11-17, host HTTPS and isolated Chromium: the live
      [download page](https://ttsnative.com/download/) automatically started
      `TTSNative-Setup-2.2.0.exe` from published `v2.2.0`. The saved installer is 424,812,869 bytes;
      SHA-256 `a59b3de42222717d72179ed6147c94fab34e08c635f5046dc9892003a5fe1e47` matches both the live
      [release checksums](https://github.com/carsonmcrae/ttsnative/releases/download/v2.2.0/SHA256SUMS.txt)
      and GitHub's published asset digest. Transferred that verified installer on the read-only
      `TTSNPREV` disc to `TTSNative-Win11-Download-2.2`, restored from clean baseline `e393553b`.
      Installed as standard user `reader` into the default per-user `%LOCALAPPDATA%\TTSNative`
      folder, without an administrator prompt or separately installed developer tools or Visual C++
      redistributable. Setup completed; **Finish** with **Run TTSNative** selected launched the app.
      NAT was connected for this first launch. The empty Library showed **Voices ready**, and About
      showed app 2.2.0, server 2.2.0 and **Stable release**. Installer-completion and About screenshots
      are recorded with the web/hash and clean-VM evidence.
- [~] **The website** footer and release pages name 2.2.0, and the 2.2.0 features (sound effects,
  Immersive, the music card) appear.
  — waived: 2026-11-17, live browser checks confirm that the footer and release pages identify
  2.2.0 and the background-music card appears. The homepage still omits the Sound effects and
  Immersive card and the newer long-track music copy; the release pages describe those features
  correctly. This optional marketing presentation gap is deferred until the maintainer merges
  and deploys the website condition fix.

## Blockers

- [x] The `release` environment exists with you as required reviewer, and both
      `TAURI_SIGNING_PRIVATE_KEY` and `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` secrets are set. — verified:
      2026-10-30, GitHub API: environment `release` has carsonmcrae as required reviewer and a branch
      policy, and lists both secrets by name (values not read); Release run 39974518710 signed and
      published 2.1.0 with them on 2026-10-23.
- [x] The updater private key and its password are backed up offline in two places.
      — verified: 2026-11-03, the maintainer confirmed both backups are made and each was checked.
- [x] 2.1.0 is published from `6037548` (the fix for the C++ runtime on top of `e71d192`), installs, and
      its update check reaches GitHub (About → Check for updates says it's up to date). The gate also
      checks on GitHub that v2.1.0 is published from a release commit. — verified: 2026-10-23, after
      publishing: v2.1.0 is a published, non-draft release whose tag points at 6037548; a clean Windows 11
      VM installed it from ttsnative.com through Edge, it spoke, About showed 2.1.0 "Stable release" and
      the update check (automatic and manual) said it's up to date.

## If the published release is broken

If a required check after publishing fails: on GitHub, edit the 2.2.0 release and tick "Set as a
pre-release". `releases/latest` then points back at 2.1.0, so no app is offered the broken update and
the website's download falls back after its next build. Fix forward as 2.2.1; never move or reuse the
v2.2.0 tag.

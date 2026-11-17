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

- [ ] Restore desktop control or provide a guest automation connection for the existing clean VM.
      It is powered off, has no Guest Additions, SSH or WinRM route, and the desktop-control runtime
      fails to start. No VM state or existing test data has been changed.
- [ ] Complete and record the before-release observations above. A successful MSIX build alone does
      not establish that Microsoft's reviewer can use optional cloning or the matched path.
- [ ] Complete the still-open required after-publishing evidence for 2.2.0 in its acceptance record.
      The release gate checks that record before permitting the next version.

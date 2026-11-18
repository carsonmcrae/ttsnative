# Post-publication evidence: 2.3.0

The maintainer explicitly authorized publication, the real post-publication checks and preparation
of the official Microsoft Store package. No application or dependency changes were made.

## Published source and assets

- Annotated tag `v2.3.0` points to verified main commit
  `eaf4b05f1ee375f6272f3131648ec63aa86fe7e2`. Its four required workflows and release gate passed
  before tagging; the tag was authored by Carson McRae and was not moved or replaced.
- [Release run 44331272896](https://github.com/carsonmcrae/ttsnative/actions/runs/44331272896)
  passed verification, signing-key validation, the clean-runner smoke test, Store packaging and
  attestation/publication. The existing protected environment was approved under the maintainer's
  explicit instruction; no signing key or credential was retrieved or changed.
- [The public release](https://github.com/carsonmcrae/ttsnative/releases/tag/v2.3.0) became Latest at
  **2026-11-18 15:23:20 UTC (09:23:20 America/Chicago)**, neither draft nor prerelease.
- The installer is **424,929,305 bytes**, SHA-256
  `ead2b3686dee4e3291274456885d173cf0e13bd21aa6b0a739b8bc2f3eb3e35d`.
  The published checksum manifest, GitHub asset digest, updater signature against the built-in key,
  and GitHub attestation all matched. Attestation verification pinned the repository, Release
  workflow, source commit and tag, and rejected self-hosted runners.

## Actual published 2.2.0 to 2.3.0 update

Windows 11 Home, standard `reader`, four CPUs/8 GB RAM, no NVIDIA GPU, VM
`TTSNative-Win11-Upgrade-2.1-to-2.2` (`53a163db-1f4a-4b6f-ae4c-9865908996a5`). Before boot,
snapshot `b73afcb5-96f8-40cc-9c26-629659faea3c` preserved the powered-off published 2.2.0 installation
and its checked test data. Only this isolated VM's existing NAT cable was connected for the update.

Fresh visual observations confirmed app/server 2.2.0 and the baseline data. After publication,
**Check for updates** offered 2.3.0 with the actual matched-voice and local-agent notes. **Update now**
then **Install and restart** were consented under the maintainer's instruction. The real updater
downloaded, verified and installed the published release; TTSNative reopened automatically with
**What's new in TTSNative 2.3.0**. About reports **app 2.3.0, server 2.3.0, Stable release**.

Before/after observations matched:

| Data          | Retained observation                                                              |
| ------------- | --------------------------------------------------------------------------------- |
| Documents     | Three: Lamp Keeper PDF, Time Machine EPUB and the pasted sample                   |
| Positions     | PDF 55%, EPUB 19%, pasted sample 46%                                              |
| Bookmark      | `Upgrade test note: the keeper counts 112 steps.`                                 |
| Voice         | `Upgrade test voice`, 30-second imported clip, created October 30, 2026           |
| Export        | Lamp Keeper MP3, Ready, 528 KB, one minute                                        |
| Appearance    | System, Standard contrast, Medium text, Relaxed spacing, Sans serif, Normal width |
| Pronunciation | `Morlocks` → `MOR-locks`, All documents                                           |
| Reader        | 1.25×; paused at 0:30 with the same highlighted sentence                          |

No new recording, optional engine installation or data deletion was performed. The app closed
normally after verification. The old A/B CI updater test is supporting evidence, not the source of
these actual published-update observations.

## Website-delivered installer on clean Windows

Fresh linked clone `TTSNative-Win11-Download-2.3.0`
(`cf0bdc75-b554-43ed-85b9-5cb5df4910d1`) came from the preserved clean Windows 11 snapshot
`e393553b-8545-4210-b305-d180bd01e1a1`. The source VM and Store SSD VM were not restored or modified.
The clone used the standard `reader`, four CPUs/8 GB RAM, NAT only, no shares, no clipboard or drag
and drop, and no preinstalled TTSNative or developer tools.

At **15:24:23 UTC**, the live [download page](https://ttsnative.com/download/) linked to
[the official 2.3.0 installer](https://github.com/carsonmcrae/ttsnative/releases/download/v2.3.0/TTSNative-Setup-2.3.0.exe).
Downloading that exact link returned HTTP 200 and the size/hash above. Verification finished at
**15:25:05 UTC**. The unchanged installer and public checksum/signature files were copied to a
read-only disc, `TTSN230PUB`, for the clean guest.

The per-user installer completed successfully in `C:\Users\reader\AppData\Local\TTSNative`, with
no administrator prompt, separate redistributable or development-tool install. Its normal finish
page launched TTSNative. The **empty Library** and **Voices ready** appeared without a console.
About reports **app 2.3.0, server 2.3.0, Stable release**, bundled Python 3.12.14 and CPU mode.
**Try a sample** opened _A Scandal in Bohemia (excerpt)_. Play generated bundled narration; a visual
observation showed 0:26 elapsed, 0:37 remaining, 36% listened and the later sentence highlighted.
Playback then finished at 1:03 elapsed/0:00 remaining with the final sentence highlighted and Play
restored; no error was observed.
After normal app closure and graceful Windows shutdown, snapshot
`8afeba79-63ee-4495-b543-126b1ff485bb` preserved the passed clean installation powered off with its
virtual network cable disconnected.

The website delivery was verified on the host; installation used those same bytes on read-only
media. This does not claim a guest browser download, Internet-zone mark or SmartScreen assessment.
Neither VM's sound was audibly assessed. Host UTC is used for the publication window; the fresh
guest's displayed clock was an hour behind. The update and clean-install observations completed
within the first hour after publication.

## Live website

[Pages run 44335065992](https://github.com/carsonmcrae/ttsnative/actions/runs/44335065992) deployed
the release-triggered rebuild from the same source successfully at **15:24:08 UTC**. Live observations
at **15:25:26–15:25:28 UTC** returned HTTP 200 for the homepage, download page, release history and
[2.3.0 notes](https://ttsnative.com/releases/2.3.0/).

The footer links Version 2.3.0 to its notes; history selects 2.3.0. Both the download anchor and its
one-second refresh point to the exact published installer; the checksum link is also for 2.3.0.
The final download response is HTTP 200, Content-Length 424,929,305. The notes describe the matched
voice as a stand-in mixed from built-in voices, not a copy of the speaker, usable without the
cloning download while retaining the recording for later.

## Official Microsoft Store package

Release artifact **14439908496**, `ttsnative-store-package`, contains the untouched, unsigned
`TTSNative-2.3.0.msix`: **468,888,446 bytes**, SHA-256
`7d5b40ed59c37b34d17d904f658344101b0a15520afb3810ed71373114cebead`.
Its archive digest, sibling checksum, ZIP integrity, 15 tagged agent/application/worker source files,
protocol 1 declarations and known debug-marker/Node exclusions passed static validation.

Identity: `CarsonMcRae.TTSNative`, publisher `CN=C4520066-EE1C-4415-98F3-3A007C6FA29A`,
`2.3.0.0`, x64, Windows 11 minimum `10.0.22000.0`. Its published release asset has the same size/hash
and its GitHub attestation passed the source/tag/workflow constraints above. The workflow's generic
artifact collection also attached the MSIX publicly; this does not submit it to Microsoft.

The package was staged with checksum/provenance evidence and certification-note copy for manual
resubmission. It was not repacked, signed or installed during this post-publication pass. Earlier
installed Windows 11 Store observations keep their original source/test-revision scope. No Partner
Center submission or Agensi upload was performed; Store `listed` remains false until actually live.

## Retained evidence

Ignored local records under `.tools/publication-2.3.0/` retain publication metadata, updater and
clean-install observations, the unchanged downloaded installer, attestation results, live HTML/HTTP
evidence and official Store validation. They contain no private signing key, bearer credentials,
reader tickets or personal recording. The original VM snapshots and test recordings were kept.

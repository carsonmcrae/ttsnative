# Free listing draft: TTSNative Reader

Prepared for maintainer review. This is listing copy, not a submitted or published marketplace page.

**Title:** TTSNative Reader — Private Document Narration and Audiobooks

**Price:** Free

**Short description:** Read PDFs, EPUBs, Word, Markdown and text aloud on your computer, or make a
local MP3, WAV or chaptered M4B audiobook with TTSNative.

## Description

Ask your local assistant to open a document in TTSNative, request narration with sentence
highlighting, choose an available voice, or export an audiobook. TTSNative processes documents and
generates speech on your computer. After setup, its installed voices work offline, without an API
key, account, subscription or cloud inference.

This free, MIT-licensed skill uses the existing TTSNative reader and resumable export pipeline.
It discovers the running app, checks voices and prerequisites, and reports actual results. Browser
autoplay can require you to press Play; the skill reports that instead of claiming audio started.
Exports protect existing output files and retain job IDs for pause, status and resume.

The skill runs independently of Agensi. It does not upload your documents, recordings or generated
audio to Agensi or call paid voice providers.

Website: [ttsnative.com](https://ttsnative.com/)

Source and licence: [carsonmcrae/ttsnative](https://github.com/carsonmcrae/ttsnative)

## Features

- Open a selected document in TTSNative's normal reader.
- Request local narration with synchronized sentence highlighting.
- Choose from installed, ready voices by language and accent.
- Save MP3 or WAV audio using the app's encoder.
- Export chaptered M4B when ffmpeg is already installed.
- Inspect, pause and resume the existing export jobs.
- Receive machine-readable success, failure, unsupported or user-action results.
- Work offline after dependencies and chosen models are installed.

## Formats, prerequisites and limits

Supported skill inputs: PDF with extractable text, EPUB, DOCX, Markdown (`.md`, `.markdown`) and TXT.
Output: MP3, WAV and M4B. M4B uses existing document chapter boundaries.

Requires an agent with local shell and file access on TTSNative's computer, Node.js 22.22+, and a
TTSNative build supporting agent protocol 1. Use the Windows 11 app or an already-prepared source
checkout. An agent running only in the cloud or inside an isolated environment cannot control a
different computer's desktop. The Windows app does not install Node for your agent.

Reading requires an interactive app or browser; browser autoplay may need a Play click. Exports
can run without a GUI. M4B requires an already-installed ffmpeg. The skill never installs apps,
dependencies, models or optional engines automatically. Scanned PDFs, legacy `.doc`, DRM removal,
cloud voices and automatic voice cloning setup are not included. Only installed, ready voices can
be selected. Replacing an output or canceling saved export work requires user approval.

## Example requests

- “Read this PDF aloud using TTSNative.”
- “Open this EPUB in TTSNative without starting audio.”
- “Read this Word document using an available British voice.”
- “Turn this Markdown document into an MP3 in this output folder.”
- “Export this book as an M4B with chapters if ffmpeg is installed.”

**Keywords:** text to speech, TTSNative, read aloud, offline, private, local AI, PDF, EPUB, DOCX,
Markdown, audiobook, MP3, WAV, M4B, accessibility, document reader.

**Suggested tags:** Productivity; Accessibility; Document processing; Audio; Local tools.

## Review checklist

- Use the generated `ttsnative-reader.zip`, containing exactly one skill and text supporting files.
- Confirm the release with agent protocol 1 is available and the intended platforms were verified.
- Keep the local execution and Node requirements visible in the listing.
- Set the listing to free and retain both official project links and MIT attribution.
- Review the current Agensi requirements before manual upload. No submission is automated here.

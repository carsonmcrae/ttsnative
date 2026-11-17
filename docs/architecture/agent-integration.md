# Local agent integration

The reader skill controls the existing TTSNative application. Document extraction, sentence
segmentation, voice readiness, playback and resumable exports retain their existing implementations.
The optional `/v1/audio/speech` API takes text and returns audio; it does not import documents, open
the reader or manage audiobook export jobs, so it is not the skill's control interface.

## Decisions

- A standalone Node.js helper is the portable agent entry point. It uses only built-in modules and
  works when copied alone into a temporary file, as Agensi delivers scripts. Node is an explicit
  prerequisite of the agent host, not something the Windows app installs or the skill downloads.
- The existing server provides a narrow `/api/agent/v1` interface. Every operation requires a
  per-instance bearer token and a loopback connection; browser-origin and LAN requests are refused.
  Existing Host, forwarding, CSRF and LAN protections remain in force. Agent operations reuse
  document, voice and export services and do not accept arbitrary server-side file paths.
- The server publishes its actual port and a fresh token in a per-instance descriptor in a private
  user directory. Each credential-containing leaf is created with owner-restricted permissions
  before writing. Tokens rotate at startup; authenticated instance identity detects stale records.
  The client refuses redirects and non-loopback endpoints before sending credentials or file bytes.
- A read request creates a short-lived, single-use ticket bound to its document and preferences.
  The ticket travels in a URL fragment, is removed from history immediately, and is claimed by the
  local reader. A separate request-scoped acknowledgement capability can report results but cannot
  create new commands. The ordinary player still renders sentence highlighting and handles audio.
- The Windows shell accepts only a strictly validated opaque reader ticket as a new command-line
  argument. Its existing single-instance behavior, server ownership and shutdown remain intact.
  A source installation opens the same reader in a browser. Actual playback acknowledgement, not
  a successful launch or resolved Play promise, determines whether narration started. Browser
  autoplay restrictions produce a user-action result with instructions to press Play.
- Exports use the existing jobs, pause/resume and downloads. The client writes to an explicitly
  chosen local output using exclusive creation; replacement requires explicit authorization.
  M4B requires an already-installed ffmpeg. No model, dependency or application installation,
  network exposure, telemetry, cloud voice provider or marketplace access is enabled by the helper.

## Distribution and verification

The skill lives under `integrations/agent-skills/ttsnative-reader/`. Its ZIP contains exactly one
`SKILL.md`, the standalone text helper, necessary references and the MIT licence. A deterministic
allowlist-based builder validates metadata and rejects binaries, dependencies, symlinks and unsafe
archive paths. Marketplace copy stays outside the skill. The package is prepared locally for owner
review; publishing or uploading is a separate action.

Tests cover authentication and tickets, discovery and launch outcomes, file and voice validation,
playback acknowledgement, export recovery and output safety, and standalone helper execution.
Real document ingestion and audio export complement unit tests; platform observations are recorded
separately from mocked operating-system behavior.

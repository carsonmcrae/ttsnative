# Results and recovery

Commands: `status`, `voices`, `open FILE`, `read FILE`, `export FILE`, and
`job status|pause|resume|cancel|download ID`. Selectors: `--instance`, `--discovery-dir`,
`--source-root`. Preferences: `--voice ID`, `--pace NUMBER`. Exports require
`--format mp3|wav|m4b` and `--output PATH`. `--wait-seconds` limits waiting without canceling app work.

| Result                                | Agent response                                                                                               |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Playback acknowledged                 | Say narration started; do not claim the whole book finished or audio quality was assessed.                   |
| Completed export with verified output | Return its local path, format and job ID.                                                                    |
| User action required                  | Give the action: press Play, select an instance, approve setup or choose an output filename.                 |
| Unsupported operation or old app      | State the limitation and offer an available local workflow.                                                  |
| Missing model or voice                | List ready alternatives or ask about official setup; do not download automatically.                          |
| M4B unavailable                       | Explain that ffmpeg is missing and offer MP3 or WAV.                                                         |
| Export still queued/running           | Keep the job ID and inspect it later; do not claim a finished file.                                          |
| Paused, interrupted or failed export  | Inspect status, address the prerequisite and resume that job when supported.                                 |
| Authentication/discovery failure      | Refresh status, select the intended instance or relaunch the app; never use an unauthenticated API fallback. |

`--overwrite` must follow permission to replace an existing file. `job cancel ID --confirm-cancel`
discards saved work and requires explicit approval. Pause/resume preserve work. No command grants
permission to share the output externally.

Initial commands can return `launch_required`. Run the independent launch helper for the installed
Windows app, then retry discovery during startup for at most three minutes. If it remains unavailable,
ask the user to check the app or upgrade to an agent-protocol-1 build. Do not repeatedly launch it.

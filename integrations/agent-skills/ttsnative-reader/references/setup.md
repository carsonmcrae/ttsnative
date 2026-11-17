# Setup and compatibility

The agent needs Node.js 22.22+, a local shell and access to the selected file on TTSNative's computer.
The Windows application does not install Node for the agent. Remote agents and isolated containers
cannot operate a desktop outside their environment.

Run `node helper status` first. A TTSNative build supporting agent protocol 1 is required. Use
[official Windows releases](https://ttsnative.com/download/) or the
[project repository](https://github.com/carsonmcrae/ttsnative). Obtain approval before installation,
upgrades, dependency or model downloads. The helper never installs them automatically.

The Windows 11 application includes the default voice model. Source users must follow the approved
repository quick start and build the web UI first. `--source-root` selects a running checkout.
The separate launch helper can open an existing Windows installation, but source startup requires
the user to check for a server already using that checkout's database and start the prepared app.
Never start another backend against an application's existing database.

Discovery uses the current user's private TTSNative agent directory. A custom root needs
`--discovery-dir`; ambiguous instances need `--instance`. Do not guess ports or read tokens from logs.
The reader needs an interactive session; a browser may require a Play click. Exports can run without
a GUI. M4B requires ffmpeg already visible to the application; otherwise offer MP3 or WAV.

After setup, narration and exports work offline with installed models and ready voices. Scanned
PDFs, DRM-protected books and legacy Word `.doc` files are outside this skill.

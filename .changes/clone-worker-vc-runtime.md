---
bump: patch
desktop: changed
browser: changed
phone: limited: voices are created on the computer running TTSNative
website: unchanged
docs: changed
---

## Fixed

- On a Windows PC with few other programs installed, such as a new one, installing voice cloning no longer stops with "The voice engine reported an error".

## Technical

- The voice-cloning worker starts with the desktop runtime's folder first on `PATH`, so PyTorch finds the Microsoft Visual C++ runtime (`msvcp140.dll`) that the runtime ships next to `python.exe`. The worker runs on uv's own Python, which carries `vcruntime140.dll` but not `msvcp140.dll`, so on a PC without Microsoft's redistributable `import torch` failed with `OSError: [WinError 126]` loading `c10.dll` and the install's verification load reported `OSError`. Found on a clean Windows 11 VM while testing the 2.2.0 upgrade; the maintainer's PC and GitHub's runners have the redistributable, so nothing automated had noticed.

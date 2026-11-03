---
bump: none
desktop: unchanged
browser: unchanged
phone: unchanged
website: unchanged
docs: unchanged
---

## Technical

- `test_a_request_that_takes_too_long_answers_504` restores the usual speech-API timeout before its last request: left at the 0.3 s it sets to force a timeout, that request failed with 504 on a slow Windows runner (CI on `main` at `3d0aedc`), as its sibling in `test_speech_api_load.py` did before.

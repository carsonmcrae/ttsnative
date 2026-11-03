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
- The library rail test's recently added document is created on the day the test runs. Its fixture date of 19 October fell outside the 14 days that Recently added counts on 2 November, and the test has failed on every run since.

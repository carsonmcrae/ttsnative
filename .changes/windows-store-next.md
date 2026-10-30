---
bump: none
desktop: unchanged
browser: unchanged
phone: unchanged
website: changed
docs: changed
---

## Technical

- ttsnative.com's installation steps describe both warnings an unsigned installer meets: Edge's "isn't commonly downloaded" (… → Keep, then Keep anyway) and SmartScreen's "Windows protected your PC" (More info → Run anyway).
- The download section leads with "Get TTSNative from the Microsoft Store" once `listed` is true in `apps/desktop/store/identity.json`, keeping the installer as the alternative (`scripts/site/store.mjs`, `<!-- if:store -->` / `<!-- if:no-store -->`, applied after the download section is decided).
- The code signing policy says the direct download is unsigned: SignPath Foundation declined on 2026-10-24 pending wider adoption (ADR-26 updated); the Microsoft Store version is signed by Microsoft.
- The Release workflow builds `TTSNative-X.Y.Z.msix` from the tag with the Partner Center identity and keeps it as the `ttsnative-store-package` artifact for 30 days; it publishes nothing. `docs/guides/windows-distribution.md` now walks through the Store submission: package, properties, listing text, screenshots, restricted-capability justifications and certification notes.

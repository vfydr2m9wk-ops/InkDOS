# InkDesk release notes

## Current release — v0.20.2.26

**Export Confirmation Safety and Release Notes Organization**

Spreadsheet Save-copy now treats browser download dispatch as **unverified**: recovery is flushed before the request, but dirty/recovery protection is not cleared merely because the browser accepted the click. This prevents a canceled or lost download from silently removing the user's in-browser safety net.

Historical per-version notes have been moved to [`docs/releases/`](docs/releases/). The complete note for this release is [`docs/releases/RELEASE_NOTES_0.20.2.26.md`](docs/releases/RELEASE_NOTES_0.20.2.26.md).

The hosted package/checksum suite and **17/17 Chromium regressions** remain the authoritative release gate.

# InkDesk v0.20.2.29 — Cross-Workspace Unverified Export Safety Hardening

This maintenance release prevents a browser download request from being mistaken for a verified save in the editable workspaces where that mistake could remove the user's last unsaved-work protection.

## Current release

- Documents flushes pending recovery before the DOCX copy is offered and no longer clears dirty/recovery state when the download link is clicked.
- Presentations flushes pending recovery before PPTX download dispatch and no longer marks the presentation saved or clears recovery merely because the browser accepted the request.
- TXT now transitions through the shared `export-preparing` and `download-requested-unverified` lifecycle states instead of calling `resetClean()` after download dispatch.
- Spreadsheet keeps its existing unverified-download protection unchanged.
- PDF and EPUB are deliberately not changed in this patch because the demonstrated data-loss risk is materially lower, keeping the patch bounded to cases where benefit exceeds regression risk.
- Existing visual layout and file-format behavior are intentionally unchanged.

Full notes: [`docs/releases/RELEASE_NOTES_0.20.2.29.md`](docs/releases/RELEASE_NOTES_0.20.2.29.md)

Historical notes: [`docs/releases/`](docs/releases/)

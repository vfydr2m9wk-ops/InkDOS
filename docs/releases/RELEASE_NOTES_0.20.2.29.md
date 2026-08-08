# InkDesk v0.20.2.29 — Cross-Workspace Unverified Export Safety Hardening

## Why this patch exists

The stability audit after v0.20.2.28 confirmed the same unsafe assumption in three editable workspaces: once the browser accepted a download request, InkDesk could immediately clear the in-app dirty state and/or recovery snapshot even though browser APIs do not confirm that the user actually retained the downloaded copy. If the browser cancelled, redirected or failed the download and the user then closed or replaced the document, the last protected version of the work could be lost.

## Changes

### Documents

- Flush pending IndexedDB recovery before presenting the generated DOCX copy for download.
- Keep dirty state and recovery snapshots after the Save-copy link is clicked.
- Report that changes remain protected until the copy is verified.

### Presentations

- Flush pending presentation recovery immediately before PPTX download dispatch.
- Do not call `markSaved()` or recovery cleanup after an unverified download request.
- Preserve the existing package-generation and source-buffer behavior; only the save-verification assumption changes.

### TXT

- Enter `export-preparing` before creating the text copy.
- Transition to `download-requested-unverified` after dispatch instead of `resetClean()`.
- Keep before-unload/discard protection active when the editor contains changes that have not been verified in a reopened copy.

## Deliberate exclusions

- Spreadsheet already implements this strict policy and is left unchanged.
- PDF review changes are continuously persisted to local review storage, so the demonstrated loss path is lower risk.
- EPUB Save only downloads the original book under the chosen copy name; it does not contain editable book-content state.

Those lower-risk paths are not changed merely for consistency; this release follows the rule that a stability patch proceeds only when expected benefit exceeds regression risk.

## Validation

The release adds deterministic cross-workspace export-safety tests and extends the existing Chromium functional-corrections harness rather than adding another browser-script process. The hosted gate remains the authoritative checksum and 17-script Chromium validation.

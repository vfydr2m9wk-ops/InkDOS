# InkDesk v0.20.2.26 — Export Confirmation Safety and Release Notes Organization

This maintenance release hardens Spreadsheet Save-copy behavior at the point where the browser can only confirm that a download was requested, not that the user actually retained the file.

## What changed

- Spreadsheet recovery is flushed before a generated XLSX copy is dispatched to the browser.
- A download request no longer clears the Spreadsheet dirty state or private recovery snapshots.
- The workbook remains protected as unsaved until the user explicitly replaces/discards it, so canceling or losing a browser download cannot silently remove the recovery path.
- The Save-copy message now tells the user to confirm the XLSX in Downloads before discarding the workbook.
- The existing local-recovery Chromium regression now verifies that dirty-state, title warning and at least one recovery snapshot remain present immediately after the first download request.
- Historical per-version release notes were moved out of the repository root into `docs/releases/`.
- `RELEASE_NOTES.md` remains at the root as the current-release/index entry point, and `docs/releases/README.md` indexes the historical notes.

## Stability rationale

A browser anchor click only proves that InkDesk asked the browser to download a Blob. It does not prove that the user accepted the download, that the browser completed it, or that the resulting file remains available. Clearing dirty/recovery state at that moment could therefore create a false "saved" condition. v0.20.2.26 adopts the conservative rule that an unverified download request does not destroy the in-browser safety net.

## Repository organization

All historical `RELEASE_NOTES_*.md` files now live under `docs/releases/`. The repository root keeps only `RELEASE_NOTES.md`, making the source tree easier to browse without changing any runtime path.

## Validation target

Local reconstruction: **313/314** tests pass; the only hold is the authoritative PDF.js checksum because the three hosted publication files are absent locally. The hosted target is **314/314 tests + 17/17 Chromium regressions + checksum PASS**.

# InkDesk 0.20.2.9 — Presentations Architecture Consolidation

This patch completes the current Presentations refactoring cycle without changing the visible editor contract.

## Architecture

- Added `apps/presentations/io/pptx-write-adapter.js` as the focused owner of package-preserving PPTX write/patch operations.
- `apps/presentations/app.js` now composes the writer with the existing file, recovery, slideshow, history, selection, notes, thumbnails and inspector controllers instead of owning imported-PPTX mutation helpers itself.
- The existing native modular runtime remains unchanged: no React migration, build step, backend or telemetry was introduced.

## Behavior contract

- PPTX open/edit/save-copy behavior is intended to remain unchanged.
- Imported slide text/transform/transition patching and presenter-note patching use the same algorithms moved behind the adapter boundary.
- New-presentation shape and image XML generation uses the same serialization logic moved behind the adapter boundary.
- No visual redesign or new editing feature is included.

## Validation

The release gate keeps the cumulative unit/package suite, the independent Chromium browser scripts, checksum verification, source audit and architecture ratchet. The GitHub Actions dry-run remains the authoritative candidate-tree validation before commit/push.

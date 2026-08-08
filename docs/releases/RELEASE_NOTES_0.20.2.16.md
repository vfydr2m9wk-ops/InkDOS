# InkDesk v0.20.2.16 — Documents Ruler Model Decomposition

This beta architecture patch continues the bounded shared-UI refactor without adding features or changing the visible Documents ruler contract.

## What changed

- Added `shared/ui/document-ruler-model.js` as the focused owner of pure ruler calculations and indent-state helpers.
- Moved existing ruler tick generation, active-page geometry, visible-page selection, selected-block indent state, clamping, pointer conversion and indent style/input application out of `shared/ui/workspace-layout.js`.
- Kept ruler DOM synchronization, ticks/handle rendering, zoom/scroll/selection observation and pointer drag lifecycle in `workspace-layout.js`.
- Preserved the public `InkDeskWorkspaceLayout` helper methods through compatibility delegation to the new model.
- Added explicit load ordering in Documents and the Office shell, plus offline precaching for the model.

## Architecture ratchet

- `shared/ui/workspace-layout.js`: 1,009 -> 710 physical lines.
- `shared/ui/document-ruler-model.js`: 346 physical lines, below the normal 500-line new-file ceiling.
- `shared/office-shell.js`: 435 physical lines after adding the model loader, still below the normal 500-line ceiling.

## Behavior contract

No visible control, default state, DOCX open/save behavior, page geometry rule, ruler unit, indentation interaction, panel behavior or workflow behavior is intentionally changed.

The hosted gate remains authoritative: full Python/package validation, checksum verification and the existing 17 isolated Chromium regression scenarios must all pass before the live transaction is committed.

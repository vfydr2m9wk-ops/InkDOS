# InkDesk v0.20.2.17 — Documents Ruler Interaction Decomposition

This beta architecture patch continues the bounded shared-UI refactor without adding features or changing the visible Documents ruler contract.

## What changed

- Added `shared/ui/document-ruler-drag-controller.js` as the focused owner of the existing ruler pointer-drag lifecycle.
- Moved pointerdown/move/up/cancel handling, pointer capture, drag-state transitions, indentation application orchestration and drag status messages out of `shared/ui/workspace-layout.js`.
- Kept ruler DOM synchronization, tick/handle rendering, zoom/scroll/selection observation and resize/mutation observers in `workspace-layout.js`.
- Kept all pure ruler geometry and indent-state calculations in `shared/ui/document-ruler-model.js`.
- Added deterministic load ordering in Documents and the Office shell, plus offline precaching for the drag controller.

## Architecture ratchet

- `shared/ui/workspace-layout.js`: 710 -> 541 physical lines.
- `shared/ui/document-ruler-drag-controller.js`: 252 physical lines, below the normal 500-line new-file ceiling.
- `shared/ui/document-ruler-model.js`: remains 346 physical lines.
- `shared/office-shell.js`: 493 physical lines after adding the drag-controller loader, still below the normal 500-line ceiling.

## Behavior contract

No visible control, default state, DOCX open/save behavior, page geometry rule, ruler unit, indentation result, panel behavior or workflow behavior is intentionally changed.

The hosted gate remains authoritative: full Python/package validation, checksum verification and the existing 17 isolated Chromium regression scenarios must all pass before the live transaction is committed.

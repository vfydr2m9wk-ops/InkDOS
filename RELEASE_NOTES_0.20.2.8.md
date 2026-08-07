# InkDesk 0.20.2.8 — Presentations I/O and Recovery Decomposition

## Purpose

Continue the behavior-neutral Presentations refactor by moving file lifecycle
and recovery responsibilities out of the main editor entry point.

## Changes

- Added `apps/presentations/io/file-controller.js` for PPTX open validation,
  imported source-buffer ownership, preservation-mode save, new-presentation
  PPTX generation and copy download lifecycle.
- Added `apps/presentations/io/recovery-controller.js` for IndexedDB snapshot
  capture/restore, file recovery keys, dirty/clean signaling and restore-state
  coordination.
- `apps/presentations/app.js` now delegates open/save/recovery orchestration
  through explicit controller dependencies while retaining format parsing,
  editing and imported-slide patch helpers.
- The architecture ratchet for Presentations moves from 783 physical lines /
  82 long lines to 714 / 70.
- Offline precache, manual browser harnesses and structural tests load the two
  new I/O controllers before `app.js`.

## Preserved

- No visual redesign or new editor feature.
- Existing PPTX compatibility, preservation-mode copy export and local recovery
  behavior are intended to remain unchanged.
- Existing Inspector, thumbnails, presenter notes, selection/history and
  slideshow controllers remain unchanged.
- The GitHub Actions workflow remains untouched by the update ZIP.

## Next bounded step

Close the Presentations decomposition with a consolidation pass and only then
begin the PDF decomposition.

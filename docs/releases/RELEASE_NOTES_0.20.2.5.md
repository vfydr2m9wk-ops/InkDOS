# InkDesk v0.20.2.5 — Presentations State and Selection Decomposition

Released: 2026-08-07

This patch is the third behavior-neutral Presentations decomposition step.
It moves object-selection state, drag/resize/rotate interaction state, and
Undo/Redo history stacks out of the monolithic `apps/presentations/app.js`.

## Architecture changes

- Added `apps/presentations/state/selection-controller.js` for selected-object
  ownership, canvas clear/reselect behavior, drag/resize/rotate gestures,
  selection handles, and alignment guides.
- Added `apps/presentations/state/history-controller.js` for snapshot capture,
  bounded Undo/Redo stacks, action wrapping, restoration, and toolbar state.
- Kept `app.js` as the presentation/document orchestrator and lowered its
  architecture ratchet again.
- Added both state components to the offline shell and every browser harness
  that manually loads Presentations runtime scripts.

## Behavior contract

No visual redesign, new editing command, PPTX format change, save behavior,
recovery format, or default panel state is intended. Existing Inspector,
thumbnail and presenter-notes components remain unchanged in responsibility.

The Presentations browser regression now explicitly proves object
clear/reselect plus Undo/Redo restoration after formatting, in addition to the
existing Format panel, notes, thumbnails, tabs, compact drawer and Escape
checks.

## Scope

This remains a beta architecture-refactor patch. The next bounded Presentations
step should isolate slideshow/presentation-mode behavior before I/O and recovery
are considered for extraction.

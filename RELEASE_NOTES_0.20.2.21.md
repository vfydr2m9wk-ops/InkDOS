# InkDesk v0.20.2.21 — Spreadsheet Formula Session Lifecycle Decomposition

## Scope

- Adds `apps/spreadsheets/formula-session.js` as the owner of persistent formula draft state.
- Moves deterministic start/update/suspend/resume/commit-preparation/cancel-preparation transitions out of `formula-editor.js`.
- Keeps DOM/caret synchronization, suggestion rendering, keyboard behavior and formula-reference integration in `formula-editor.js`.

## Stability result

The draft lifecycle now has a DOM-free Node regression surface. Tests cover draft creation, newline normalization, caret clamping, suspension, resumption by worksheet/cell key, commit cleanup and cancellation restoration. This targets the class of Spreadsheet bugs where an incomplete formula could lose or reuse the wrong state after changing cells.

## Architecture result

`apps/spreadsheets/formula-editor.js` falls from 616 to 586 physical lines. The new session module is 169 lines and remains below the normal 500-line ceiling. The editor ratchet is reduced to the new boundary; no new architecture debt entry is created.

## Behavior contract

No visible Spreadsheet UI, formula semantics, selection behavior, XLS/XLSX import/export, Save, dirty-state or workflow behavior is intentionally changed.

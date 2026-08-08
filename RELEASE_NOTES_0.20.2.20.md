# InkDesk v0.20.2.20 — Spreadsheet Formula Model Decomposition

## Scope

- Extracts the immutable Spreadsheet function catalog to `apps/spreadsheets/formula-model.js`.
- Extracts pure column/cell encoding, parenthesis tracking, formula balancing, suggestion context/matching/insertion and reference/commit predicates from `formula-editor.js`.
- Keeps persistent draft state, DOM/caret synchronization, suggestion rendering, keyboard handling and reference-controller integration in `formula-editor.js`.

## Architecture result

`apps/spreadsheets/formula-editor.js` falls from 756 to 616 physical lines and its grandfathered ratchet is reduced accordingly. The new formula model is 194 lines and stays below the normal 500-line ceiling. The browser entry point loads the model before both formula interaction controllers and the service worker precaches it.

## Stability result

The deterministic formula helpers now have an independent Node test surface, including quoted-parenthesis handling, formula balancing, suggestion insertion and reference-selection/commit predicates. `formula-editor.js` keeps the existing `InkDeskFormulaEditor` helper API through delegation so existing callers and regression harnesses do not change.

## Behavior contract

No visible Spreadsheet UI, formula semantics, in-cell editing, draft persistence, selection, XLS/XLSX import/export, Save, dirty-state or workflow behavior is intentionally changed.

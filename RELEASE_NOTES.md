# InkDesk v0.20.2.20 — Spreadsheet Formula Model Decomposition

Pure formula-session logic now lives in `apps/spreadsheets/formula-model.js`, while `formula-editor.js` retains stateful in-cell editing, draft persistence, suggestion UI and reference-controller integration. The public helper API and visible Spreadsheet behavior are intentionally unchanged. See `RELEASE_NOTES_0.20.2.20.md`.

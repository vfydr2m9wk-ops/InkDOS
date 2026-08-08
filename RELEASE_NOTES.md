# InkDesk v0.20.2.19 — TXT Editor Interaction Decomposition

Plain Text Undo/Redo history and Find interaction now live in focused TXT controllers. `apps/txt/app.js` remains responsible for file lifecycle, encoding, Save, counts and display controls while falling below the normal 500-line ceiling. No visible or file-format behavior is intentionally changed. See `RELEASE_NOTES_0.20.2.19.md`.

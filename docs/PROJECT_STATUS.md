# Project status

Release: **InkDOS 2.0.7**

Six installed independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. InkDOS 2.0.7 preserves the Web App compatibility restored in 2.0.5, the deterministic Plain Text distribution work from 2.0.6 and the six-app Share behavior from 2.0.4.

All workspaces now obey the same behavioral empty-state contract while remaining physically modular: opening a workspace alone does not make Save or Share available. Those actions become available only after the app has a real active document/book/PDF according to its own private state. Presentations now starts with zero slides and creates a presentation only after New or a successful Open. Plain Text starts unloaded unless New, Open, or a valid recovery checkpoint activates a document.

PDF retains the user-accepted P4.2 functional baseline. See `PDF-CLOSURE-AUDIT.md` for its verification scope.

# Project status

Release: **InkDOS 2.0.8**

Six installed independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. InkDOS 2.0.8 preserves the Web App compatibility restored in 2.0.5, the deterministic Plain Text distribution work from 2.0.6, the six-app Share behavior from 2.0.4 and the 2.0.7 empty-workspace behavioral contract.

All workspaces obey the same behavioral empty-state rule while remaining physically modular: opening a workspace alone does not make Save or Share available. Those actions become available only after the app has a real active document/book/PDF according to its own private state. Presentations starts with zero slides and creates a presentation only after New or a successful Open. Plain Text starts unloaded unless New, Open, or a valid recovery checkpoint activates a document.

InkDOS 2.0.8 hardens the two remaining UI discrepancies found in Edge: PDF and Spreadsheets now ship Save disabled directly in their initial HTML and render disabled menu actions visibly inactive, in addition to their existing app-local runtime guards. Home routes are versioned to the current release to make post-update navigation deterministic across browser caches.

PDF retains the user-accepted P4.2 functional baseline. See `PDF-CLOSURE-AUDIT.md` for its verification scope.

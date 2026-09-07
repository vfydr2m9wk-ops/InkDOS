# Project status

Release: **InkDOS 2.0.9**

Six installed independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. InkDOS 2.0.9 preserves the Web App compatibility restored in 2.0.5, the deterministic Plain Text distribution work from 2.0.6, the six-app Share behavior from 2.0.4, the 2.0.7 empty-workspace behavioral contract and the 2.0.8 fail-safe disabled-state work.

Home now supports Light, Dark and System with a compact appearance control. The same preference can be changed from any workspace using its existing appearance UI. The selected value is communicated horizontally through `inkdos2:appearance`; each workspace continues to apply the value through its own private appearance controller and retains its own app-specific preference key. There is no shared theme engine or cross-app runtime dependency.

This preserves physical modularity: extracting a workspace from the suite leaves its local appearance behavior functional; only suite-wide preference synchronization naturally disappears when no other InkDOS page is present.

All workspaces continue to obey the same behavioral empty-state rule while remaining physically modular: opening a workspace alone does not make Save or Share available. Those actions become available only after the app has a real active document/book/PDF according to its own private state. Presentations starts with zero slides and creates a presentation only after New or a successful Open. Plain Text starts unloaded unless New, Open, or a valid recovery checkpoint activates a document.

PDF retains the user-accepted P4.2 functional baseline. See `PDF-CLOSURE-AUDIT.md` for its verification scope.

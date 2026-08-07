# InkDesk v0.20.2.14 — Shared Document Session Decomposition

## Scope

This is a behavior-neutral architecture patch. It starts the shared-UI phase after the PDF decomposition completed in v0.20.2.13.

## What changed

- Moved the existing document-session implementation from `shared/office-shell.js` to `shared/ui/document-session-controller.js`.
- Preserved the existing editable filename contract across Documents, Spreadsheets, Presentations, PDF, TXT and EPUB.
- Preserved filename normalization and extension handling.
- Preserved title/content dirty-state bridging through `InkDeskFileLifecycle`.
- Preserved discard confirmation before replacement actions and file selection.
- Preserved `InkDeskRuntime.requestDownload` filename rewriting and clean-state reset after successful download dispatch.
- Kept `InkDeskDocumentSessionReady` as the public readiness promise exposed by `shared/office-shell.js`.
- Added the controller to the offline shell precache and application manifest.
- Reduced `shared/office-shell.js` from 617 to 315 physical lines and removed it from `grandfatheredDebt`.

## What did not change

- No visible UI redesign.
- No new control or editing command.
- No file-format parser/writer change.
- No PDF, DOCX, XLS/XLSX or PPTX fidelity change.
- No workflow-file change.
- No change to the document-session behavioral contract version (`0.20.0`).

## Validation intent

The permanent structural tests enforce controller ownership, Office-shell composition-only behavior, offline precache registration and architecture-debt retirement. The existing 17 Chromium regression scripts remain the behavioral gate; in particular the functional-corrections scenario continues to exercise shared title behavior in Spreadsheets and Presentations.

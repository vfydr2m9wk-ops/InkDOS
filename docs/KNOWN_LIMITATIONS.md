# Known Limitations

## General

- InkDesk does not aim for Microsoft Office feature parity or pixel-identical rendering.
- Saving creates a new download rather than overwriting the selected source file.
- Browser and host policies control file selection, downloads, fullscreen, service workers, and installation.
- Fonts can be substituted and change pagination or slide geometry.
- Active documents and Undo/Redo history are memory-only. Crash/session recovery is not implemented.
- Compressed Office inputs larger than 100 MiB are rejected. Packages are also rejected when entry count, per-entry expansion, total expansion, path safety, encryption, ZIP64, or compression-ratio limits are exceeded.
- Password-protected and encrypted Office files are unsupported.
- Direct `file://`, native Firefox, native Safari/WebKit, iPadOS, and embedded-host behavior was not executed in the current review environment.

## Documents

- Fields, comments, equations, embedded Office objects, tracked-change semantics, and complex DrawingML layouts are not fully editable.
- Content inside controls or revision wrappers may be displayed, but editing can change review semantics.
- Pagination is approximate.
- New documents use a compact generated DOCX package rather than a full Word template.
- Legacy `.doc` is unsupported.
- Filename editing is available in the Document Workspace; the selected source `File` object itself remains immutable.

## Spreadsheets

- BIFF8 `.xls` is import-only and is exported as `.xlsx`.
- Older BIFF variants, encrypted workbooks, unusual continuation records, VBA, ActiveX, legacy charts, and embedded OLE objects are unsupported or best effort.
- BIFF formula token streams are not reconstructed; cached displayed results are imported as values where necessary.
- Formula evaluation is intentionally limited and is not a complete Excel calculation engine. The local arithmetic preview uses a strict allowlist and remains a manual security-review item.
- External links, data connections, Power Query, pivot features, dynamic arrays beyond the focused implementation, and advanced chart fidelity are incomplete.
- Spreadsheet rename UI is not currently exposed; exported names derive from the opened workbook or generated default.

## Presentations

- Imported PPTX export preserves the existing slide set. Insert/delete/duplicate operations that would require rebuilding an imported relationship graph are blocked during preservation-mode save rather than silently discarding parts.
- New presentations can add, duplicate, reorder, and delete slides using the compact generated writer.
- SmartArt, embedded media, OLE objects, advanced animations, complex groups, charts, themes, and exact text layout are partial or preview-only.
- Presenter notes are preserved/editable when the imported package already contains the required notes relationships. Creating a complete notes graph for a new presentation is deferred.
- Presentation filename editing is not currently exposed.

## PWA and offline hosting

- The manifest and same-origin service worker are structurally present and validated.
- Static HTTP delivery of required assets was verified.
- Actual browser installation, service-worker control, and browser-offline reload were not executed because the available Chromium was administratively blocked from navigating to both `file://` and localhost URLs.
- The application remains usable without service-worker support when its files are otherwise accessible to the host.

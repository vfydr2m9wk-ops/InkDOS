# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2

Version 0.20.2 is the **Data Safety and Browser Matrix** patch. It keeps the six
modular workspaces introduced in v0.20.0 and adds private crash-recovery support
for the three editable Office workspaces without adding new editing tools:

- **Documents** — basic DOCX opening, editing, local recovery and copy export.
- **Spreadsheets** — XLS import, XLSX opening/editing, formulas, local recovery and copy export.
- **Presentations** — basic PPTX editing, presentation mode, local recovery and copy export.
- **PDF Workspace** — local PDF.js rendering, forms, review marks and PDF copy saving.
- **Plain Text** — local TXT viewing/editing with encoding-aware opening.
- **EPUB Reader** — local reflowed reading with themes, text sizing and images.

Recovery snapshots are stored only in the browser's IndexedDB. InkDesk offers
**Restore**, **Open normally**, and **Discard recovery**; it never silently
replaces the selected source file. Snapshot retention is bounded, and confirmed
copy saves clear the recovery record for that document.


InkDesk also maintains a functional acceptance matrix for the Home screen and all six workspaces. Visible controls that do not yet have dedicated behavioral evidence are explicitly tracked as scheduled rather than assumed to work.

## Privacy

The selected file is processed in the browser. InkDesk includes no project-run
upload server, account system or analytics service. Saving normally downloads a
new local copy rather than overwriting the source file.

## Run

Open `index.html` directly or serve the directory with a static HTTP server.
Cross-workspace handoff, service workers, browser recovery and installation are
more reliable over HTTP or HTTPS.

## Validate

```bash
npm run validate
npm run audit
npm test
npm run test:browser
npm run test:browser:matrix
```

The normal incremental-update workflow remains Chromium-only for predictable
runtime, and the complete release gate runs once without duplicate unit/audit passes. `test:browser:matrix` explicitly checks every installed Chromium,
Firefox and WebKit engine and reports unavailable engines as not performed
unless strict matrix mode is requested.

## Status

v0.20.2 remains a beta. Real-device validation is still required for critical
workflows, large files, native Safari/iPadOS, Firefox, Edge, download behavior
and installed-PWA behavior.

## License

MIT for InkDesk original code. Bundled third-party components retain their
upstream licenses; see `docs/THIRD_PARTY_NOTICES.md`.

## PDF.js vendoring during publication

The consolidated source pins `pdfjs-dist` 3.11.174 in `VENDOR_SOURCES.json`.
The publication process retrieves that exact npm package, commits the local
display and worker files, regenerates checksums, and runs strict validation.
The published app does not load PDF.js from a CDN at runtime.

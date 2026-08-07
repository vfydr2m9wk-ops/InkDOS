# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2.1

Version 0.20.2.1 is a narrow **Functional Corrections** beta patch on top of
v0.20.2. It adds no new formats or broad editing features. The patch fixes
visible and workflow inconsistencies found during the functional audit:

- simplifies the Home copy and synchronizes the visible beta version;
- makes Spreadsheet and Presentation filenames editable from the top bar;
- removes the obsolete visible `Forms: PDF.js` note while retaining AcroForm support;
- normalizes the TXT and EPUB primary title bars to the 44 px Office reference;
- adds permanent static and browser regression coverage for these corrections.

The v0.20.2 private recovery system remains unchanged: Documents, Spreadsheets
and Presentations keep bounded IndexedDB snapshots with Restore, Open normally
and Discard recovery choices.

The functional acceptance matrix remains the release policy: a visible control
is not considered verified merely because it exists or has an event handler.

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

v0.20.2.1 remains a beta. Real-device validation is still required for critical
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

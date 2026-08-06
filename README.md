# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.0

Version 0.20.0 is the first consolidated package after the 0.19.4 development
sequence. It replaces the long chain of internal update suffixes with one
complete source tree and six modular workspaces:

- **Documents** — basic DOCX opening, editing and copy export.
- **Spreadsheets** — XLS import, XLSX opening/editing, formulas and copy export.
- **Presentations** — basic PPTX editing and presentation mode.
- **PDF Workspace** — local PDF.js rendering, forms, review marks and PDF copy saving.
- **Plain Text** — local TXT viewing/editing with encoding-aware opening.
- **EPUB Reader** — local reflowed reading with themes, text sizing and images.

## Privacy

The selected file is processed in the browser. InkDesk includes no project-run
upload server, account system or analytics service. Saving normally downloads a
new local copy rather than overwriting the source file.

## Run

Open `index.html` directly or serve the directory with a static HTTP server.
Cross-workspace handoff, service workers and installation are more reliable over
HTTP or HTTPS.

## Validate

```bash
npm run validate
npm run audit
npm test
```

## Status

v0.20.0 remains a beta. Real-device validation is still required for critical
workflows, large files and browser-specific download behavior.

## License

MIT for InkDesk original code. Bundled third-party components retain their
upstream licenses; see `docs/THIRD_PARTY_NOTICES.md`.


## PDF.js vendoring during publication

The v0.20.0 source package pins `pdfjs-dist` 3.11.174 in
`VENDOR_SOURCES.json`. The publication workflow retrieves that exact npm
package, commits the local display and worker files, regenerates checksums, and
runs strict validation before replacing the repository. The published app does
not load PDF.js from a CDN at runtime.

# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.3.1

Version 0.20.3.1 applies the first workspace-specific visual pass on top of the v0.20.3.0 shared foundation. Documents now uses denser, clearer editor chrome; Plain Text becomes a quieter writing surface; and EPUB shifts toward a book-first reading presentation with less decorative navigation.

The structural baseline remains frozen at v0.20.2.31. This release adds a last-loaded presentation-only stylesheet for Documents/TXT/EPUB and regression coverage for its geometry and states; parsers, writers, recovery, formulas, history and document transactions remain unchanged.

## Development policy

The v0.20.2.31 structural baseline is frozen. During the 0.20.3 visual train, architecture and data-safety code should change only for a reproducible defect whose benefit clearly exceeds regression risk. Visual work should prefer shared CSS and bounded markup changes over opportunistic refactors.

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
runtime. `test:browser:matrix` explicitly checks installed Chromium, Firefox and
WebKit engines; unavailable engines are reported as not performed unless strict
matrix mode is requested.

## Status

v0.20.3.1 remains a beta. Real-device validation is still required for critical
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

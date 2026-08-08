# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.3.0

Version 0.20.3.0 starts the user-visible visual/UX phase on top of the frozen v0.20.2.31 structural baseline. A new shared presentation layer is loaded last by Home and all six workspaces, giving InkDesk one typography, surface, control-state and spacing system while preserving each workspace color identity.

The first pass deliberately avoids editor logic: parsers, writers, recovery, formulas, history and document transactions are unchanged. Home receives the largest immediate polish; the six workspaces receive common titlebar, toolbar, start-surface, focus and touch-target refinement without changing their feature set.

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

v0.20.3.0 remains a beta. Real-device validation is still required for critical
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

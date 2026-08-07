# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2.15

Version 0.20.2.15 continues the **shared UI decomposition** without changing the visible workflow. Cross-workspace panel visibility and persistence now live in `shared/ui/workspace-panel-controller.js`, while the Documents ruler remains in `shared/ui/workspace-layout.js`.

The new panel controller owns only the existing panel/layout-state behavior: Documents navigation, Presentations thumbnails/Format/notes, PDF navigation sidebar and Spreadsheet layout markers. The Documents ruler remains in `shared/ui/workspace-layout.js`, whose architecture ratchet drops from 1,270 to 1,009 physical lines.

The document-session extraction completed in v0.20.2.14 and the PDF decomposition completed in v0.20.2.13 remain unchanged. The hardened updater flow, package SHA identity, incremental checksums and the same 17 isolated Chromium scenarios continue to protect the behavior-neutral refactoring sequence.

## Refactoring policy

The 0.20.x decomposition remains incremental: continue shared UI in bounded
steps, then Documents/Spreadsheets cleanup and final architecture consolidation. Every extraction
must preserve existing behavioral tests, stay inside the architecture guardrails
and stop immediately if a regression appears.

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

v0.20.2.15 remains a beta. Real-device validation is still required for critical
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

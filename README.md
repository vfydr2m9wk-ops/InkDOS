# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2.13

Version 0.20.2.13 completes the main **PDF architecture decomposition** without changing the visible workflow. PDF rendering, navigation and review already live behind focused components; unified Save / flattened annotated export now moves behind `apps/pdf/io/save-controller.js`.

The save controller owns both existing save paths: PDF.js `saveDocument()` when there are no InkDesk review marks, and the local flattened exporter when review annotations must be embedded visibly. It also owns the Save button busy/available lifecycle and download coordination. `apps/pdf/app.js` is now below the normal 500-line architecture ceiling and remains the document-lifecycle/composition entry point.

The hardened updater flow remains in place: real dry-run, package SHA identity, incremental checksums and isolated browser scenarios protect each refactoring package.

## Refactoring policy

The 0.20.x decomposition remains incremental: finish Presentations in bounded
steps, then PDF → shared UI → Documents/Spreadsheets cleanup. Every extraction
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

v0.20.2.13 remains a beta. Real-device validation is still required for critical
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

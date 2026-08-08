# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2.19

Version 0.20.2.19 begins the final workspace-specific cleanup before the 0.20.3 milestone. Plain Text Undo/Redo history and Find interaction now live in focused controllers under `apps/txt/`, while `app.js` keeps TXT file lifecycle, encoding, save, counts and display controls.

The visible TXT editor is unchanged: the same buttons, 180 ms history batching, 80-snapshot bound, selection restoration, wrap/text-size controls and Find behavior remain in place. `apps/txt/app.js` drops below the normal 500-line ceiling and leaves grandfathered architecture debt.

The shared workspace-layout cycle completed in v0.20.2.18, the Documents ruler boundaries from v0.20.2.17/v0.20.2.16, document-session/panel decomposition from v0.20.2.14-v0.20.2.15 and PDF decomposition through v0.20.2.13 remain unchanged. The hardened updater and the same 17 isolated Chromium scripts continue to protect behavior-neutral refactoring.

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

v0.20.2.19 remains a beta. Real-device validation is still required for critical
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

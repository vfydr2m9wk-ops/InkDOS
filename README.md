# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2.3

Version 0.20.2.3 is the first behavior-neutral **Presentations decomposition**
patch. The existing Format/Inspector feature has been moved out of the large
`apps/presentations/app.js` controller into the focused
`apps/presentations/ui/inspector-controller.js` component.

The extracted controller owns Format-panel open/closed state, accessibility
state, compact Escape behavior, object geometry/opacity/fill/rotation controls,
image crop controls and the fill palette. `app.js` now composes that component
through a small dependency interface instead of owning those handlers directly.

No Presentations command, visual layout, file format or save behavior is
intentionally changed. The runtime remains native HTML/CSS/JavaScript,
local-first and build-free.

## Refactoring policy

The 0.20.x decomposition remains incremental: Presentations → PDF → shared UI →
Documents/Spreadsheets cleanup. Every extraction must preserve existing
behavioral tests, stay inside the architecture guardrails and stop immediately
if a regression appears.

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

v0.20.2.3 remains a beta. Real-device validation is still required for critical
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

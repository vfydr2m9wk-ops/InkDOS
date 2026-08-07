# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2.12

Version 0.20.2.12 continues the behavior-neutral **PDF architecture decomposition**.
Rendering remains in `viewer/page-renderer.js`, navigation remains in
`viewer/navigation-controller.js`, and PDF review behavior is now isolated in
`review/review-controller.js` plus `review/annotation-layer.js`.

The new review boundary owns local review persistence, selected-text
highlight/underline/comment flows, free marker/text placement, comments and review
Undo. `apps/pdf/app.js` remains the composition entry point and still owns unified
Save / flattened export and document lifecycle. No visible PDF control or file
format behavior is intentionally changed in this release.

The hardened updater flow remains in place: real dry-run, package SHA identity,
incremental checksums and isolated browser scenarios protect each refactoring
package.

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

v0.20.2.12 remains a beta. Real-device validation is still required for critical
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

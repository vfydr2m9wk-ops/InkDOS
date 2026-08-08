# InkDesk

InkDesk is an experimental, local-first browser productivity suite for focused
DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows. It is not intended to replace
Microsoft Office, a full PDF editor or a complete publishing system.

## InkDesk v0.20.2.18

Version 0.20.2.18 closes the current **shared workspace-layout debt** without changing the visible workflow. Workspace module detection, persisted panel-preference resolution and the `inkdesk:workspace-layout-ready` notification now belong to `shared/ui/workspace-panel-controller.js`; `shared/ui/workspace-layout.js` remains focused on Documents ruler DOM synchronization and delegates the shared contract helpers.

The compatibility surface remains available through `InkDeskWorkspaceLayout`: `defaults`, `moduleId()` and `resolvedPreference()` still resolve the same values in the delivered load order. `workspace-layout.js` drops from 541 to 492 physical lines and is removed from grandfathered architecture debt; the panel controller remains below the normal 500-line ceiling.

The ruler interaction/model boundaries from v0.20.2.17/v0.20.2.16, panel-state extraction from v0.20.2.15, document-session extraction from v0.20.2.14 and PDF decomposition from v0.20.2.13 remain unchanged. The hardened updater and the same 17 isolated Chromium scenarios continue to protect the behavior-neutral refactoring sequence.

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

v0.20.2.18 remains a beta. Real-device validation is still required for critical
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

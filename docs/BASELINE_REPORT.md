# Baseline Report — InkDesk 0.19.0-beta

## Scope and environment

This report records the unmodified package baseline before structural changes.

- Package: `InkDesk_v0.19.0-beta.zip`
- Review date: 2026-08-03
- Python: 3.13.5
- Node.js: 22.16.0
- npm: 10.9.2
- Browser automation: Playwright 1.57.0 with system Chromium
- Native Firefox: not available in the review environment
- Native Safari/WebKit: not available in the review environment
- iPadOS and embedded browser hosts: not available in the review environment

## Repository inventory

- Main hub: `index.html`
- Compatibility launchers: `InkDesk.html`, `Documents.html`, `Spreadsheets.html`, `Presentations.html`
- Document Workspace: `apps/documents/`
- Spreadsheet Workspace: `apps/spreadsheets/`
- Presentation Workspace: `apps/presentations/`
- Shared visual shell: `shared/`
- Validation scripts: `scripts/`
- Unit and package-preservation tests: `tests/`
- Bundled runtime libraries: JSZip 3.10.1 and pako inflate, duplicated in each workspace
- Service worker: not present
- Standard Web App Manifest: not present; `app-manifest.json` is a project/host manifest, not a browser PWA manifest
- IndexedDB/localStorage persistence: not present in the reviewed baseline

## Supported formats observed in code and fixtures

- DOCX: open, edit, and export a new DOCX copy
- XLS BIFF8: local import and conversion to XLSX
- XLSX: open, edit, and export a new XLSX copy
- PPTX: open, edit, present, and export a new PPTX copy
- Legacy DOC and PPT: fixtures exist only to verify controlled rejection

## Automated baseline results

| Validation | Result |
|---|---|
| Python unit tests | 39/39 passed |
| Repository validation | Passed; 8 HTML files and 5 JSON files inspected |
| Source audit | Passed under the existing rules |
| Release checksum verification | Passed; 136 files verified |
| JavaScript syntax checks | Passed for all non-vendor JavaScript files |
| DOCX Chromium round-trip script | Passed |
| XLS/XLSX Chromium round-trip script | Passed |
| BIFF8 zero-display Chromium script | Passed |
| PPT/PPTX Chromium round-trip script | 14/14 checks passed |

The four Chromium scripts reported no page-level runtime errors in their covered scenarios.

## Baseline limitations and pre-existing risks

- Browser regression coverage is Chromium-only in this environment.
- No native Firefox, Safari/WebKit, iPadOS, installed-PWA, private-browsing, or denied-storage test was performed.
- No service worker or standard browser manifest exists, so installed PWA mode is not an implemented baseline capability.
- The existing source audit is intentionally lightweight and does not detect transactional open failures, stale save state, XML parser errors, resource exhaustion, or all data-integrity edge cases.
- Generated Python bytecode and historical browser test exports are included in the release package.
- `apps/presentations/app.js` is a large multi-responsibility file.
- Hostile-package resource limits are not consistently enforced.

These limitations are baseline facts, not regressions introduced by the cleanup.

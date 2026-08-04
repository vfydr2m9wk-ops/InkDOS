# InkDesk 0.19.1-beta — Export Verification and Parser Hardening

This focused beta addresses data-integrity and untrusted-file risks without expanding the editing feature set.

## Security and reliability changes

- Replaced false “saved” semantics with shared states: clean, dirty, export preparing, download requested/unverified, failed, and fingerprint-verified.
- Kept unload protection active after a browser download request.
- Added SHA-256 verification when the exact exported copy is reopened.
- Rebuilt DOCX-derived editable DOM through a deny-by-default allowlist; active attributes/elements, dangerous URLs, external resources, unsafe CSS, and clobbering names are removed.
- Removed spreadsheet `Function`/dynamic compilation and added a bounded deterministic arithmetic parser.
- Expanded raw ZIP validation for duplicates/collisions, local/central mismatch, overlap, methods, encryption, ZIP64, truncation, nested archives, and resource limits.
- Added XML DTD/entity rejection and explicit size/complexity budgets.
- Added relationship-target validation and package-inventory comparisons.

## Navigation enhancement in the local test package

- Added one main **Open document** button that routes DOCX, XLS/XLSX, and PPTX to the matching workspace.
- Added home buttons to Documents, Spreadsheets, and Presentations.
- Added hosted IndexedDB and direct-local embedded file handoff paths without introducing a server or remote processing.
- Added mobile title-bar compatibility rules and Chromium checks for route detection, bridge transfer, and home-link targets.
- Reorganized the home information area into three equal responsive cards, removing the unused gray cell visible on tablet layouts.

## Tests and release engineering

- Added malicious/failure-path module tests and a browser hardening scenario with script/network assertions.
- Added deterministic release packaging with exact commit metadata and SHA-256.
- Added Playwright browser-matrix CI for Chromium, Firefox, and WebKit and a manual opt-in prerelease workflow.
- Removed the committed manually generated source ZIP and its bootstrap workflow.

## Upgrade notes

No persisted user-document schema migration is required. Service-worker cache version changes to `inkdesk-shell-v0.19.1-beta-router1`; hosted users may need one reload after activation. Existing exports remain ordinary Office files. See `UPGRADE_NOTES.md`.

## Known limitations

Browser download completion is still not observable; fingerprint verification requires reopening the exported copy. Native Safari/iPadOS behavior, installed PWA flows, advanced OOXML fidelity, large-file memory pressure, and exhaustive fuzzing remain unverified. This release is not a 1.0 candidate.

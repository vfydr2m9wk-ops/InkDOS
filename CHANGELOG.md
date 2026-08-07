# Changelog

## 0.20.2 — Data Safety and Browser Matrix (2026-08-07)

- Added bounded, private IndexedDB recovery snapshots to Documents, Spreadsheets and Presentations.
- Added explicit Restore, Open normally and Discard recovery choices without overwriting the original file.
- Recovery keeps at most three snapshots per document, twelve per workspace, and removes snapshots older than thirty days.
- Successful copy download clears the active recovery history.
- Added a Playwright browser-selection layer and an explicit Chromium/Firefox/WebKit matrix command while keeping normal update validation Chromium-only for predictable runtime.
- Added behavioral and structural regression coverage for data safety.
- Removed duplicate full-validation passes from the incremental updater; the complete release gate now runs once.
- Canonicalized cache-busted application-shell requests in the service worker so versioned assets remain available offline.
- Corrected the Playwright local-recovery regression to pass `wait_for_function` arguments using the current keyword-only API.

## 0.20.1 — Consistency Refinement 1 (2026-08-06)

- Corrected v0.20.1 package: explicit favicons for all workspaces and URL-aware HTTP failure diagnostics.


- Restored the permanent Home control in Documents and Presentations.
- Restored normal spreadsheet range selection by click-and-drag.
- Isolated formula-reference capture from ordinary grid selection.
- Added static and Chromium regression gates for these functions.
- Synchronized the public version and service-worker cache.


## 0.20.0 — 2026-08-06

- Consolidated the 0.19.4 modular development sequence.
- Reworked the home page around six compact workspace cards.
- Added the Plain Text editor and EPUB Reader to the complete distribution.
- Standardized public version metadata, cache naming and release documentation.
- Reset incremental development state for the 0.20.x series.

## [0.19.0-beta] - 2026-08-03

### Fixed

- Preserved zero-valued spreadsheet formulas in the grid and page view while retaining explicit hide-zero formats.
- Made DOCX, XLS/XLSX, and PPTX opening transactional so a corrupt replacement file does not destroy the active in-memory document.
- Separated the editable DOCX filename from the browser's read-only `File.name` property.
- Added Undo/Redo history for presentation text edits.
- Invalidated stale spreadsheet export state after edits and recalculated after paste.
- Improved save failure reporting and removed wording that falsely implied a browser download had completed.
- Revoked temporary object URLs at controlled lifecycle boundaries.

### Security and reliability

- Added shared ZIP/OOXML package limits for compressed size, entry count, expanded size, compression ratio, unsafe paths, encryption, ZIP64, malformed offsets, and XML parser errors.
- Added controlled filename sanitation and shared download handling.
- Replaced empty or silent catches with contextual diagnostics where safe.

### Architecture

- Consolidated byte-identical JSZip 3.10.1 and pako 1.0.11 copies under `shared/vendor/` with retained license notices.
- Added `shared/office-runtime.js` for genuinely shared package, XML, filename, download, and object-URL behavior.
- Added a standard web manifest, guarded service-worker registration, and a same-origin application-shell cache without changing `file://` behavior.

### Testing and documentation

- Expanded the Python suite from 39 to 43 tests.
- Added browser regressions for package guards, transactional open failure, restricted APIs/touch emulation, cross-workspace isolation, DOCX rename, presentation text Undo/Redo, and zero visibility in page view.
- Expanded static validation for PWA assets, CSS references, casing, source maps, generated artifacts, canonical vendor files, and runtime paths.
- Synchronized architecture, compatibility, security, testing, dependency, limitation, and release documentation.

### Preserved

- Existing user-facing layout and workflows.
- Local-first/offline-capable operation without a backend.
- Focused DOCX, XLS/BIFF8, XLSX, and PPTX behavior and package-preserving export strategies.

- Fixed release checksum verification after the incremental updater changes `DEVELOPMENT_STATE.json`.
### v0.20.2 correction 2

- Restored the Presentations format panel as a responsive compact-width drawer.
- Separated local-recovery validation from presenter-notes visibility.
- Added dedicated Presentations control behavior regression.
- Added a persistent functional acceptance inventory/checklist for all visible controls.


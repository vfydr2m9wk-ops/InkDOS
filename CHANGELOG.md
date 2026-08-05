# Changelog

## [0.19.2-beta] - 2026-08-04

### Packaging and release

- Added a manual full-replacement workflow that deletes the prior worktree, copies the source archive in full, force-updates `main`, moves the version tag, and replaces release assets without comparing prior files.
- Fixed source-package checksum coverage so every distributable source file except the checksum manifest itself is verified.
- Updated version metadata, cache keys, release notes, upgrade notes, and validation documentation.

### Privacy

- Removed tool-generated personal-name metadata from synthetic Office compatibility fixtures.
- Added a repeatable package privacy/readiness audit report.

### Status

- Retained beta status because native Safari/iPadOS, installed-PWA, Firefox/WebKit, memory-pressure, and post-hardening real-corpus validation remain incomplete.

## [0.19.1-beta] - 2026-08-04

### Data integrity

- Replaced the three independent save flags with a shared lifecycle model: clean, dirty, export-preparing, download-requested-unverified, export-failed, and export-verified.
- Kept `beforeunload` protection active after a browser download request.
- Added SHA-256 and byte-length verification when the exact generated copy is reopened.
- Added package-inventory checks and open-edit-export-reopen coverage for DOCX, XLS/XLSX, and PPTX.

### Security

- Added raw ZIP central/local-header validation, normalized collision detection, overlap checks, conservative resource limits, relationship validation, and controlled errors before JSZip processing.
- Added XML byte, aggregate, depth, node, attribute, and attribute-length limits with DTD/entity rejection.
- Rebuilt DOCX-derived editable content through a deny-by-default DOM allowlist.
- Replaced spreadsheet `Function` construction with a deterministic limited expression parser.

### Navigation and local opening

- Added one prominent **Open document** action on the main index that detects DOCX, XLS, XLSX, or PPTX and selects the correct workspace.
- Added a house-shaped InkDesk home button to all three workspace title bars and to the Presentations start screen.
- Added a temporary IndexedDB handoff for hosted/PWA navigation and an in-page `postMessage` file bridge for direct `file://` launches where cross-page storage is unreliable.
- Added narrow-screen rules that preserve the home, new, open, and save controls without overlapping the document title.
- Reorganized the home-page information panel into three equal responsive columns, removing the unused fourth cell visible on tablet layouts.

### Architecture, CI, and release

- Added shared lifecycle, formula, safe-DOM, package-inventory, fingerprint, and download-safety modules.
- Added adversarial Node/Python/browser tests and split browser CI into isolated Playwright engine/scenario groups.
- Added deterministic tagged runtime packaging, checksums, exact commit metadata, prerelease preparation, and explicit opt-in publication.
- Removed the manually committed source ZIP/bootstrap workflow.

### Post-audit hardening refresh

- Bound HTTP(S) frame handoff messages to exact origins and validated both message origin and source.
- Added bridge protocol versioning, token expiration, one-time consumption, receipt acknowledgement, deterministic cleanup, and a documented isolated `file://` opaque-origin exception.
- Replaced wildcard-message regex auditing with a nesting-aware JavaScript call scanner and adversarial scanner tests.
- Corrected service-worker query-key handling, incomplete-cache cleanup, cache failure reporting, shell-only caching, and recovery messaging.
- Required clean tagged Git checkouts for official builds and added an included-file manifest, SPDX SBOM, and double-build byte comparison.
- Expanded the Python suite to 53 tests and retained 11 passing Chromium browser regression scripts.

### Documentation

- Documented unverified download semantics, package/XML limits, formula scope, actual validation evidence, device test boundaries, known limitations, upgrade notes, and release procedures.

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

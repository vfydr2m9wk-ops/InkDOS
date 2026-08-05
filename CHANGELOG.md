# Changelog

## 0.19.3-beta.7 — 2026-08-05

- Restored PDF startup for downloaded packages opened directly through `file://` by switching from an ES-module entry point to the official classic PDF.js 3.11.174 distribution.
- Verified the **Open PDF** button, hub-to-PDF local handoff, selectable text, five AcroForm controls and outline navigation under normal Edge security settings.
- Added determinate, staged PPTX opening progress with byte and slide counts.
- Made `=` on a selected spreadsheet cell open the formula bar and show function suggestions immediately.
- Added regression coverage for classic PDF assets, local-file compatibility, presentation progress and direct formula discovery.
- Added `check_no_legacy_runtime.py` and a simple `main` GitHub Actions workflow so retired PDF mechanisms cannot silently return.
- Removed stale native-viewer selectors and identifiers from the PDF source instead of merely leaving them unused.

## 0.19.3-beta.6 — 2026-08-05

- Replaced the native PDF embed with bundled PDF.js 4.10.38 and a local worker.
- Added selectable text, PDF.js form layers, synchronized page navigation, lazy thumbnails, outline destinations and vertical/horizontal page layouts.
- Limited full PDF canvases to the current page plus two neighbors on each side and capped canvas pixels.
- Attached InkDesk review annotations to normalized page coordinates and separated JSON review export from supported PDF saving.
- Added spreadsheet drag selection, formula autocomplete, Excel-style shortcuts and an expanded local formula set.
- Updated tests, documentation, SPDX inventory, manifests and privacy checks.

## 0.19.3-beta.5 — 2026-08-05

- Changed only the PDF Workspace runtime, PDF tests, documentation and release metadata.
- Reverted the beta.4 `iframe` preview regression that produced a gray surface in Safari-compatible/WebKit hosts.
- Restored a single native `object`/`embed` bridge and remounts it with a fresh short-lived object URL for each page, zoom or viewing-mode command.
- Preserved bounded file inspection, the 61-entry page window, 50%–400% zoom and full-screen recovery from beta.4.
- Corrected page-total detection so unrelated outline/name-tree `/Count` values are not mistaken for page counts.
- Verified the reported external 13-page PDF as 13 pages, with one object, one embed, zero iframes and a direct page-7 target; the private test file is not included in the package.

## 0.19.3-beta.4 — 2026-08-05

- Changed only the PDF Workspace runtime, PDF tests and release metadata.
- Removed full-file PDF byte duplication and whole-document text conversion during opening.
- Added bounded file-slice inspection and bounded fingerprinting for large PDFs.
- Removed nested native PDF thumbnail objects and limited the page navigator to a 61-entry moving window.
- Rebuilds a single native PDF iframe for every page or zoom command so page fragments are reapplied reliably.
- Expanded zoom to 50%–400% and corrected full-screen/immersive exit recovery.
- Added a synthetic 4,000-page PDF regression fixture and direct page-3,500 navigation test.

## 0.19.3-beta.3 — 2026-08-05

- Fixed the hub file selector so PDF is selectable and routed to the PDF Workspace.
- Replaced the iframe-only PDF preview with a native `object`/`embed` bridge plus a system-viewer fallback.
- Added page navigation, page jump, zoom presets, outline inspection, page preview cards, vertical/horizontal modes and fullscreen/immersive viewing.
- Added local review highlights, underlines, marker regions, comments, inserted text, personal bookmarks, Undo and anonymized sidecar import/export.
- Added native AcroForm/widget detection and preserved native form interaction while review tools are inactive.
- Added UTF-8 BOM removal and NFC package-path normalization for DOCX/OOXML XML parsing.
- Added synthetic AcroForm/outline PDF and BOM-DOCX regression fixtures.
- Updated repository presentation images and deterministic release metadata.

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

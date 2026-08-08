## 0.20.2.22 — Spreadsheet Formula Draft Safety Hardening (2026-08-07)

- Added `apps/spreadsheets/formula-safety.js` as the workbook-level guard for pending formula drafts.
- Prevented Save from creating an XLSX copy while a formula draft is still pending, avoiding silent omission of visible draft text.
- Made New, Open and before-unload treat pending formula drafts as unsaved work.
- Reset formula drafts after a confirmed workbook replacement, while preserving the current draft when a replacement file fails to parse.
- Added deterministic session/safety tests and extended the Spreadsheet Chromium consistency regression without changing the browser-script count.

## 0.20.2.21 — Spreadsheet Formula Session Lifecycle Decomposition (2026-08-07)

- Moved persistent formula draft storage and lifecycle transitions into `apps/spreadsheets/formula-session.js`.
- Added DOM-free tests for start, update, suspend, resume, commit cleanup and cancel cleanup.
- Reduced the `formula-editor.js` architecture ratchet from 616 to 586 lines.
- Preserved visible Spreadsheet behavior and the existing 17 Chromium regression scenarios.

## 0.20.2.20 — Spreadsheet Formula Model Decomposition (2026-08-07)

- Moved deterministic Spreadsheet formula-session helpers and function metadata into `apps/spreadsheets/formula-model.js`.
- Preserved the existing `InkDeskFormulaEditor` helper API while reducing `formula-editor.js` from 756 to 616 lines.
- Added independent formula-model invariants and load-order/offline-cache regression checks.
- Preserved visible Spreadsheet behavior and the existing 17 Chromium regression scenarios.

## 0.20.2.19 — TXT Editor Interaction Decomposition (2026-08-07)

- Extracted TXT Undo/Redo snapshot history to `apps/txt/history-controller.js`.
- Extracted TXT Find bar/search behavior to `apps/txt/find-controller.js`.
- Reduced `apps/txt/app.js` from 591 to 457 physical lines and removed its grandfathered architecture-debt entry.
- Added deterministic load order, offline precache and permanent structural/behavioral coverage for both controllers.
- No visible UI, encoding, line-ending, save, dirty-state or workflow behavior change is intended.

## 0.20.2.18 — Shared Workspace Contract Consolidation (2026-08-07)

- Consolidated workspace module detection, session-backed panel preference resolution and layout-ready notification into `shared/ui/workspace-panel-controller.js`.
- Preserved the existing `InkDeskWorkspaceLayout` helper API through delegation.
- Reduced `shared/ui/workspace-layout.js` from 541 to 492 physical lines and removed its final grandfathered architecture-debt entry.
- Kept Documents ruler DOM synchronization, model and drag behavior unchanged.
- No visible UI, file-format, save, recovery or workflow behavior change is intended.

## 0.20.2.17 — Documents Ruler Interaction Decomposition (2026-08-07)

- Extracted Documents ruler pointer-drag lifecycle to `shared/ui/document-ruler-drag-controller.js`.
- Kept ruler DOM synchronization/rendering and observers in `shared/ui/workspace-layout.js`; pure geometry remains in `document-ruler-model.js`.
- Added deterministic load order and offline precache for the new drag controller.
- Lowered the `workspace-layout.js` architecture ratchet from 710 to 541 physical lines; the new controller is 252 lines.
- No visible UI, DOCX, save, panel or workflow behavior change is intended.

## 0.20.2.16 — Documents Ruler Model Decomposition (2026-08-07)

- Extracted pure Documents ruler geometry, tick generation and indentation calculations to `shared/ui/document-ruler-model.js`.
- Kept ruler DOM synchronization, observers and pointer-drag interaction in `shared/ui/workspace-layout.js`.
- Preserved the existing `InkDeskWorkspaceLayout` ruler-helper API through delegation and added deterministic script load order/offline precache.
- Lowered the `workspace-layout.js` architecture ratchet from 1,009 to 710 physical lines; the new model remains below 500 lines.
- No visible UI, DOCX, save, panel or workflow behavior change is intended.

## 0.20.2.15 — 2026-08-07

### Shared Workspace Panel Decomposition

- Moved Documents, Presentations, PDF and Spreadsheet shared panel/layout-state behavior into `shared/ui/workspace-panel-controller.js`.
- Kept Documents ruler geometry and interaction in `shared/ui/workspace-layout.js`, reducing that grandfathered file from 1,270 to 1,009 physical lines.
- Added deterministic controller loading, offline precache and architecture ownership tests without changing visible panel defaults or controls.

## 0.20.2.14 — 2026-08-07

- Extracted the shared document-session implementation into `shared/ui/document-session-controller.js`.
- Preserved editable filenames, dirty-state bridging, discard warnings and download-name rewriting across all six workspaces.
- Reduced `shared/office-shell.js` from 617 to 315 physical lines and retired its inherited architecture-debt entry.
- Added permanent structural coverage and offline precaching for the new shared UI boundary.
- No visual, editor, file-format, save-path or workflow behavior change is intended.

## 0.20.2.13 — 2026-08-07

- Extracted unified PDF save/download coordination into `apps/pdf/io/save-controller.js`.
- Preserved the PDF.js structure-preserving save path and flattened annotated-export path behind the new boundary.
- Reduced `apps/pdf/app.js` below the normal 500-line runtime ceiling and removed its grandfathered debt entry.
- Added permanent structural and isolated Chromium coverage for both PDF save paths.
- Preserved the existing PDF UI, local-review persistence and original-file safety behavior.

## 0.20.2.11 — 2026-08-07

- Extract PDF navigation, page-list thumbnails, outline destinations, bookmark navigation and sidebar tab state into `apps/pdf/viewer/navigation-controller.js`.
- Add an isolated PDF navigation browser regression and permanent architecture-boundary test.
- Tighten the PDF `app.js` ratchet again without changing visible behavior.

## 0.20.2.10 — 2026-08-07

- Extract PDF page rendering/virtualization into `apps/pdf/viewer/page-renderer.js`.
- Add isolated PDF rendering/navigation browser regression and architecture boundary test.
- Tighten the PDF `app.js` ratchet without changing visible behavior.

## 0.20.2.8 — Presentations I/O and Recovery Decomposition (2026-08-07)

## 0.20.2.10 — Presentations Architecture Consolidation

- Extracted package-preserving PPTX write/patch logic from the Presentations entry point into `apps/presentations/io/pptx-write-adapter.js`.
- Kept imported PPTX slide patching, notes patching, new shape/image serialization and source-order checks behaviorally unchanged behind the new adapter.
- Tightened the Presentations `app.js` architecture ratchet and added permanent modular-boundary tests.
- No visual redesign, new editor feature or deliberate PPTX behavior change.


- Extracted PPTX open/save orchestration and imported source-buffer ownership to `apps/presentations/io/file-controller.js`.
- Extracted local recovery capture/restore and recovery-manager lifecycle to `apps/presentations/io/recovery-controller.js`.
- Lowered the Presentations `app.js` architecture ratchet to 714 physical lines / 70 long lines.
- Updated offline precache, browser harnesses and structural tests for the new ownership boundary.
- No visual or intentional file-format behavior change.

# Changelog

## 0.20.2.7 — Update Flow Hardening (2026-08-07)

- Changed updater dry-run semantics from plan-only to full validation against a disposable candidate repository while leaving the source checkout untouched.
- Added package SHA-256 to updater reports and documented artifact-identity checks for correction attempts.
- Added incremental checksum tooling that preserves undeclared hosted-tree hashes instead of regenerating the entire manifest from an incomplete local reconstruction.
- Isolated Presentations slideshow behavior in its own browser regression process/context with explicit tab state.
- Added permanent regressions for dry-run safety, incremental checksum preservation and slideshow-harness isolation.
- No editor runtime, visual, file-format, save or recovery behavior change is intended.

## 0.20.2.6 — Presentations Slideshow Decomposition (2026-08-07)

- Extracted slideshow/presentation-mode lifecycle into `apps/presentations/presentation/slideshow-controller.js`.
- Moved from-start/from-current entry, keyboard and pointer navigation, counter/help state, slide fitting, transition animation and Fullscreen API fallback handling out of `app.js`.
- Extended the Presentations behavioral regression to prove slideshow start/current entry, Home/End/Arrow navigation, Escape and visible Exit behavior.
- Updated offline precaching and manual browser harnesses so the slideshow component loads before `app.js`.
- Lowered the Presentations `app.js` architecture ratchet again with no intended visual, PPTX, save or recovery behavior change.

## 0.20.2.5 — Presentations State and Selection Decomposition (2026-08-07)

- Extracted object-selection ownership and pointer drag/resize/rotate interactions into `apps/presentations/state/selection-controller.js`.
- Extracted snapshot capture, bounded Undo/Redo stacks and history-button synchronization into `apps/presentations/state/history-controller.js`.
- Extended the Presentations behavioral regression to prove clear/reselect plus Undo/Redo restoration after formatting.
- Updated offline precaching and manual browser harnesses so both state components load before `app.js`.
- Lowered the Presentations `app.js` architecture ratchet again with no intended visual, PPTX, save or recovery behavior change.

## 0.20.2.4 — Presentations Navigation and Notes Decomposition (2026-08-07)

- Extracted slide-thumbnail rendering and thumbnail visibility into `apps/presentations/ui/thumbnails-controller.js`.
- Extracted presenter-notes rendering, character count, input/debounce behavior and panel visibility into `apps/presentations/ui/presenter-notes-controller.js`.
- Preserved the existing visual contract, default panel visibility, PPTX behavior and recovery semantics.
- Updated offline precaching and manual browser harnesses so both new components are exercised by the existing regression paths.
- Lowered the Presentations `app.js` architecture ratchet again; no editing command or file-format behavior is intentionally changed.

## 0.20.2.3 — Presentations Inspector Decomposition (2026-08-07)

- Extracted the Presentations Format/Inspector behavior into `apps/presentations/ui/inspector-controller.js`.
- Preserved the existing closed-by-default desktop/compact panel contract, accessibility state, Escape handling and format-property behavior.
- Updated manual browser harnesses and offline precaching so the new component is exercised in the same regression paths as `app.js`.
- Lowered the Presentations `app.js` architecture ratchet after the extraction and added permanent modularization tests.
- No editing command, visual redesign or file-format behavior is intentionally changed.

## 0.20.2.2 — Refactoring Guardrails (2026-08-07)

- Added repository-level AI/human guardrails and a behavior-neutral refactoring contract.
- Added a source-size/readability ratchet for inherited runtime debt and strict limits for new runtime files.
- Added cross-workspace/shared dependency and relative import-cycle checks to the release gate.
- Recorded the native modular runtime decision and ordered 0.20.x decomposition sequence.
- No editor feature or visual redesign is intentionally included.


## 0.20.2.1 — Functional Corrections (2026-08-07)

- Removed stale Home preview/status copy and synchronized the visible beta version.
- Added top-title rename behavior to Spreadsheets and Presentations.
- Removed the obsolete visible PDF.js forms note while preserving form support.
- Normalized TXT/EPUB primary title bars to the 44 px Office reference.
- Added permanent functional-correction regressions.

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


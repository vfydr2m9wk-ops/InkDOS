# Structural Audit — InkDesk 0.19.0-beta

> Historical baseline. The dynamic formula construction described below was removed in 0.19.1-beta; see `docs/VALIDATION_REPORT.md` for current evidence.

## Severity model

- **Critical:** probable data loss, corruption, stale export, or cross-document contamination.
- **High:** broken core workflow, unsafe untrusted-input handling, or materially misleading save state.
- **Medium:** maintainability, compatibility, or reliability defect with a practical workaround.
- **Low:** localized quality issue with limited runtime impact.
- **Informational:** observed limitation or future design concern.

## Findings and results

| Severity | File / location | Problem | Practical consequence | Correction | Regression risk | Validation result |
|---|---|---|---|---|---|---|
| Critical | `apps/spreadsheets/app.js`, cell/page rendering | Formula results equal to numeric zero were treated as falsy/empty in some views. | Valid results could disappear, creating incorrect financial or analytical output. | Replaced truthiness checks with explicit empty/missing checks while preserving number formats that intentionally hide zero. | Medium | Zero, positive, negative, empty, and hidden-zero scenarios passed in grid, page view, export, and reopen tests. |
| Critical | `apps/documents/app.js`, open flow | A failed DOCX parse could partially replace or clear active state. | A user could lose access to unsaved in-memory work after selecting a corrupt file. | Parse/render into temporary state and commit only on success; restore prior state and release temporary URLs on failure. | Medium | Corrupt-open regression preserved the active document and its exported marker. |
| Critical | `apps/presentations/app.js`, open/save flows | Failed PPTX open or preservation-mode save could mutate source/package state before completion. | Active content or the next save could use partially changed state. | Added transactional snapshots and rollback for imported package, identifiers, theme, and presentation model. | Medium | Failed-open and save-preservation regressions passed without page errors. |
| High | `apps/documents/app.js`, rename | The code attempted to assign to read-only `File.name`. | Console exception and divergence between displayed and exported filenames. | Added separate editable `currentFileName` state; the source `File` remains immutable. | Low | Rename, save, package reopen, and cross-workspace isolation passed. |
| High | `apps/presentations/app.js`, text editing | Text edits set dirty state but did not create an Undo/Redo history entry. | A core editing operation could not be reversed reliably. | Capture a pre-edit snapshot and commit one history entry on blur when text changes. | Medium | PPTX regression now verifies text edit, Undo, and Redo. |
| High | OOXML parsers and writers | ZIP entry count, expansion, unsafe paths, malformed offsets, encryption, and excessive ratios were not consistently bounded. | Hostile packages could consume excessive memory or exploit unsafe assumptions. | Added shared input/package limits and malformed-package guards before model commit. | Medium | Safe package accepted; unsafe path, control path, empty ZIP, malformed offset, count, size, XML, encryption/ZIP64 markers, and filename tests passed where represented. |
| High | Workspace save/download handlers | Some messages implied a completed save when only a browser download request had been issued; object URLs were not consistently revoked. | False success indication and avoidable memory retention. | Centralized download request, filename sanitation, honest wording, and URL revocation. | Low | Export/reopen tests passed; no new console errors were observed. |
| Medium | `apps/spreadsheets/app.js`, dirty/export state | Cell paste/recalculation and pending export Blob invalidation were inconsistent. | A later download could contain stale workbook content. | Recalculate after paste and invalidate pending export whenever the workbook becomes dirty or save UI closes. | Medium | Edited workbook markers and formulas survived save/reopen. |
| Medium | All workspace vendor directories | JSZip and pako were duplicated three times. | Version drift, larger package, and repeated license/update work. | Consolidated exact existing bytes under `shared/vendor/` with canonical notices. | Low | Hash checks, local references, repository validation, and all workspace regressions passed. |
| Medium | Repository/PWA metadata | Documentation described installable use, but no standard manifest or service worker existed. | Installation/offline-hosting claims were not backed by implementation. | Added a standard manifest, guarded registration, and same-origin application-shell service worker. | Medium | Manifest/service-worker/static-asset checks passed; native installation/offline reload was not performed due environment policy. |
| Medium | Test/release package | Generated results, Python bytecode, and historical test exports could enter the release and checksums. | Noisy source package and non-reproducible checksums. | Expanded ignore/exclusion rules and made generated evidence non-distributable. | Low | Validation rejects duplicate vendor/generated release artifacts; final ZIP inspection is part of release validation. |
| Medium | `beforeunload` and failure reporting | Some paths prompted even when clean or swallowed contextual errors. | Unnecessary prompts and difficult diagnosis. | Prompt only when dirty; replace empty/silent catches with contextual warnings at safe boundaries. | Low | Source audit reports no empty catch blocks; workflow tests pass. |
| Low | `apps/documents/app.js` | `countDocumentss` and implicit outline indexes reduced clarity. | Maintenance errors and difficult search/refactoring. | Renamed to `countWords` and made indexes explicit. | Low | Syntax/unit/browser checks passed. |
| Resolved in 0.19.1-beta | `apps/spreadsheets/app.js`, `shared/formula-engine.js` | The 0.19.0-beta baseline used restricted dynamic function construction. | Dynamic compilation increased review risk. | Replaced by a deterministic limited parser with resource limits and regression tests. | Medium | Current source audit and formula injection tests pass. |
| Informational | `apps/presentations/app.js` | The file remains a large multi-responsibility module. | Future changes have a wider review surface and higher merge risk. | No large rewrite performed; incremental extraction is recommended after behavior coverage expands. | High if changed broadly | Current behavior is covered; no modularization claim is made. |
| Informational | Whole application | No persisted recovery store exists. | A browser/process crash can lose unsaved in-memory edits. | Documented as unsupported; design a privacy-preserving opt-in recovery layer before stable 1.0. | High | Denied IndexedDB/localStorage fallback passed because core workflows do not depend on them. |

## Overall condition

The project has a coherent static-client foundation, explicit workspace directories, local dependencies, package-preserving OOXML strategies, and meaningful automated regression coverage. The cleanup removed several data-integrity defects without redesigning the interface or introducing a build framework.

The remaining risks are dominated by untested native browser/device environments, incomplete crash recovery, partial Office fidelity, and the size of the Presentation Workspace controller. A broad rewrite is not recommended.

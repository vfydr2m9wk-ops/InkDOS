# Validation Report — InkDesk 0.19.0-beta

## Review environment

- Review date: 2026-08-03
- Python: 3.13.5
- Node.js: 22.16.0
- npm: 10.9.2
- Playwright: 1.57.0
- Automated browser: system Chromium
- Native Firefox, Safari/WebKit, iPadOS, and embedded hosts: unavailable
- Direct `file://` and localhost browser navigation: blocked by an administrative Chromium policy

The original unmodified baseline is recorded separately in `docs/BASELINE_REPORT.md`.

## Final static and unit results

| Check | Final result |
|---|---|
| Repository/metadata validation | Passed |
| HTML files validated | 8 |
| JSON/web manifest files validated | 5 |
| First-party JavaScript syntax | Passed |
| CSS/local asset references | Passed |
| Duplicate HTML IDs | None detected |
| Case-sensitive filename conflicts | None detected |
| Service-worker app-shell paths | Passed |
| Automatic remote runtime dependency audit | None detected |
| Empty catch block audit | None detected |
| Unit/package test suite | 43/43 passed |
| Release checksums | Passed after final regeneration |

The source audit reports one manual-review note: the Spreadsheet Workspace retains a strictly allowlisted arithmetic preview implemented with dynamic function construction. It is not fed arbitrary imported JavaScript, but it remains a documented review item.

## Browser regression results

Eight of eight Chromium/Playwright scripts passed:

| Script | Verified scope |
|---|---|
| `revalidate_office_runtime_guards.py` | Safe package acceptance; empty/unsafe/malformed/excessive package rejection; invalid XML; filename sanitation; no page errors |
| `revalidate_docx_three_eras.py` | DOCX open/edit/export/reopen across the maintained fixture eras; supported part preservation; no runtime errors |
| `revalidate_xlsx_three_eras.py` | BIFF8 import and XLSX open/edit/export/reopen; worksheets, formulas, images, hidden sheets, tables, validations, and advanced parts represented by fixtures |
| `revalidate_xls_zero_formula_display.py` | Zero values visible in grid and page view unless explicitly hidden by number format; values preserved after XLSX export |
| `revalidate_pptx_three_eras.py` | 18/18 checks, including text edit Undo/Redo, package preservation, presentation behavior, and no runtime errors |
| `revalidate_transactional_open_failures.py` | Corrupt replacement input preserved the active Document, Spreadsheet, and Presentation state |
| `revalidate_cross_workspace_isolation.py` | Three simultaneous workspaces, five switch rounds, isolated filenames/history/content, independent exports, and no page errors |
| `revalidate_launch_and_offline_modes.py` | Required static HTTP assets served; restricted-API/touch fallbacks passed; presentation mode exited without fullscreen support |

## Repeated final release loop

**Three consecutive complete release-validation cycles passed**. Cycle durations were 37.1 seconds, 53.0 seconds, and 41.5 seconds. Every cycle passed repository validation, source audit, 43/43 unit/package tests, 8/8 browser scripts, and verification of all 143 distributed-file checksums.

A pass is counted only when repository validation, source audit, all 43 unit/package tests, all eight browser scripts, and checksum verification complete successfully in the same cycle.

## Data-integrity evidence

- The active document survives a failed open in all three workspaces.
- DOCX rename is stored separately from the immutable source `File` object and is used by export.
- Spreadsheet zero, empty string, hidden-zero format, and positive values remain distinguishable in the represented tests.
- Export uses the current model after edits rather than a stale pending Blob in the tested spreadsheet scenarios.
- Presentation text edits participate in Undo/Redo history.
- Cross-workspace markers, filenames, histories, and exported OOXML packages remained isolated.
- Exported DOCX, XLSX, and PPTX fixtures reopened successfully in the project parsers.
- No page-level runtime errors were reported by the final browser scripts.

## Compatibility not performed

The following were not executed and are not claimed:

- native Firefox;
- native Safari/WebKit;
- physical iPadOS touch, keyboard, pointer, orientation, background/return, and download behavior;
- embedded local-file browser hosts;
- actual browser PWA installation and browser-controlled offline reload;
- private-browsing behavior in native target browsers;
- complete Microsoft Office fidelity;
- exhaustive fuzzing or arbitrary hostile-file safety.

## Final validation conclusion

The tested core is materially stronger than the baseline and no critical save, stale-export, zero-value, failed-open, or cross-workspace-contamination defect remains known in the executed scenarios. The evidence supports **Beta quality**, not a stable 1.0 recommendation, because important target engines/devices and crash recovery remain unvalidated or unimplemented.

# InkDesk v0.20.2.1 — Functional Corrections

Released: 2026-08-07

This correction patch is intentionally narrow. It adds no new formats or editing tools.

## Corrected

- Simplified Home by removing the obsolete consolidated-preview copy and replacing the stale footer sentence with `v0.20.2.1 beta`.
- Added editable workbook filenames in Spreadsheets; rename updates the XLSX copy name and participates in dirty/recovery state.
- Added editable presentation filenames in Presentations; rename updates PPTX copy names and participates in dirty/recovery state.
- Removed the obsolete visible `Forms: PDF.js` note without removing AcroForm support.
- Normalized TXT and EPUB primary title bars to the 44 px Office reference and kept them single-row at compact widths.
- Added permanent regression checks for these corrections.

## Preserved

- v0.20.2 local recovery, offline behavior and Presentations Format-panel fixes.
- Stable external workflow policy; update ZIPs still contain no `.github/workflows` files.

## Hosted validation correction 2

- Fixed a real PDF start-screen/pagehide race: delayed resize work now exits when no PDF document is active and pending resize work is cancelled during close.
- Updated the cumulative cross-workspace isolation regression for the editable Spreadsheet and Presentation filename controls introduced in 0.20.2.1. The test now reads input values (including the file extension) instead of legacy span text.
- Added permanent unit regressions for both hosted failures. No workflow changes are included.


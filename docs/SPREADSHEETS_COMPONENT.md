# Spreadsheets Component

## Entry point

`apps/spreadsheets/index.html`

## Main source files

- `app.js` — workbook state, grid interaction, focused formulas, drawing previews and export workflow.
- `xls-biff8-engine.js` — focused offline OLE/BIFF8 importer for Excel 97–2004 `.xls`.
- `xlsx-engine.js` — offline XLSX parser, package-preserving writer and XLS-to-XLSX package builder.
- `styles.css` — grid, page, chart, table, toolbar, start screen and save-dialog styling.
- `vendor/` — bundled JSZip and pako browser builds.

## Focused compatibility path

The offline runtime accepts `.xlsx` directly and imports Excel 97–2004 BIFF8 `.xls` locally. Legacy XLS is converted in memory to the editor model and Save creates a new `.xlsx` copy. No network service, remote conversion endpoint or build step is required.

## Package-preserving save

For an imported workbook, Save creates a clone of the original ZIP package and patches only changed worksheet data. Unedited OOXML parts and worksheet structures are retained, including drawings, images, chart parts, tables, filters, panes, page settings, validation, conditional formatting, defined names and extension markup.

A blank workbook is generated from a compact standard XLSX package. The upper-right Save button always downloads a new copy and does not overwrite the source.

## Modern preview scope

The editor provides focused local previews for `XLOOKUP`, `FILTER` and `LET`, basic column/bar charts, hidden-sheet state and structured table regions. These previews do not replace the spreadsheet application's own calculation engine. The original formulas are retained and the workbook is marked for recalculation when opened by a full spreadsheet suite.


## Excel 97–2004 import

Version 0.19.0-beta retains the BIFF8 `.xls` import introduced in 0.18.6 and makes cached formula-zero display format-aware. The importer covers worksheet names and visibility, shared strings, numeric and boolean values, cached formula results, cell styles, merged ranges, row heights, column widths, page margins/setup, embedded PNG/JPEG images and text boxes.

The original binary file is never overwritten. Save always creates an `.xlsx` copy. Formula token streams, VBA macros, ActiveX controls, legacy charts and unsupported embedded OLE objects are not converted. Formula cells are imported from their cached displayed result so that the workbook remains readable without claiming full formula compatibility. Cached zero results are visible unless the original number format explicitly defines an empty zero section.

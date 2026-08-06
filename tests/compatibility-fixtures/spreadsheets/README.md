# Spreadsheet compatibility fixtures

These files contain generated test data only. They do not contain private user information.

- `era1_office_97_2003_legacy.xls` — controlled BIFF8/OLE fixture used for the public legacy import workflow.
- `era2_office_2007_2013_baseline.xlsx` — baseline OOXML workbook with formulas, merges, dimensions, an image and page settings.
- `era3_office_2016_365_modern.xlsx` — modern OOXML workbook with formulas, table, chart, hidden sheet, validation and conditional formatting.
- `independent_libreoffice_biff8_stress.xls` — independently produced through LibreOffice from a generated XLSX workbook. It contains a 10,520-character Unicode shared string crossing BIFF CONTINUE records, 179 subsequent shared strings, cached formulas, a hidden sheet, styles, landscape page setup and a PNG image.
- `independent_biff8_zero_formula_display.xls` — independently converted through LibreOffice and designed to distinguish formula-derived zero, literal zero, visible-zero formats, hidden-zero formats and a nonzero cached formula result.

The XLS fixtures are import-and-convert tests. The project never claims binary XLS round-trip output; saving creates a new XLSX copy.

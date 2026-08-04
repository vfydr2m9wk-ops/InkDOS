# Tests

The tests use synthetic OOXML packages plus public BIFF8 fixtures created for this repository and an independent LibreOffice-generated stress workbook. They contain no private user content, proprietary fonts or third-party document material.

Run the fast repository and fixture suite:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Optional browser round-trip tests require Playwright, Beautiful Soup and a local Chromium executable:

```bash
python3 tests/browser/revalidate_docx_three_eras.py
python3 tests/browser/revalidate_xlsx_three_eras.py
python3 tests/browser/revalidate_xls_zero_formula_display.py
python3 tests/browser/revalidate_pptx_three_eras.py
```

The browser scripts exercise DOCX, XLS/BIFF8, XLSX and PPTX workflows. The BIFF8 zero-display regression verifies format-aware formula and literal zero rendering, XLSX export and application reopen. The spreadsheet script imports legacy XLS, exports XLSX, reopens the copy and checks the edited marker and embedded image. Native Safari/iPadOS/WebKit testing remains a separate platform validation step.

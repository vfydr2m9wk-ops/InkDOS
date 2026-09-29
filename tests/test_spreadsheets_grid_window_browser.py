#!/usr/bin/env python3
"""Regression: the spreadsheet grid shows every row of the file and keeps only the visible cells in the DOM.

The grid created an element for every cell of the sheet, so each click, arrow key and edit restyled and
relaid out thousands of elements (the heaviest CPU user in the suite). To stay usable it also cut
sheets off at row 600 (XLSX) or row 100 (CSV), hiding the rest of the data. The grid now renders the
visible window only, and the sheet extent follows the data.
"""
from __future__ import annotations
import io, os, socket, subprocess, sys, tempfile, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8850
BASE = f"http://127.0.0.1:{PORT}"
API = "globalThis.__inkdosSpreadsheetsS1"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def xlsx_bytes(rows: int) -> bytes:
    data = "".join(f'<row r="{r}"><c r="A{r}"><v>{r}</v></c><c r="B{r}" t="inlineStr"><is><t>row {r}</t></is></c></row>' for r in range(1, rows + 1))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS}"><sheetData>{data}</sheetData></worksheet>')
    return out.getvalue()


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")


def open_file(browser, path):
    page = browser.new_page(viewport={"width": 1180, "height": 820})
    page.goto(BASE + "/apps/spreadsheets/", wait_until="load")
    page.wait_for_function(f"() => !!{API}")
    page.set_input_files("#fileInput", str(path))
    page.wait_for_function(f"() => !!{API}?.session?.book?.loaded && document.getElementById('startState')?.hidden === true", timeout=60000)
    return page


def check_last_row(page, last_row: int, text: str):
    state = page.evaluate(f"() => ({{maxR: {API}.session.activeSheet().maxR, cells: document.querySelectorAll('.cell').length}})")
    assert state["maxR"] >= last_row - 1, f"grid stops before the data: {state}"
    assert state["cells"] < 2500, f"grid must render only the visible window: {state}"
    page.evaluate("() => { const v = document.querySelector('.grid-stage').parentElement; v.scrollTop = v.scrollHeight; v.dispatchEvent(new Event('scroll')); }")
    page.wait_for_function(f"() => document.querySelector('.cell[data-ref=\"B{last_row}\"]')?.textContent === {text!r}", timeout=5000)
    assert page.evaluate("() => document.querySelectorAll('.cell').length") < 2500


def main():
    browser_name = os.environ.get("BROWSER", "chromium")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td:
            csv = Path(td) / "window.csv"
            csv.write_text("id,label\n" + "".join(f"{r},row {r}\n" for r in range(2, 3001)), encoding="utf-8")
            xlsx = Path(td) / "window.xlsx"
            xlsx.write_bytes(xlsx_bytes(1500))
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                # Every row of a CSV beyond row 100 and of an XLSX beyond row 600 is reachable.
                page = open_file(browser, csv)
                check_last_row(page, 3000, "row 3000")
                page.close()
                page = open_file(browser, xlsx)
                check_last_row(page, 1500, "row 1500")
                # Selection, keyboard navigation and editing still work on rendered cells.
                page.evaluate("() => { const v = document.querySelector('.grid-stage').parentElement; v.scrollTop = 0; v.dispatchEvent(new Event('scroll')); }")
                page.wait_for_selector('.cell[data-ref="B3"]')
                page.click('.cell[data-ref="B3"]')
                assert page.evaluate("() => document.querySelector('.cell.selected')?.dataset.ref") == "B3"
                page.keyboard.press("ArrowDown")
                page.wait_for_function("() => document.querySelector('.cell.selected')?.dataset.ref === 'B4'")
                assert page.evaluate("() => [document.querySelector('.col-header.axis-active')?.textContent.trim(), document.querySelector('.row-header.axis-active')?.textContent.trim()]") == ["B", "4"]
                page.keyboard.type("edited")
                page.keyboard.press("Enter")
                page.wait_for_function("() => document.querySelector('.cell[data-ref=\"B4\"]')?.textContent === 'edited'")
                assert page.evaluate(f"() => {API}.session.activeSheet().cells.get('B4')?.v") == "edited"
                # Moving the active cell past the rendered window scrolls and renders it.
                for _ in range(80):
                    page.keyboard.press("ArrowDown")
                page.wait_for_function("() => document.querySelector('.cell.selected')?.dataset.ref === 'B85'", timeout=5000)
                # Selecting a whole column marks its rendered cells without touching the rest.
                page.click('.col-header[data-c="0"]')
                marked = page.evaluate("() => [...document.querySelectorAll('.cell.in-range')].every(el => el.dataset.c === '0') && document.querySelectorAll('.cell.in-range').length > 10")
                assert marked, "column selection must mark rendered cells of that column"
                page.close()
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Spreadsheets grid window ({browser_name}): OK")


if __name__ == "__main__":
    main()

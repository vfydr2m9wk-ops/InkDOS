#!/usr/bin/env python3
"""Regression: saving an opened XLSX must not rewrite untouched cells and must scale linearly.

Opening resolves theme/indexed colours into each cell's visual style. That resolution used to
make every cell differ from its original snapshot, so every save patched every cell, and each
patch looked its row up with a linear scan (quadratic: ~8.7 s for 2,000 rows, minutes for 10,000).
"""
from __future__ import annotations
import io, os, re, socket, subprocess, sys, tempfile, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8798
BASE = f"http://127.0.0.1:{PORT}"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ROWS = 3000


def fixture() -> bytes:
    rows = []
    for r in range(1, ROWS + 1):
        rows.append(
            f'<row r="{r}"><c r="A{r}"><v>{r}</v></c><c r="B{r}" s="1" t="inlineStr"><is><t>item {r}</t></is></c>'
            f'<c r="C{r}" s="1"><v>{r * 3}</v></c><c r="D{r}"><f>C{r}*2</f><v>{r * 6}</v></c></row>'
        )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        # Font 1 uses a theme colour, which opening resolves to a concrete visual colour.
        z.writestr("xl/styles.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{NS}"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color theme="1"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs></styleSheet>')
        z.writestr("xl/worksheets/sheet1.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS}"><sheetData>{"".join(rows)}</sheetData></worksheet>')
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


def main():
    browser_name = os.environ.get("BROWSER", "chromium")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "save-scaling.xlsx"
            path.write_bytes(fixture())
            with sync_playwright() as pw:
                args = {"headless": True}
                if os.environ.get("CHROMIUM_PATH") and browser_name == "chromium":
                    args["executable_path"] = os.environ["CHROMIUM_PATH"]
                browser = getattr(pw, browser_name).launch(**args)
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(BASE + "/apps/spreadsheets/", wait_until="load")
                page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1")
                page.set_input_files("#fileInput", str(path))
                page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded && document.getElementById('startState')?.hidden === true", timeout=60000)
                result = page.evaluate(
                    """async (rows) => {
                      const api = globalThis.__inkdosSpreadsheetsS1, book = api.session.book, sheet = book.sheets[0];
                      const key = c => JSON.stringify([c.f||'', c.t||'', Number(c.styleId||0), c.style||{}, String(c.v ?? '')]);
                      let differing = 0;
                      for (const [ref, cell] of sheet.cells) { const o = sheet.originalCells.get(ref); if (!o || key(o) !== key(cell)) differing++; }
                      const resolvedColor = sheet.cells.get('B2')?.style?.font?.color || '';
                      api.editor.editor.commitValue('edited', 1, 1);
                      let t0 = performance.now();
                      const one = await globalThis.LocalXLSX.saveCopy(book);
                      const oneMs = performance.now() - t0;
                      // Worst case for the row lookup: every row carries a changed cell.
                      for (let r = 2; r <= rows; r++) sheet.cells.get('C' + r).v = r * 3 + 1;
                      t0 = performance.now();
                      const all = await globalThis.LocalXLSX.saveCopy(book);
                      const allMs = performance.now() - t0;
                      const reparsed = await globalThis.LocalXLSX.parseWorkbook(await all.arrayBuffer(), 'save-scaling.xlsx');
                      const rs = reparsed.sheets[0];
                      const b64 = async blob => { const b = new Uint8Array(await blob.arrayBuffer()); let s = ''; for (let i = 0; i < b.length; i += 32768) s += String.fromCharCode(...b.subarray(i, i + 32768)); return btoa(s); };
                      return {differing, cells: sheet.cells.size, resolvedColor, oneMs, allMs, one: await b64(one),
                        b2: rs.cells.get('B2')?.v, b3: rs.cells.get('B3')?.v, c9: rs.cells.get('C9')?.v, lastA: rs.cells.get('A' + rows)?.v,
                        d5f: rs.cells.get('D5')?.f, b3style: rs.cells.get('B3')?.styleId};
                    }""",
                    ROWS,
                )
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

    assert result["resolvedColor"], "fixture must exercise colour resolution on open"
    assert result["cells"] == ROWS * 4, result["cells"]
    assert result["differing"] == 0, f"{result['differing']} untouched cells differ from their original snapshot after open"
    import base64
    sheet = zipfile.ZipFile(io.BytesIO(base64.b64decode(result["one"]))).read("xl/worksheets/sheet1.xml").decode()
    assert len(re.findall(r"<row\b", sheet)) == ROWS
    assert len(re.findall(r'\ss="1"', sheet)) == ROWS * 2, "untouched cells must keep their style ids"
    assert "edited" in sheet and "item 3</t>" in sheet
    assert result["b2"] == "edited" and result["b3"] == "item 3" and result["c9"] == 28 and result["lastA"] == ROWS, result
    assert result["d5f"] and result["b3style"] == 1, result
    # Generous bounds: the quadratic path took ~20 s (one edit) and far longer (all rows) at this size.
    assert result["oneMs"] < 5000, f"single-edit save took {result['oneMs']:.0f} ms"
    assert result["allMs"] < 10000, f"all-rows-changed save took {result['allMs']:.0f} ms"
    print(f"Spreadsheets XLSX save scaling ({browser_name}): OK — one edit {result['oneMs']:.0f} ms, {ROWS} changed rows {result['allMs']:.0f} ms")


if __name__ == "__main__":
    main()

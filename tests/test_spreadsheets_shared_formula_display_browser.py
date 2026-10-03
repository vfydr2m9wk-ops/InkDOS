#!/usr/bin/env python3
"""XLSX shared formulas and number formats as the grid shows them.

The workbook is built here (no fixture files): A2:A4 share one formula (only A2 carries its text),
A1 has a custom date format, B1 a built-in date format id, C1 an accounting format with a zero and
a negative section. Dependent cells must keep a formula and the grid must show formatted text
instead of serial numbers.
"""
from __future__ import annotations

import io
import os
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8796
ACC = '_(* #,##0.00_);_(* \\(#,##0.00\\);_(* &quot;-&quot;??_);_(@_)'


def xlsx() -> bytes:
    sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             '<row r="1"><c r="A1" s="1"><v>46110</v></c><c r="B1" s="2"><v>46110</v></c><c r="C1" s="3"><v>0</v></c><c r="D1" s="3"><v>-100</v></c></row>'
             '<row r="2"><c r="A2" s="1"><f t="shared" ref="A2:A4" si="0">A1+7</f><v>46117</v></c></row>'
             '<row r="3"><c r="A3" s="1"><f t="shared" si="0"/><v>46124</v></c></row>'
             '<row r="4"><c r="A4" s="1"><f t="shared" si="0"/><v>46131</v></c></row>'
             '</sheetData></worksheet>')
    styles = ('<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              f'<numFmts count="2"><numFmt numFmtId="165" formatCode="mm/dd/yy"/><numFmt numFmtId="166" formatCode="{ACC}"/></numFmts>'
              '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
              '<borders count="1"><border/></borders><cellXfs count="4"><xf numFmtId="0"/><xf numFmtId="165"/><xf numFmtId="14"/><xf numFmtId="166"/></cellXfs></styleSheet>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', sheet)
        z.writestr('xl/styles.xml', styles)
    return buf.getvalue()


PROBE = """() => { const s=globalThis.__inkdosSpreadsheetsS1.session.book.sheets[0], g=globalThis.InkDOS2Spreadsheets.GridDisplay;
  const cell=k=>s.cells.get(k); return {f:['A2','A3','A4'].map(k=>cell(k).f), shown:['A1','B1','C1','D1'].map(k=>g.display(cell(k)).trim())} }"""


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def main() -> None:
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
            book = Path(td) / 'shared.xlsx'
            book.write_bytes(xlsx())
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            page = browser.new_context(service_workers='block', viewport={'width': 1200, 'height': 800}).new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{PORT}/apps/spreadsheets/', wait_until='load')
            page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')
            page.set_input_files('#fileInput', str(book))
            page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded', timeout=30000)
            got = page.evaluate(PROBE)
            assert got['f'] == ['A1+7', 'A2+7', 'A3+7'], got
            assert got['shown'][0] == '03/29/26', got
            assert got['shown'][1] not in ('', '46110') and '2026' in got['shown'][1], got
            assert got['shown'][2] == '-' and got['shown'][3] == '(100.00)', got
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Spreadsheets XLSX shared formulas and formatted display passed')


if __name__ == '__main__':
    main()

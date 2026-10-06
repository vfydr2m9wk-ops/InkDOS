#!/usr/bin/env python3
"""Spreadsheets: large workbooks stay responsive.

A 20,000-row workbook (240,000 cells, a SUM formula per row) is built here. Opening it reports progress
("Opening workbook… N%"), which proves the page is handed back to the browser while cells are read instead
of freezing until the end. Editing keeps only the touched cells in undo history and recalculates only what
depends on them: a value edit updates the row's SUM, a formula edit evaluates, bold applies, and undo/redo
restore every step.
"""
from __future__ import annotations

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
PORT = 8823
ROWS, COLS = 20000, 12


def col(i: int) -> str:
    s = ''
    while True:
        s = chr(65 + i % 26) + s
        i = i // 26 - 1
        if i < 0:
            return s


def build_xlsx(path: Path) -> None:
    rows = []
    for r in range(1, ROWS + 1):
        cells = [f'<c r="A{r}" t="inlineStr"><is><t>row {r}</t></is></c>']
        cells += [f'<c r="{col(c)}{r}"><v>{(r * 7 + c) % 1000}</v></c>' for c in range(1, COLS - 1)]
        total = sum((r * 7 + c) % 1000 for c in range(1, COLS - 1))
        cells.append(f'<c r="{col(COLS - 1)}{r}"><f>SUM(B{r}:{col(COLS - 2)}{r})</f><v>{total}</v></c>')
        rows.append(f'<row r="{r}">{"".join(cells)}</row>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(rows) + '</sheetData></worksheet>')


def wait_port() -> None:
    deadline = time.time() + 10
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
            book = Path(td) / 'Large.xlsx'
            build_xlsx(book)
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            page = browser.new_context(service_workers='block', viewport={'width': 1280, 'height': 860}).new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{PORT}/apps/spreadsheets/index.html', wait_until='load')
            page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')
            page.evaluate("""() => { window.__progress = []; const label = document.getElementById('loadingLabel');
                new MutationObserver(() => { const t = label.textContent || ''; if (/\\d+%/.test(t)) window.__progress.push(t.trim()); })
                  .observe(label, {subtree: true, childList: true, characterData: true}); }""")
            page.set_input_files('#fileInput', str(book))
            page.wait_for_function("() => { const s = globalThis.__inkdosSpreadsheetsS1.session; return s.fileName === 'Large.xlsx' && !!s.book?.loaded }", timeout=180000)
            progress = page.evaluate('window.__progress')
            assert progress and all('Opening workbook' in p for p in progress), progress
            state = page.evaluate(f"""() => {{
                const a = globalThis.__inkdosSpreadsheetsS1, E = a.editor.editor, S = () => a.session.activeSheet();
                const val = k => {{ const c = S().cells.get(k); return c ? (c.calculated ?? c.v) : null; }};
                const sumRef = '{col(COLS - 1)}1', b1 = val('B1'), sum0 = val(sumRef);
                E.commitValue('5000', 0, 1); const sum1 = val(sumRef);
                E.commitValue('=B1*2', 0, {COLS + 2}); const formula = val('{col(COLS + 2)}1');
                E.selection.select(0, 1, S(), false); E.toggleFont('bold'); const bold = !!S().cells.get('B1').style.font.bold;
                E.undo(); const unbold = !S().cells.get('B1').style.font.bold;
                E.undo(); const formulaGone = !S().cells.has('{col(COLS + 2)}1');
                E.undo(); const sum2 = val(sumRef), b2 = val('B1');
                E.redo(); const sum3 = val(sumRef);
                return {{ b1, sum0, sum1, formula, bold, unbold, formulaGone, sum2, b2, sum3 }};
            }}""")
            assert state['sum1'] == state['sum0'] - state['b1'] + 5000, state
            assert state['formula'] == 10000 and state['bold'] and state['unbold'] and state['formulaGone'], state
            assert state['sum2'] == state['sum0'] and state['b2'] == state['b1'] and state['sum3'] == state['sum1'], state
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Spreadsheets large workbook: progress while opening; cell edits, formatting and undo/redo stay exact')


if __name__ == '__main__':
    main()

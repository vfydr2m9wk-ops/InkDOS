#!/usr/bin/env python3
"""Spreadsheets: a legacy Excel workbook (.xls) is shown view-only, without converting it to XLSX.

Typing, double-click editing, the formula bar (and the greyed-out editing toolbar), paste, formatting/structure commands, worksheet
add/delete, rename, Save, Share and XLSX/CSV export do nothing for a .xls; selection, copy and PDF
export keep working. The BIFF8 decoding itself is covered by the XLS contract tests; here the
reader's parse step returns a known workbook so the real open flow runs on it. An XLSX stays
editable.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8817
BASE = f'http://127.0.0.1:{PORT}'

OPEN_XLS = r"""async () => {
    const api = globalThis.__inkdosSpreadsheetsS1, X = globalThis.LocalXLSX;
    globalThis.LocalXLS = { ...globalThis.LocalXLS, parseWorkbook: async () => {
        const book = X.createBlank(), s = book.sheets[0];
        const cell = v => ({ v, f: '', styleId: 0, style: { font: {}, border: {} }, t: typeof v === 'number' ? 'n' : 's', display: String(v) });
        s.cells.set('A1', cell('Legacy')); s.cells.set('B1', cell(42)); s.maxR = Math.max(s.maxR || 0, 1); s.maxC = Math.max(s.maxC || 0, 1);
        book.loaded = true;
        return book;
    } };
    const bytes = new Uint8Array([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]);
    return await api.openController.handle(new File([bytes], 'Old budget.xls', { type: 'application/vnd.ms-excel' }));
}"""


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def a1(page) -> str:
    return page.evaluate("() => String(globalThis.__inkdosSpreadsheetsS1.session.activeSheet().cells.get('A1')?.v ?? '')")


def main() -> None:
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            context = browser.new_context(service_workers='block', accept_downloads=True, viewport={'width': 1360, 'height': 900})
            page = context.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            downloads: list[str] = []
            page.on('download', lambda d: (downloads.append(d.suggested_filename), d.cancel()))
            page.goto(BASE + '/apps/spreadsheets/index.html', wait_until='load')
            page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1")
            opened = page.evaluate(OPEN_XLS)
            assert page.evaluate("() => globalThis.__inkdosSpreadsheetsS1.session.sourceKind") == 'xls', opened
            page.wait_for_selector('.cell[data-r="0"][data-c="0"]')
            assert a1(page) == 'Legacy'

            # typing, double-click and the formula bar do not edit
            page.click('.cell[data-r="0"][data-c="0"]')
            page.keyboard.type('X')
            page.keyboard.press('Enter')
            page.dblclick('.cell[data-r="0"][data-c="0"]')
            assert page.evaluate("() => !document.querySelector('.cell[contenteditable=\"true\"]')"), 'a cell entered edit mode'
            assert page.evaluate("() => document.getElementById('formulaInput').readOnly")
            # the editing toolbar is greyed out; zoom and print stay available
            bar = page.evaluate("""() => ({ bold: document.getElementById('boldBtn').disabled, font: document.getElementById('fontFamily').disabled,
                zoom: document.getElementById('zoomIn').disabled, print: document.getElementById('printBtn').disabled })""")
            assert bar == {'bold': True, 'font': True, 'zoom': False, 'print': False}, bar
            assert a1(page) == 'Legacy'

            state = page.evaluate("""async () => {
                const api = globalThis.__inkdosSpreadsheetsS1, cmd = api.editor.commands, s = api.session;
                const results = {
                    bold: cmd.execute('format.bold'), clear: cmd.execute('edit.clear'),
                    insertRow: cmd.execute('structure.insertRow'), undo: cmd.execute('edit.undo'),
                    mutate: api.editor.editor.mutate('Probe', sh => { sh.cells.get('A1').v = 'changed'; }),
                    save: await api.saveController.save(), share: await api.saveController.share(),
                    xlsx: await api.saveController.exportAs('xlsx'), csv: await api.saveController.exportAs('csv'),
                    rename: s.rename('Renamed.xlsx'),
                    copy: !!cmd.execute('edit.copyPayload'),
                };
                return { results, dirty: s.dirty, sheets: s.book.sheets.length, name: s.fileName,
                         menuSave: document.getElementById('menuSave')?.disabled, menuShare: document.getElementById('menuShare')?.disabled };
            }""")
            r = state['results']
            for key in ('bold', 'clear', 'insertRow', 'mutate', 'save', 'share', 'xlsx', 'csv'):
                assert r[key] is False, (key, state)
            assert r['copy'], state
            assert r['rename'] == 'Old budget.xls' and state['name'] == 'Old budget.xls', state
            assert not state['dirty'] and state['sheets'] == 1, state
            assert state['menuSave'] and state['menuShare'], state
            assert a1(page) == 'Legacy'

            # Ctrl/Cmd+S and paste do nothing; the Save panel offers only a PDF export
            page.keyboard.press('Control+s')
            page.evaluate("""() => { const dt = new DataTransfer(); dt.setData('text/plain', 'pasted');
                window.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true })); }""")
            page.wait_for_timeout(500)
            assert a1(page) == 'Legacy'
            page.evaluate("() => globalThis.InkDOSSaveOptions()")
            panel = page.locator('#saveOptionsPanel')
            panel.wait_for(state='visible')
            assert 'view-only' in panel.inner_text(), panel.inner_text()
            labels = page.eval_on_selector_all('#saveOptionsPanel button strong', 'els => els.map(e => e.textContent)')
            assert labels == ['PDF…', 'Cancel'], labels
            assert not downloads, downloads

            # an XLSX opened afterwards is editable again
            page.keyboard.press('Escape')
            page.evaluate("async () => { await globalThis.__inkdosSpreadsheetsS1.openController.newWorkbook(); }")
            page.wait_for_function("() => globalThis.__inkdosSpreadsheetsS1.session.sourceKind !== 'xls'")
            assert page.evaluate("""() => { const api = globalThis.__inkdosSpreadsheetsS1;
                return api.editor.editor.commitValue('fresh', 0, 0) !== false && api.session.activeSheet().cells.get('A1')?.v === 'fresh'; }""")
            page.click('.cell[data-r="1"][data-c="1"]')
            assert not page.evaluate("() => document.getElementById('boldBtn').disabled || document.getElementById('fontFamily').disabled"), 'toolbar stayed disabled'
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Spreadsheets: legacy XLS is view-only (no edits, no XLSX conversion; copy and PDF export remain)')


if __name__ == '__main__':
    main()

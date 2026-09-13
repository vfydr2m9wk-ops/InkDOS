#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8798
BASE = f'http://127.0.0.1:{PORT}'


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')


def main() -> None:
    browser_name = os.environ.get('BROWSER', 'chromium')
    server = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={'width': 1360, 'height': 900})
            page.on('pageerror', lambda exc: errors.append(f'pageerror: {exc}'))
            page.goto(BASE + '/apps/spreadsheets/?suite=1', wait_until='load')
            page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')

            result = page.evaluate("""async()=>{
              const api=globalThis.__inkdosSpreadsheetsS1;
              const source='Username; Identifier;First name;Last name\\nuser01;1001;Alex;Morgan\\nuser02;0007;Taylor;Lee\\n';
              const file=new File([source],'sample.csv',{type:'text/csv',lastModified:1700000000000});
              const opened=await api.openController.handle(file);
              const sheet=api.session.book.sheets[0];
              const cells={};
              for(const [ref,cell] of sheet.cells)cells[ref]=cell.v;
              const before={
                status:opened.status,
                sourceKind:api.session.sourceKind,
                delimiter:api.session.book.delimitedMeta?.delimiter,
                lineEnding:api.session.book.delimitedMeta?.lineEnding,
                finalRecordSeparator:api.session.book.delimitedMeta?.finalRecordSeparator,
                cells
              };
              api.editor.editor.commitValue('0008',2,1);
              const edited=sheet.cells.get('B3');
              const blob=globalThis.InkDOS2Spreadsheets.DelimitedText.serialize(api.session.book);
              const text=await blob.text();
              return {
                before,
                edited:{v:edited?.v,t:edited?.t,display:edited?.display},
                text,
                mime:blob.type
              };
            }""")

            assert result['before']['status'] == 'committed', result
            assert result['before']['sourceKind'] == 'csv', result
            assert result['before']['delimiter'] == ';', result
            assert result['before']['lineEnding'] == '\n', result
            assert result['before']['finalRecordSeparator'] is True, result
            expected_cells = {
                'A1': 'Username', 'B1': ' Identifier', 'C1': 'First name', 'D1': 'Last name',
                'A2': 'user01', 'B2': '1001', 'C2': 'Alex', 'D2': 'Morgan',
                'A3': 'user02', 'B3': '0007', 'C3': 'Taylor', 'D3': 'Lee',
            }
            assert result['before']['cells'] == expected_cells, result
            assert result['edited'] == {'v': '0008', 't': 's', 'display': '0008'}, result
            assert result['text'] == (
                'Username; Identifier;First name;Last name\n'
                'user01;1001;Alex;Morgan\n'
                'user02;0008;Taylor;Lee\n'
            ), result
            assert result['mime'] == 'text/csv;charset=utf-8', result
            assert not errors, errors
            browser.close()

        print(f'Spreadsheets delimited-text browser ({browser_name}): OK')
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == '__main__':
    main()

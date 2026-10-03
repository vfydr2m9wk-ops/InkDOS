#!/usr/bin/env python3
"""A table taller than a page is not clipped away, and line breaks/tabs inside its cells are kept.

The DOCX is built here (no fixture files): one 90-row table whose first cell holds two lines
separated by w:br. The last row must be visible inside its page, and the first cell must render
its break instead of running the two lines together.
"""
from __future__ import annotations

import io
import os
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8798
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def docx() -> bytes:
    cell = lambda body: f'<w:tc><w:p>{body}</w:p></w:tc>'
    run = lambda t: f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r>'
    rows = [f'<w:tr>{cell(run("first line") + "<w:r><w:br/></w:r>" + run("second line"))}{cell(run("x"))}</w:tr>']
    rows += [f'<w:tr>{cell(run(f"row {i}"))}{cell(run("y"))}</w:tr>' for i in range(1, 90)]
    rows.append(f'<w:tr>{cell(run("LASTROWMARK"))}{cell(run("z"))}</w:tr>')
    body = f'<w:document xmlns:w="{W}"><w:body><w:tbl>{"".join(rows)}</w:tbl><w:p/></w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml', body)
    return buf.getvalue()


VISIBLE = """() => { const cell=[...document.querySelectorAll('.page-content td')].find(td=>td.textContent.includes('LASTROWMARK'));
  if(!cell) return 'missing'; const c=cell.closest('.page-content').getBoundingClientRect(), r=cell.getBoundingClientRect();
  return r.top>=c.top-1&&r.bottom<=c.bottom+1?'visible':'clipped' }"""


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
        with sync_playwright() as pw:
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            page = browser.new_context(service_workers='block', viewport={'width': 1200, 'height': 900}).new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{PORT}/apps/documents/', wait_until='load')
            page.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsDebug?.openBytes')
            page.evaluate('async b => { await globalThis.InkDOS2Documents.DocumentsDebug.openBytes("tall.docx", new Uint8Array(b)) }', list(docx()))
            page.wait_for_timeout(1500)
            state = page.evaluate(VISIBLE)
            assert state == 'visible', f'last table row is {state}'
            first = page.evaluate("() => [...document.querySelectorAll('.page-content td')].find(td=>td.textContent.includes('first line'))?.innerHTML||''")
            assert '<br>' in first, f'cell line break lost: {first}'
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Documents tall table / cell breaks passed')


if __name__ == '__main__':
    main()

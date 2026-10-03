#!/usr/bin/env python3
"""First-page headers/footers and table cells that used to be dropped.

The DOCX is built here (no fixture files): a section with a different first page (w:titlePg)
whose first page and later pages have different headers and footers, a table row whose second
cell is wrapped in a content control (w:sdt around w:tc), and a picture inside a cell.
"""
from __future__ import annotations

import base64
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
PORT = 8795
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')


def docx() -> bytes:
    t = lambda s: f'<w:r><w:t xml:space="preserve">{s}</w:t></w:r>'
    pic = ('<w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><wp:extent cx="952500" cy="952500"/>'
           '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
           '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:blipFill><a:blip r:embed="rIdP"/></pic:blipFill></pic:pic>'
           '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    body = (f'<w:tbl><w:tr><w:tc><w:p>{t("plain cell")}</w:p></w:tc>'
            f'<w:sdt><w:sdtPr/><w:sdtContent><w:tc><w:p>{t("Choose an item.")}</w:p></w:tc></w:sdtContent></w:sdt>'
            f'<w:tc><w:p>{pic}</w:p></w:tc></w:tr></w:tbl>'
            f'<w:p>{t("First page body")}</w:p><w:p><w:r><w:br w:type="page"/></w:r>{t("Second page body")}</w:p>'
            '<w:sectPr><w:headerReference w:type="default" r:id="rIdHD"/><w:headerReference w:type="first" r:id="rIdHF"/>'
            '<w:footerReference w:type="first" r:id="rIdFF"/><w:titlePg/></w:sectPr>')
    part = lambda kind, text: f'<w:{kind} xmlns:w="{W}"><w:p>{t(text)}</w:p></w:{kind}>'
    rel = lambda i, typ, target: f'<Relationship Id="{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/{typ}" Target="{target}"/>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                   '<Default Extension="png" ContentType="image/png"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + rel('rId1', 'officeDocument', 'word/document.xml') + '</Relationships>')
        z.writestr('word/_rels/document.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + rel('rIdHD', 'header', 'header1.xml') + rel('rIdHF', 'header', 'header2.xml') + rel('rIdFF', 'footer', 'footer1.xml')
                   + rel('rIdP', 'image', 'media/image1.png') + '</Relationships>')
        z.writestr('word/document.xml', f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}</w:body></w:document>')
        z.writestr('word/header1.xml', part('hdr', 'LATER PAGES HEADER'))
        z.writestr('word/header2.xml', part('hdr', 'FIRST PAGE HEADER'))
        z.writestr('word/footer1.xml', part('ftr', 'FIRST PAGE FOOTER'))
        z.writestr('word/media/image1.png', PNG)
    return buf.getvalue()


PROBE = """() => { const pages=[...document.querySelectorAll('.doc-page')];
  return {headers:pages.map(p=>p.querySelector('.page-header')?.textContent||''), footers:pages.map(p=>p.querySelector('.page-footer')?.textContent||''),
    cells:[...document.querySelectorAll('.page-content td')].map(td=>td.textContent), cellImages:document.querySelectorAll('.page-content td img').length} }"""


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
            page.evaluate('async b => { await globalThis.InkDOS2Documents.DocumentsDebug.openBytes("variants.docx", new Uint8Array(b)) }', list(docx()))
            page.wait_for_timeout(1200)
            got = page.evaluate(PROBE)
            assert got['headers'][:2] == ['FIRST PAGE HEADER', 'LATER PAGES HEADER'], got
            assert got['footers'][0].startswith('FIRST PAGE FOOTER') and 'FIRST PAGE FOOTER' not in got['footers'][1], got
            assert got['cells'][:2] == ['plain cell', 'Choose an item.'], got
            assert got['cellImages'] == 1, got
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Documents first-page header/footer and table cells passed')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Saving an opened .docx without edits keeps its text exactly.

The DOCX is built here (no fixture files) with what used to break the save: a hyperlink (its
r:id needs the relationships namespace), a tab (rendered as an em space), a text box (its text
is not in the editor) and a table whose cell holds two paragraphs and a line break.
"""
from __future__ import annotations

import base64
import html
import io
import os
import re
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8799
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def docx() -> bytes:
    t = lambda s: f'<w:r><w:t xml:space="preserve">{s}</w:t></w:r>'
    box = ('<w:r><w:pict><v:shape xmlns:v="urn:schemas-microsoft-com:vml" style="width:100pt;height:40pt"><v:textbox>'
           f'<w:txbxContent><w:p>{t("Boxed words")}</w:p></w:txbxContent></v:textbox></v:shape></w:pict></w:r>')
    body = (f'<w:p>{t("Write to ")}<w:hyperlink r:id="rIdL">{t("info@example.org")}</w:hyperlink>{t(" today.")}</w:p>'
            f'<w:p>{t("Place")}<w:r><w:tab/></w:r>{t("Signature")}</w:p>'
            f'<w:p>{t("Anchor")}{box}</w:p>'
            f'<w:tbl><w:tr><w:tc><w:p>{t("one")}<w:r><w:br/></w:r>{t("two")}</w:p><w:p>{t("three")}</w:p></w:tc>'
            f'<w:tc><w:p>{t("four")}</w:p></w:tc></w:tr></w:tbl><w:p>{t("End.")}</w:p>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/_rels/document.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rIdL" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="mailto:info@example.org" TargetMode="External"/></Relationships>')
        z.writestr('word/document.xml', f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}<w:sectPr/></w:body></w:document>')
    return buf.getvalue()


def text_runs(data: bytes) -> str:
    xml = zipfile.ZipFile(io.BytesIO(data)).read('word/document.xml').decode()
    return html.unescape(''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', xml)))


SAVE = r"""async () => { const NS=globalThis.InkDOS2Documents, s=NS.DocumentsDebug.session;
  const r=await NS.DocxWriter.save(document.getElementById('pagesHost'), 'saved.docx', s.sourceBuffer, s.sourceContext);
  const u=new Uint8Array(await r.blob.arrayBuffer()); let t=''; for(let i=0;i<u.length;i+=32768) t+=String.fromCharCode(...u.subarray(i,i+32768)); return btoa(t) }"""


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
    source = docx()
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
            page.evaluate('async b => { await globalThis.InkDOS2Documents.DocumentsDebug.openBytes("links.docx", new Uint8Array(b)) }', list(source))
            page.wait_for_timeout(1200)
            saved = base64.b64decode(page.evaluate(SAVE))
            assert text_runs(saved) == text_runs(source), (text_runs(source), text_runs(saved))
            assert b'info@example.org' in zipfile.ZipFile(io.BytesIO(saved)).read('word/_rels/document.xml.rels'), 'hyperlink target lost'
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Documents unchanged save keeps text passed')


if __name__ == '__main__':
    main()

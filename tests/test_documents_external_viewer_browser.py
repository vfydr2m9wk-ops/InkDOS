#!/usr/bin/env python3
"""Documents: .odt and .pages files open view-only inside the workspace through the InkDOS-tools viewer.

The viewer is published by the InkDOS-tools repository on its own origin (inkdos-tools.github.io);
here a stub that speaks the same protocol stands in for it on another origin (localhost instead of
127.0.0.1), so the exchange really crosses origins. This test checks the Documents side:
the right viewer is embedded, the file is handed over, the session is view-only (no save, share or
rename), and opening a DOCX or a new document afterwards closes the viewer.
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
PORT = 8818
BASE = f'http://127.0.0.1:{PORT}'

STUB = """<!doctype html><meta charset="utf-8"><title>stub viewer</title><body>waiting
<script>
const inkdos = new URL(document.referrer).origin;
addEventListener('message', async e => {
  if (e.origin !== inkdos || !e.data || e.data.type !== 'inkdos-viewer-open') return;
  const file = e.data.file, text = await file.text();
  document.body.textContent = 'VIEWER __NAME__ ' + file.name + ' ' + file.size + ' ' + location.search;
  parent.postMessage({type: 'inkdos-viewer-loaded', ok: !/broken/.test(file.name), error: 'stub cannot read'}, inkdos);
});
parent.postMessage({type: 'inkdos-viewer-ready'}, inkdos);
</script>"""
# the viewers' origin in this test; the pages enforce the published one in their CSP frame-src, so these
# contexts bypass CSP (the CSP itself is checked by tests/test_home_advanced_tools_browser.py and the
# frame-src assertion below)
def tools_base(port: int) -> str:
    return f'http://localhost:{port}/InkDOS-tools/'


def use_stub_tools(context, port: int) -> None:
    context.add_init_script(f'window.InkDOSToolsBase = {tools_base(port)!r};')


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def minimal_docx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Editable docx</w:t></w:r></w:p></w:body></w:document>')
    return buf.getvalue()


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        site = Path(td)
        (site / 'InkDOS').symlink_to(ROOT)
        for viewer in ('odf', 'pnk'):
            (site / 'InkDOS-tools' / viewer).mkdir(parents=True)
            (site / 'InkDOS-tools' / viewer / 'index.html').write_text(STUB.replace('__NAME__', viewer), encoding='utf-8')
        files = site / 'files'
        files.mkdir()
        (files / 'Report.odt').write_bytes(b'PK odt stand-in')
        (files / 'Notes.pages').write_bytes(b'PK pages stand-in')
        (files / 'broken.odt').write_bytes(b'not a document')
        (files / 'Editable.docx').write_bytes(minimal_docx())
        server = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=site,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        errors: list[str] = []
        try:
            wait_port()
            with sync_playwright() as pw:
                browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
                context = browser.new_context(service_workers='block', viewport={'width': 1280, 'height': 860}, bypass_csp=True)
                use_stub_tools(context, PORT)
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(BASE + '/InkDOS/apps/documents/index.html', wait_until='load')
                page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!globalThis.InkDOS2Documents?.ExternalViewer")
                assert '.odt' in page.get_attribute('#fileInput', 'accept') and '.pages' in page.get_attribute('#fileInput', 'accept')
                csp = page.get_attribute('meta[http-equiv="Content-Security-Policy"]', 'content')
                assert "frame-src 'self' https://inkdos-offic.pages.dev;" in csp, csp

                def open_file(name: str) -> None:
                    page.set_input_files('#fileInput', str(files / name))

                def viewer_text() -> str:
                    frame = page.frame_locator('.external-viewer iframe')
                    return frame.locator('body').inner_text(timeout=10000)

                for name, viewer in (('Report.odt', 'odf'), ('Notes.pages', 'pnk')):
                    open_file(name)
                    page.wait_for_function("(n) => (document.getElementById('statusText')?.textContent || '').includes(n + ' · View only')", arg=name, timeout=15000)
                    assert f'VIEWER {viewer} {name}' in viewer_text(), viewer_text()
                    src = page.get_attribute('.external-viewer iframe', 'src')
                    assert src == tools_base(PORT) + f'{viewer}/?embed=1&inkdos-theme=light', src
                    state = page.evaluate("""async () => {
                        const app = InkDOS2Documents.DocumentsApp;
                        const saved = await app.save();
                        return { kind: app.session.kind, title: document.getElementById('titleText').value,
                                 readOnlyTitle: document.getElementById('titleText').readOnly,
                                 save: document.getElementById('saveMenuBtn').disabled, saved: saved ?? null,
                                 panel: !!document.getElementById('saveReadyPanel'), dirty: app.session.dirty,
                                 welcome: document.getElementById('welcome').style.display };
                    }""")
                    assert state == {'kind': 'view', 'title': name, 'readOnlyTitle': True, 'save': True, 'saved': None,
                                     'panel': False, 'dirty': False, 'welcome': 'none'}, state
                    assert page.locator('.external-viewer').count() == 1

                # a file the viewer cannot read reports an error instead of a blank screen
                open_file('broken.odt')
                page.wait_for_function("() => (document.getElementById('statusText')?.textContent || '').includes('could not be shown')", timeout=15000)

                # a DOCX afterwards is editable again and the viewer is gone
                open_file('Editable.docx')
                page.wait_for_function("() => InkDOS2Documents.DocumentsApp.session.kind === 'docx'", timeout=15000)
                assert page.locator('.external-viewer').count() == 0
                assert page.evaluate("() => !document.getElementById('saveMenuBtn').disabled && [...document.querySelectorAll('.page-content')].some(p => p.isContentEditable)")
                assert page.evaluate("() => document.getElementById('pagesHost').style.display") == ''
                assert not errors, errors
                browser.close()
        finally:
            server.terminate()
    print('Documents: .odt and .pages open view-only in the embedded InkDOS-tools viewer')


if __name__ == '__main__':
    main()

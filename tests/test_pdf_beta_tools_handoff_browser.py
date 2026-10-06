#!/usr/bin/env python3
"""PDF tools (beta) are reachable from inside the PDF workspace and work on the open file.

The toolbar's 'Beta tools' button and Settings (sun) → 'PDF tools (beta)' open the tools page
in a panel on the same page (no new tab); the PDF open in the workspace is handed over
automatically; a tool result ('Open in InkDOS') comes back to the workspace and closes the panel.
Hidden in the desktop app. The PDF is built here (no fixture files).
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8792
# a page of the same origin that is not the PDF tools page (e.g. a sibling GitHub Pages project)
FOREIGN_PAGE = """<!doctype html><script>
let leaked = false;
addEventListener('message', e => { if (e.data && e.data.type === 'inkdos-lab-file') leaked = true; });
const forged = {name: 'forged.pdf', bytes: new Uint8Array([37, 80, 68, 70, 45])};
parent.postMessage({type: 'inkdos-lab-ready'}, location.origin);
parent.postMessage({type: 'inkdos-lab-result', ...forged}, location.origin);
parent.document.querySelector('iframe.beta-tools-frame').contentWindow.postMessage({type: 'inkdos-lab-file', ...forged}, location.origin);
setTimeout(() => parent.postMessage({type: 'foreign-done', leaked}, location.origin), 1000);
</script>"""


def text_pdf(path: Path) -> None:
    content = b'BT /F1 24 Tf 72 700 Td (Handoff test page with words) Tj ET'
    objs = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
            b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    out, offsets = bytearray(b'%PDF-1.7\n'), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f'{i} 0 obj\n'.encode() + body + b'\nendobj\n'
    xref = len(out)
    out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode() + b''.join(f'{o:010d} 00000 n \n'.encode() for o in offsets)
    out += f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    path.write_bytes(bytes(out))


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
            pdf = Path(td) / 'handoff.pdf'
            text_pdf(pdf)
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            context = browser.new_context(service_workers='block', viewport={'width': 1280, 'height': 900})
            app = context.new_page()
            app.on('pageerror', lambda e: errors.append(f'app: {e}'))
            app.goto(f'http://127.0.0.1:{PORT}/apps/pdf/index.html', wait_until='load')
            app.wait_for_function('() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug')
            app.set_input_files('#fileInput', str(pdf))
            app.wait_for_function("() => (document.getElementById('titleText')?.textContent||'').includes('handoff')", timeout=30000)
            # the toolbar entry is visible and opens the tools in a panel on the same page
            button = app.locator('#betaToolsBtn')
            assert button.is_visible() and 'Beta tools' in button.inner_text()
            button.click()
            app.wait_for_selector('#betaToolsPanel:not([hidden]) iframe.beta-tools-frame')
            lab = next(f for f in app.frames if '/labs/pdf/' in f.url)
            lab.wait_for_function("() => (document.getElementById('fileName')?.textContent||'').includes('handoff')", timeout=30000)
            assert lab.evaluate("() => document.querySelector('.lab-head .back').hidden"), 'the tools page must not navigate the panel away'
            # the web edition's OCR is the official one in the workspace: the tools page hides its copy
            assert lab.locator('[role=tab][data-tab="ocr"]').is_hidden()
            assert lab.get_attribute('[role=tab][data-tab="stamp"]', 'aria-selected') == 'true'
            # visual signature: draw it (bounding boxes are in page coordinates), place it, apply
            box = lab.locator('#pad').bounding_box()
            x0, y0 = box['x'], box['y']
            app.mouse.move(x0 + 40, y0 + 100)
            app.mouse.down()
            for step in range(1, 12):
                app.mouse.move(x0 + 40 + step * 25, y0 + 100 - (step % 3) * 20)
            app.mouse.up()
            lab.wait_for_function("() => document.getElementById('preview').width > 0", timeout=30000)
            lab.click('#preview')
            assert lab.evaluate("() => { const c = document.getElementById('pad'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; for (let i = 3; i < d.length; i += 4) if (d[i]) return true; return false; }"), 'nothing was drawn on the pad'
            lab.click('#stampBtn')
            lab.wait_for_selector('#returnBtn:not([hidden])', timeout=60000)
            lab.click('#returnBtn')
            app.wait_for_function("() => (document.getElementById('titleText')?.textContent||'').includes('-assinado')", timeout=30000)
            app.wait_for_selector('#betaToolsPanel', state='hidden')
            assert app.locator('#betaToolsPanel iframe').count() == 0, 'closing the panel must drop the tools frame'
            assert len(context.pages) == 1, 'no other tab or window may be opened'
            # Settings (sun) → 'PDF tools (beta)' opens the same panel, and Escape closes it
            app.wait_for_selector('[data-frame-action="sun"]', timeout=15000)
            app.click('[data-frame-action="sun"]')
            app.click('.inkdos-settings-option[data-settings-value="beta-pdf"]')
            app.wait_for_selector('#betaToolsPanel:not([hidden]) iframe.beta-tools-frame')
            lab = next(f for f in app.frames if '/labs/pdf/' in f.url)
            lab.wait_for_function("() => (document.getElementById('fileName')?.textContent||'').includes('-assinado')", timeout=30000)
            # any other page of the same origin (e.g. a sibling GitHub Pages project) is ignored by both
            # sides: it gets no copy of the open PDF, cannot replace it, and cannot push one to the tools
            context.route(f'http://127.0.0.1:{PORT}/foreign.html', lambda route: route.fulfill(content_type='text/html', body=FOREIGN_PAGE))
            leaked = app.evaluate("""() => new Promise(resolve => {
                const f = document.createElement('iframe'); f.id = 'foreignPage'; f.src = '/foreign.html';
                addEventListener('message', e => { if (e.data && e.data.type === 'foreign-done') resolve(e.data.leaked); });
                document.body.appendChild(f); })""")
            assert leaked is False, 'a non-tools page must not receive the open PDF'
            app.wait_for_timeout(800)
            assert 'forged' not in (app.text_content('#titleText') or ''), 'a non-tools page must not replace the open PDF'
            assert 'forged' not in (lab.text_content('#fileName') or ''), 'only the opener may hand the tools a document'
            app.evaluate("() => document.getElementById('foreignPage').remove()")
            app.keyboard.press('Escape')
            app.wait_for_selector('#betaToolsPanel', state='hidden')
            assert len(context.pages) == 1
            # the desktop app keeps these tools in its beta channel: no toolbar entry there
            desktop = browser.new_context(service_workers='block')
            desktop.add_init_script('window.InkDOSDesktop = {host: "tauri"}')
            dpage = desktop.new_page()
            dpage.goto(f'http://127.0.0.1:{PORT}/apps/pdf/index.html', wait_until='load')
            dpage.wait_for_function('() => !!globalThis.InkDOS2PdfP4?.PdfBetaToolsPanel')
            assert dpage.locator('#betaToolsBtn').is_hidden()
            assert dpage.evaluate('() => globalThis.InkDOS2PdfP4.PdfBetaToolsPanel.open()') is False
            desktop.close()
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('PDF tools (beta): panel on the same page, file handed over and result returned')


if __name__ == '__main__':
    main()

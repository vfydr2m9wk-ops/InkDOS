#!/usr/bin/env python3
"""PDF tools (beta) are reachable from inside the PDF workspace and work on the open file.

Settings (sun) → 'PDF tools (beta)' opens the tools page in a new tab; the PDF open in the
workspace is handed over automatically; a tool result ('Open in InkDOS') comes back to the
workspace. The PDF is built here (no fixture files).
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
            app.wait_for_selector('[data-frame-action="sun"]', timeout=15000)
            app.click('[data-frame-action="sun"]')
            with context.expect_page() as popup:
                app.click('.inkdos-settings-option[data-settings-value="beta-pdf"]')
            lab = popup.value
            lab.on('pageerror', lambda e: errors.append(f'lab: {e}'))
            lab.wait_for_function("() => (document.getElementById('fileName')?.textContent||'').includes('handoff')", timeout=30000)
            lab.check('#ocrAll')
            lab.click('#ocrBtn')
            lab.wait_for_selector('#returnBtn:not([hidden])', timeout=120000)
            lab.click('#returnBtn')
            app.wait_for_function("() => (document.getElementById('titleText')?.textContent||'').includes('-ocr')", timeout=30000)
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('PDF tools (beta): reachable from the PDF workspace, file handed over and result returned')


if __name__ == '__main__':
    main()

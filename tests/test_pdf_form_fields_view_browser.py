#!/usr/bin/env python3
"""A filled form field is visible while reading, and is not painted twice while editing.

The viewer draws page canvases without the HTML forms layer in view mode, so widget appearances
must be painted on the canvas there (AnnotationMode.ENABLE); once editing mounts the forms layer the
canvas is repainted without them (ENABLE_FORMS) and the field shows as an input. The PDF is built
here (no fixture files).
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
PORT = 8797
BASE = f"http://127.0.0.1:{PORT}"
VALUE = 'Filled value'


def form_pdf(path: Path) -> None:
    ap = f'/Tx BMC q BT /Helv 18 Tf 0 g 4 8 Td ({VALUE}) Tj ET Q EMC'.encode()
    objs = [
        b'<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [4 0 R] /DA (/Helv 18 Tf 0 g) /DR << /Font << /Helv 6 0 R >> >> >> >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300] /Annots [4 0 R] /Resources << >> >>',
        b'<< /Type /Annot /Subtype /Widget /FT /Tx /T (name) /V (' + VALUE.encode() + b') /Rect [50 200 350 230] /P 3 0 R /F 4 '
        b'/DA (/Helv 18 Tf 0 g) /AP << /N 5 0 R >> >>',
        b'<< /Type /XObject /Subtype /Form /BBox [0 0 300 30] /Resources << /Font << /Helv 6 0 R >> >> /Length ' + str(len(ap)).encode() + b' >>\nstream\n' + ap + b'\nendstream',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
    ]
    out, offsets = bytearray(b'%PDF-1.7\n'), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f'{i} 0 obj\n'.encode() + body + b'\nendobj\n'
    xref = len(out)
    out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode() + b''.join(f'{o:010d} 00000 n \n'.encode() for o in offsets)
    out += f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    path.write_bytes(bytes(out))


# Dark pixels inside the field's rectangle on page 1's canvas.
INK = """() => { const c=document.querySelector('.pdf-page-shell[data-page="1"] canvas'); if(!c) return -1;
  const x=c.getContext('2d').getImageData(0,0,c.width,c.height).data; let n=0;
  for(let i=0;i<x.length;i+=4) if(x[i]<128&&x[i+1]<128&&x[i+2]<128) n++; return n }"""


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
            pdf = Path(td) / 'form.pdf'
            form_pdf(pdf)
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            page = browser.new_context(service_workers='block', viewport={'width': 1200, 'height': 900}).new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(BASE + '/apps/pdf/', wait_until='load')
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            page.set_input_files('#fileInput', str(pdf))
            page.wait_for_function("() => { const c=document.querySelector('.pdf-page-shell[data-page=\"1\"] canvas'); return !!c && c.width>0 }", timeout=30000)
            page.wait_for_timeout(800)
            viewed = page.evaluate(INK)
            assert viewed > 50, f'filled field value is not painted while reading: {viewed} dark pixels'
            page.click('#editModeBtn')
            page.wait_for_function("() => [...document.querySelectorAll('.annotationLayer input')].some(i => i.value === %r)" % VALUE, timeout=30000)
            page.wait_for_timeout(800)
            edited = page.evaluate(INK)
            assert edited < viewed / 4, f'field painted on the canvas under its editable input: {edited} dark pixels'
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('PDF form field view/edit painting passed')


if __name__ == '__main__':
    main()

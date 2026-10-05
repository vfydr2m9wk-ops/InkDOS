#!/usr/bin/env python3
"""PDF tools (beta) in the desktop app's beta window: the open PDF comes in, the result goes back.

The desktop host (desktop/src-tauri/src/beta.rs) serves the tools page on its own scheme
(http://inkdos-beta.localhost/ on Windows) and hands over the PDF of the window that opened the
tool at /__inkdos/file; the page posts its result to /__inkdos/result. That host is emulated here
by routing the scheme's origin to the repository files plus those two endpoints.
"""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'http://inkdos-beta.localhost'


def text_pdf() -> bytes:
    content = b'BT /F1 24 Tf 72 700 Td (Desktop handoff page with words) Tj ET'
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
    return bytes(out)


def main() -> None:
    handed = {'file': text_pdf()}
    results: list[tuple[str, bytes]] = []
    errors: list[str] = []

    def host(route) -> None:
        request = route.request
        path = urlparse(request.url).path
        if path == '/__inkdos/file':
            data = handed.pop('file', None)
            if data is None:
                route.fulfill(status=204, body=b'')
            else:
                route.fulfill(status=200, body=data, headers={'Content-Type': 'application/pdf',
                                                              'x-inkdos-file-name': 'Contrato%20mar%C3%A7o.pdf'})
            return
        if path == '/__inkdos/result':
            assert request.method == 'POST', request.method
            results.append((request.headers.get('x-inkdos-file-name', ''), request.post_data_buffer or b''))
            route.fulfill(status=204, body=b'')
            return
        file = (ROOT / path.lstrip('/')).resolve()
        if not file.is_relative_to(ROOT) or not file.is_file():
            route.fulfill(status=404, body=b'Not found')
            return
        kind = 'text/javascript' if file.suffix in ('.js', '.mjs') else (mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
        route.fulfill(status=200, body=file.read_bytes(), headers={'Content-Type': kind})

    with sync_playwright() as pw:
        browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
        context = browser.new_context(service_workers='block', viewport={'width': 1180, 'height': 820})
        context.route(f'{ORIGIN}/**', host)
        lab = context.new_page()
        lab.on('pageerror', lambda e: errors.append(str(e)))
        lab.goto(f'{ORIGIN}/labs/pdf/index.html', wait_until='load')
        lab.wait_for_function("() => (document.getElementById('fileName')?.textContent||'') === 'Contrato março.pdf'", timeout=30000)
        assert lab.locator('#returnBtn').is_hidden(), 'nothing to send back before a tool ran'
        lab.check('#ocrAll')
        lab.click('#ocrBtn')
        lab.wait_for_selector('#returnBtn:not([hidden])', timeout=120000)
        lab.click('#returnBtn')
        lab.wait_for_function("() => /InkDOS/.test(document.getElementById('status')?.textContent||'')", timeout=15000)
        assert len(results) == 1, results
        name, body = results[0]
        assert name == 'Contrato%20mar%C3%A7o-ocr.pdf', name
        assert body.startswith(b'%PDF-') and len(body) > len(text_pdf()), len(body)
        # a reload does not receive the document again (the host hands it over once)
        lab.reload(wait_until='load')
        lab.wait_for_timeout(1500)
        assert 'Contrato' not in (lab.text_content('#fileName') or '')
        assert not errors, errors
        browser.close()
    print('PDF tools (beta), desktop window: PDF handed over by the host and result sent back')


if __name__ == '__main__':
    main()

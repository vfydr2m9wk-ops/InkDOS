#!/usr/bin/env python3
"""Documents: a legacy Word document (.doc) is shown view-only, without offering a DOCX conversion.

The document opens read-only, Save and Share are disabled, and Save, Share and Ctrl/Cmd+S neither
build nor offer a DOCX copy. The binary .doc decoding itself is covered by the legacy DOC contract
tests; here the reader's parse step is replaced by its own text-to-blocks helper so the open flow
runs on a known document.
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
PORT = 8816
BASE = f'http://127.0.0.1:{PORT}'


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
            context = browser.new_context(service_workers='block', accept_downloads=True, viewport={'width': 1360, 'height': 900})
            page = context.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            downloads: list[str] = []
            page.on('download', lambda d: (downloads.append(d.suggested_filename), d.cancel()))
            page.goto(BASE + '/apps/documents/index.html', wait_until='load')
            page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!globalThis.InkDOS2Documents?.LegacyDocReader")
            opened = page.evaluate("""async () => {
                const NS = globalThis.InkDOS2Documents, reader = NS.LegacyDocReader;
                NS.LegacyDocReader = Object.freeze({ ...reader, parse: () => ({ blocks: reader._test.textToBlocks('Legacy view-only sample\\rSecond paragraph of the legacy Word document.\\r') }) });
                const file = new File([new Uint8Array([0xd0, 0xcf, 0x11, 0xe0])], 'Old report.doc', { type: 'application/msword' });
                return await NS.DocumentsApp.open(file, { authorized: true });
            }""")
            assert opened, 'the .doc did not open'
            page.wait_for_function("() => /Legacy view-only sample/.test(document.getElementById('pagesHost')?.textContent || document.body.textContent)")
            state = page.evaluate("""async () => {
                const NS = globalThis.InkDOS2Documents, save = document.getElementById('saveMenuBtn'), share = document.getElementById('shareMenuBtn');
                const saved = await NS.DocumentsApp.save();
                return {
                    kind: NS.DocumentsApp.session.kind,
                    editable: [...document.querySelectorAll('.page-content')].some(pc => pc.isContentEditable),
                    saveDisabled: save.disabled, shareDisabled: share ? share.disabled : true,
                    label: save.textContent, saved: saved ?? null,
                    panel: !!document.getElementById('saveReadyPanel'),
                    status: document.getElementById('statusText')?.textContent || '',
                };
            }""")
            assert state['kind'] == 'doc' and not state['editable'], state
            assert state['saveDisabled'] and state['shareDisabled'], state
            assert 'DOCX' not in state['label'], state
            assert state['saved'] is None and not state['panel'], state
            assert 'view only' in state['status'].lower(), state
            page.keyboard.press('Control+s')
            page.wait_for_timeout(600)
            assert not page.evaluate("() => !!document.getElementById('saveReadyPanel')"), 'Ctrl+S offered a DOCX copy'
            assert not downloads, downloads
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Documents: legacy DOC is view-only (no DOCX conversion offered, save/share disabled)')


if __name__ == '__main__':
    main()

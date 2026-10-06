#!/usr/bin/env python3
"""Presentations: a legacy PowerPoint (.ppt) is shown view-only, without offering a conversion.

The notice says the file is read-only, no "Save editable PPTX copy" button is offered, and save,
share and Ctrl/Cmd+S do nothing (no PPTX download). A PPTX keeps saving normally.
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
PORT = 8815
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
            page.goto(BASE + '/apps/presentations/index.html', wait_until='load')
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p2Tools")
            page.locator('#startNew').click()
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.active")
            # a PPTX can be saved
            assert page.evaluate("() => globalThis.__inkdosPresentations.hasCommand('file.save')")
            assert page.evaluate("() => !document.getElementById('saveMenuBtn').disabled")
            page.locator('#addSlideBtn').click()  # a second slide, so the navigation below re-syncs the chrome
            # the same session as a legacy .ppt (what the PPT reader produces): view-only
            page.evaluate("() => { const a = globalThis.__inkdosPresentations; a.session.sourceKind = 'ppt'; a.executeCommand('navigation.to', 0); }")
            notice = page.locator('#legacyPptNotice')
            notice.wait_for(state='visible')
            assert 'read-only' in notice.inner_text() and 'without converting' in notice.inner_text(), notice.inner_text()
            assert page.get_by_role('button', name='Save editable PPTX copy', exact=True).is_hidden()
            state = page.evaluate("""() => ({
                save: document.getElementById('saveMenuBtn')?.disabled,
                share: document.getElementById('shareMenuBtn')?.disabled ?? true,
                saveCmd: globalThis.__inkdosPresentations.executeCommand('file.save'),
                shareCmd: globalThis.__inkdosPresentations.executeCommand('file.share'),
            })""")
            assert state == {'save': True, 'share': True, 'saveCmd': False, 'shareCmd': False}, state
            page.keyboard.press('Control+s')
            page.wait_for_timeout(600)
            assert not downloads, downloads
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Presentations: legacy PPT is view-only (no conversion offered, save/share disabled)')


if __name__ == '__main__':
    main()

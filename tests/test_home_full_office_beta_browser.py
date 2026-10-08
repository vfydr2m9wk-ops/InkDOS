#!/usr/bin/env python3
"""Home: the gray "Full office (beta)" button at the bottom opens the full office suite (ranuts/document)
published on the InkDOS-tools origin (https://inkdos-tools.github.io/) in a new tab, without opener access.
It shows on phones and tablets (web), is hidden in the desktop app like the other web-only tools, and is
translated."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8820
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
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            for width, height in ((1280, 860), (390, 844)):
                context = browser.new_context(service_workers='block', viewport={'width': width, 'height': height})
                page = context.new_page()
                errors: list[str] = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(BASE + '/index.html', wait_until='load')
                link = page.locator('.beta-office a.beta-tool')
                assert link.count() == 1 and link.is_visible(), width
                assert link.get_attribute('href').split('?')[0] == 'https://inkdos-tools.github.io/'
                assert link.get_attribute('target') == '_blank'
                assert set(link.get_attribute('rel').split()) >= {'noopener', 'noreferrer'}
                assert link.inner_text().strip() == 'Full office (beta)'
                # below the quick tools, above the footer
                order = page.evaluate("""() => { const q = document.querySelector('.quick-tools').getBoundingClientRect(),
                    b = document.querySelector('.beta-office').getBoundingClientRect(),
                    f = document.querySelector('.home-footer').getBoundingClientRect();
                    return q.bottom <= b.top && b.bottom <= f.top + 1; }""")
                assert order, width
                assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth"), width
                # the desktop app hides the web-only tools
                page.evaluate("() => { document.documentElement.dataset.inkdosHost = 'tauri'; }")
                assert link.is_hidden()
                assert not errors, errors
                context.close()

            # translated with the Home language
            context = browser.new_context(service_workers='block')
            context.add_init_script("localStorage.setItem('inkdos2:language', 'pt-BR')")
            page = context.new_page()
            page.goto(BASE + '/index.html', wait_until='load')
            page.wait_for_function("() => (document.querySelector('.beta-office a')?.innerText || '').includes('Office completo')", timeout=10000)
            assert 'celulares' in page.locator('.beta-office small').inner_text()
            # the start page on the tools origin gets the InkDOS appearance and language with the link
            page.locator('.beta-office a').dispatch_event('pointerdown')
            href = page.locator('.beta-office a').get_attribute('href')
            assert href.startswith('https://inkdos-tools.github.io/?') and 'lang=pt-BR' in href and 'inkdos-theme=' in href, href
            browser.close()
    finally:
        server.terminate()
    print('Home: Full office (beta) opens the InkDOS-tools office suite in a new tab, on web only, translated')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Home: the engine switch. Light (default on the web) keeps this Home and the InkDOS editors; Full version switches
the Home right away: on the web it goes to the InkDOS Office Home on the InkDOS-tools origin
(https://inkdos-tools.github.io/), with the InkDOS appearance and language, and this Home keeps sending there while
Full is the choice, until ?engine=light (the Office Home's Light button) brings it back. Translated. In the desktop app
the switch shows too, Full version is the default, and Full or an office card opens InkDOS Office in an office window
of its own (inkdos_open_office) instead of leaving the app. Replaces the "Full office (beta)" button."""
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
OFFICE = 'https://inkdos-tools.github.io/'


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
    office = ('documents', 'spreadsheets', 'presentations')
    others = ('pdf', 'txt', 'epub')
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            for width, height in ((1280, 860), (390, 844)):
                context = browser.new_context(service_workers='block', viewport={'width': width, 'height': height})
                context.route(OFFICE + '**', lambda route: route.fulfill(status=200, content_type='text/html', body='<title>InkDOS Office</title>'))
                page = context.new_page()
                errors: list[str] = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(BASE + '/index.html', wait_until='load')
                assert page.locator('.beta-office').count() == 0, 'the Full office button is replaced by the switch'
                assert page.locator('.engine-switch').is_visible(), width
                href = lambda c: page.get_attribute(f'.workspace-grid a.workspace-card.{c}', 'href')
                light = {c: href(c) for c in office + others}
                # web default: Light, InkDOS editors
                assert page.get_attribute('[data-engine="light"]', 'aria-pressed') == 'true'
                assert all(light[c].startswith('./apps/') for c in office), light
                # the offline status line says whether this browser keeps InkDOS on the device (no worker here)
                page.wait_for_function("() => document.getElementById('engineOffline').dataset.state === 'online'")
                assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth"), width
                assert not errors, errors
                # Full version: the InkDOS Office Home takes the place of this one at once, in this tab
                page.click('[data-engine="complete"]')
                page.wait_for_url(OFFICE + '?*')
                assert 'inkdos-theme=' in page.url, page.url
                # remembered: this Home sends there again
                page.goto(BASE + '/index.html')
                page.wait_for_url(OFFICE + '?*')
                # the Office Home's Light button: ?engine=light keeps this Home, Light chosen, the address cleaned
                page.goto(BASE + '/index.html?engine=light', wait_until='load')
                page.wait_for_timeout(300)
                assert page.url == BASE + '/index.html', page.url
                assert page.get_attribute('[data-engine="light"]', 'aria-pressed') == 'true'
                assert page.evaluate("() => localStorage.getItem('inkdos2:engine')") == 'light'
                assert {c: href(c) for c in office + others} == light
                context.close()

            # desktop app: the switch shows, Full version by default; an office card opens an office window through the
            # host (the card keeps its InkDOS link, so nothing navigates this window away from the app)
            context = browser.new_context(service_workers='block')
            context.add_init_script("""window.InkDOSDesktop = {host: 'tauri'}; window.__calls = [];
                window.__TAURI__ = {core: {invoke: (cmd, args) => { window.__calls.push([cmd, args]); return Promise.resolve(); }}};""")
            page = context.new_page()
            page.goto(BASE + '/index.html', wait_until='load')
            assert page.locator('.engine-switch').is_visible()
            assert page.get_attribute('[data-engine="complete"]', 'aria-pressed') == 'true', 'Full version by default on desktop'
            assert page.get_attribute('a.workspace-card.documents', 'href').startswith('./apps/documents/')
            page.click('a.workspace-card.documents')
            page.wait_for_function("() => window.__calls.length === 1")
            calls = page.evaluate("() => window.__calls")
            assert calls[0][0] == 'inkdos_open_office' and calls[0][1]['theme'] in ('light', 'dark'), calls
            assert page.url.endswith('/index.html'), 'the Home stays'
            page.wait_for_function("() => document.getElementById('engineOffline').textContent === 'Installed on this computer'")
            # the Full button opens it right away as well
            page.click('[data-engine="complete"]')
            page.wait_for_function("() => window.__calls.length === 2")
            assert page.evaluate("() => window.__calls[1][0]") == 'inkdos_open_office'
            assert page.url.endswith('/index.html')
            # Light chosen: the card opens the InkDOS workspace as before
            page.click('[data-engine="light"]')
            page.click('a.workspace-card.pdf')
            page.wait_for_url('**/apps/pdf/**')
            assert page.evaluate("() => localStorage.getItem('inkdos2:engine')") == 'light'
            context.close()

            # translated with the Home language; the Office Home address carries the appearance and language
            context = browser.new_context(service_workers='block')
            context.route(OFFICE + '**', lambda route: route.fulfill(status=200, content_type='text/html', body='<title>InkDOS Office</title>'))
            context.add_init_script("localStorage.setItem('inkdos2:language', 'pt-BR')")
            page = context.new_page()
            page.goto(BASE + '/index.html', wait_until='load')
            page.wait_for_function("() => (document.querySelector('[data-engine=complete]')?.innerText || '').includes('Versão completa')", timeout=10000)
            page.click('[data-engine="complete"]')
            page.wait_for_url(OFFICE + '?*')
            assert 'lang=pt-BR' in page.url and 'inkdos-theme=' in page.url, page.url
            browser.close()
    finally:
        server.terminate()
    print('Home: engine switch (Light / Full version) switches the Home to the chosen one at once (web, desktop window), translated')


if __name__ == '__main__':
    main()

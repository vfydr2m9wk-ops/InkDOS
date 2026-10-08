#!/usr/bin/env python3
"""Home: the engine switch. Light (default on the web) keeps the InkDOS editors behind the Documents, Spreadsheets
and Presentations cards; Full version sends those three cards to the ONLYOFFICE editors of InkDOS Office on the
InkDOS-tools origin (https://inkdos-tools.github.io/), with the InkDOS appearance and language. The choice is
remembered, the other cards never change, the switch is hidden in the desktop app (which keeps the InkDOS editors
until the engine is installed there) and it is translated. Replaces the "Full office (beta)" button."""
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
    office = ('documents', 'spreadsheets', 'presentations')
    others = ('pdf', 'txt', 'epub')
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
                assert page.locator('.beta-office').count() == 0, 'the Full office button is replaced by the switch'
                switch = page.locator('.engine-switch')
                assert switch.is_visible(), width
                href = lambda c: page.get_attribute(f'.workspace-grid a.workspace-card.{c}', 'href')
                light = {c: href(c) for c in office + others}
                # web default: Light, InkDOS editors
                assert page.get_attribute('[data-engine="light"]', 'aria-pressed') == 'true'
                assert all(light[c].startswith('./apps/') for c in office), light
                # Full version: the three office cards lead to InkDOS Office, the others stay
                page.click('[data-engine="complete"]')
                assert page.get_attribute('[data-engine="complete"]', 'aria-pressed') == 'true'
                for c in office:
                    assert href(c).startswith('https://inkdos-tools.github.io/?inkdos-theme='), href(c)
                    assert page.get_attribute(f'a.workspace-card.{c}', 'target') is None  # same tab
                assert {c: href(c) for c in others} == {c: light[c] for c in others}
                assert 'ONLYOFFICE' in page.inner_text('#engineNote')
                assert page.evaluate("() => localStorage.getItem('inkdos2:engine')") == 'complete'
                # remembered after a reload; back to Light restores the InkDOS links
                page.reload(wait_until='load')
                assert href('documents').startswith('https://inkdos-tools.github.io/')
                page.click('[data-engine="light"]')
                assert {c: href(c) for c in office + others} == light
                # the offline status line says whether this browser keeps InkDOS on the device (no worker here)
                page.wait_for_function("() => document.getElementById('engineOffline').dataset.state === 'online'")
                assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth"), width
                # the desktop app hides the switch and keeps the InkDOS editors
                page.click('[data-engine="complete"]')
                page.evaluate("() => { document.documentElement.dataset.inkdosHost = 'tauri'; }")
                assert switch.is_hidden()
                assert not errors, errors
                context.close()

            # desktop host from the start: InkDOS editors even with Full version stored
            context = browser.new_context(service_workers='block')
            context.add_init_script("localStorage.setItem('inkdos2:engine', 'complete'); window.InkDOSDesktop = {host: 'tauri'}")
            page = context.new_page()
            page.goto(BASE + '/index.html', wait_until='load')
            assert page.get_attribute('a.workspace-card.documents', 'href').startswith('./apps/documents/')
            context.close()

            # translated with the Home language; the office link carries the appearance and language
            context = browser.new_context(service_workers='block')
            context.add_init_script("localStorage.setItem('inkdos2:language', 'pt-BR')")
            page = context.new_page()
            page.goto(BASE + '/index.html', wait_until='load')
            page.wait_for_function("() => (document.querySelector('[data-engine=complete]')?.innerText || '').includes('Versão completa')", timeout=10000)
            page.click('[data-engine="complete"]')
            page.wait_for_function("() => (document.getElementById('engineNote').innerText || '').includes('Editores ONLYOFFICE')", timeout=10000)
            page.locator('a.workspace-card.documents').dispatch_event('pointerdown')
            href = page.get_attribute('a.workspace-card.documents', 'href')
            assert href.startswith('https://inkdos-tools.github.io/?') and 'lang=pt-BR' in href and 'inkdos-theme=' in href, href
            browser.close()
    finally:
        server.terminate()
    print('Home: engine switch (Light / Full version) leads the office cards to the chosen editors, web only, translated')


if __name__ == '__main__':
    main()

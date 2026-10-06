#!/usr/bin/env python3
"""Home: the Advanced tools button opens a central, searchable list over a blurred background.

Every listed tool must open an existing page (no dead entries); Escape and the close button
dismiss the dialog; the button is web-only (hidden in the desktop app).
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
PORT = 8814
BASE = f'http://127.0.0.1:{PORT}'
# tool folders published by https://github.com/vfydr2m9wk-ops/InkDOS-tools (its tools.json)
TOOL_FOLDERS = {'archivedrop', 'cyberchef', 'it-tools', 'bentopdf', 'python'}
TOOLS_SITE = 'https://inkdos-tools.github.io/InkDOS-tools/'


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
            context = browser.new_context(service_workers='block', viewport={'width': 1180, 'height': 820})
            page = context.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(BASE + '/index.html', wait_until='load')
            button = page.locator('#advancedToolsButton')
            assert button.is_visible() and 'Advanced tools' in button.inner_text()
            button.click()
            overlay = page.locator('#advancedTools')
            overlay.wait_for(state='visible')
            assert 'blur' in page.evaluate("() => getComputedStyle(document.getElementById('advancedTools')).backdropFilter || getComputedStyle(document.getElementById('advancedTools')).webkitBackdropFilter")
            assert page.evaluate("() => document.activeElement.id") == 'advancedToolsSearch'
            # every listed tool points to a page that exists
            tools = page.evaluate("() => InkDOSAdvancedTools.tools")
            assert tools, 'the catalog must not be empty'
            for tool in tools:
                href = tool['href']
                # third-party tools are served from their own origin, never from the InkDOS one
                assert href.startswith('./') or href.startswith(TOOLS_SITE), href
                if href.startswith('./'):
                    assert (ROOT / href[2:].split('?')[0]).is_file(), href
                else:  # built and served by the InkDOS-tools repository, one folder per tool (or a page inside it)
                    folder = href.removeprefix(TOOLS_SITE).split('/')[0]
                    assert folder, href
                    assert folder in TOOL_FOLDERS, href
            # Home may frame that origin (and nothing else besides itself)
            csp = page.get_attribute('meta[http-equiv="Content-Security-Policy"]', 'content')
            assert "frame-src 'self' https://inkdos-tools.github.io;" in csp, csp
            # the other origin cannot read the InkDOS appearance, so the links carry it
            link = page.get_attribute('.tools-item[data-tool-id="cyberchef"]', 'href')
            assert link.startswith(TOOLS_SITE + 'cyberchef/?inkdos-theme='), link
            assert {'archivedrop', 'cyberchef', 'it-tools', 'bentopdf', 'python'} <= {t['id'] for t in tools}
            # LibreOffice and Apple iWork files open in Documents, Spreadsheets and Presentations instead
            assert not {'pnk', 'odt-view', 'ods-view', 'odp-view'} & {t['id'] for t in tools}
            assert page.locator('.tools-item').count() == len(tools)
            # search filters, and says so when nothing matches
            page.fill('#advancedToolsSearch', 'zzz-no-such-tool')
            assert page.locator('.tools-item').count() == 0 and page.locator('.tools-empty').is_visible()
            page.fill('#advancedToolsSearch', 'signature')
            assert page.locator('.tools-item').count() >= 1
            # Escape closes and returns focus to the button
            page.keyboard.press('Escape')
            overlay.wait_for(state='hidden')
            assert page.evaluate("() => document.activeElement.id") == 'advancedToolsButton'
            # close button and backdrop click close it too
            button.click(); overlay.wait_for(state='visible')
            page.click('#advancedToolsClose'); overlay.wait_for(state='hidden')
            button.click(); overlay.wait_for(state='visible')
            page.mouse.click(10, 10); overlay.wait_for(state='hidden')
            # an entry opens its tool inside the InkDOS tool panel (same bar and theme as the workspaces)
            button.click(); overlay.wait_for(state='visible')
            page.locator('.tools-item[data-tool-id="pdf-tools"]').click()
            tool_panel = page.locator('#toolPanel')
            tool_panel.wait_for(state='visible')
            assert overlay.is_hidden()
            panel_state = page.evaluate("""() => ({ title: document.getElementById('toolPanelTitle').textContent,
                src: document.querySelector('#toolPanel iframe')?.getAttribute('src'),
                full: document.querySelector('#toolPanel [data-tool-full]').getAttribute('href') })""")
            assert panel_state == {'title': 'PDF tools (beta)', 'src': './labs/pdf/index.html', 'full': './labs/pdf/index.html'}, panel_state
            page.frame_locator('#toolPanel iframe').locator('body').wait_for(timeout=15000)
            # back returns to the list, Escape closes everything and drops the frame
            page.click('#toolPanel [data-tool-back]')
            overlay.wait_for(state='visible'); assert tool_panel.is_hidden()
            page.locator('.tools-item[data-tool-id="pdf-tools"]').click(); tool_panel.wait_for(state='visible')
            page.keyboard.press('Escape'); tool_panel.wait_for(state='hidden')
            assert page.locator('#toolPanel iframe').count() == 0 and overlay.is_hidden()
            # "Open full window" leaves for the tool itself
            button.click(); overlay.wait_for(state='visible')
            page.locator('.tools-item[data-tool-id="pdf-tools"]').click(); tool_panel.wait_for(state='visible')
            page.click('#toolPanel [data-tool-full]')
            page.wait_for_url('**/labs/pdf/index.html')
            # desktop app: no Advanced tools button
            page.goto(BASE + '/index.html', wait_until='load')
            page.evaluate("() => { document.documentElement.dataset.inkdosHost = 'tauri'; }")
            assert button.is_hidden()
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Home Advanced tools: central searchable list over a blurred background, entries open existing tools')


if __name__ == '__main__':
    main()

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
TOOL_FOLDERS = {'archivedrop', 'cyberchef', 'it-tools', 'bentopdf', 'python', 'squoosh'}
TOOLS_SITE = 'https://inkdos-offic.pages.dev/InkDOS-tools/'


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
            # the tools site is not loaded for real: a tab opened on it gets a stub page
            context.route(TOOLS_SITE + '**', lambda route: route.fulfill(status=200, content_type='text/html', body='<title>tool</title>'))
            page = context.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(BASE + '/index.html', wait_until='load')
            # the Light Home shows no buttons under the workspaces (owner request): the row is hidden; shown here to
            # keep exercising the catalog behind it
            assert page.locator('.quick-tools').is_hidden()
            unhide = "() => { document.querySelector('.quick-tools').hidden = false; }"
            page.evaluate(unhide)
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
            assert "frame-src 'self' https://inkdos-offic.pages.dev;" in csp, csp
            # the other origin cannot read the InkDOS appearance, so the links carry it
            link = page.get_attribute('.tools-item[data-tool-id="cyberchef"]', 'href')
            assert link.startswith(TOOLS_SITE + 'cyberchef/?inkdos-theme='), link
            assert {'archivedrop', 'cyberchef', 'it-tools', 'bentopdf', 'python'} <= {t['id'] for t in tools}
            # LibreOffice and Apple iWork files open in Documents, Spreadsheets and Presentations instead
            assert not {'pnk', 'odt-view', 'ods-view', 'odp-view'} & {t['id'] for t in tools}
            assert page.locator('.tools-item').count() == len(tools)
            # the PDF toolkit and its conversion shortcuts open in their own tab: Office-to-PDF conversion needs a
            # cross-origin isolated page, which a frame inside InkDOS cannot be
            # Convert comes first, Word <-> PDF at the top, each Office conversion next to its reverse
            assert [t['id'] for t in tools[:5]] == ['word-to-pdf', 'pdf-to-docx', 'excel-to-pdf', 'pdf-to-excel', 'powerpoint-to-pdf'], tools[:5]
            assert all(t['group'] == 'Convert' for t in tools[:5]) and page.locator('.tools-group').first.inner_text().strip().lower() == 'convert'
            toolkit = [t for t in tools if t['href'].startswith(TOOLS_SITE + 'bentopdf/')]
            assert {'bentopdf', 'word-to-pdf', 'pdf-to-docx', 'image-to-pdf', 'compress-pdf'} <= {t['id'] for t in toolkit}, toolkit
            for tool in toolkit:
                assert tool.get('window') and tool['href'].startswith(TOOLS_SITE + 'bentopdf/'), tool
                item = page.locator(f'.tools-item[data-tool-id="{tool["id"]}"]')
                assert (item.get_attribute('target'), item.get_attribute('rel')) == ('_blank', 'noopener'), tool['id']
            with context.expect_page() as opened:
                page.locator('.tools-item[data-tool-id="word-to-pdf"]').click()
            assert opened.value.url.startswith(TOOLS_SITE + 'bentopdf/word-to-pdf.html?inkdos-theme='), opened.value.url
            opened.value.close()
            assert page.locator('#toolPanel iframe').count() == 0
            # where a new tab cannot open (pop-ups blocked, e.g. a web desktop on iPad), the tool opens in the panel
            page.evaluate("() => { window.__open = window.open; window.open = () => null; }")
            button.click(); overlay.wait_for(state='visible')
            page.locator('.tools-item[data-tool-id="word-to-pdf"]').click()
            page.locator('#toolPanel').wait_for(state='visible')
            assert page.get_attribute('#toolPanel iframe', 'src').startswith(TOOLS_SITE + 'bentopdf/word-to-pdf.html?inkdos-theme=')
            page.keyboard.press('Escape'); page.locator('#toolPanel').wait_for(state='hidden')
            page.evaluate("() => { window.open = window.__open; }")
            button.click(); overlay.wait_for(state='visible')
            assert page.locator('.tools-item[data-tool-id="pdf-tools"]').get_attribute('target') is None
            # the image converter (Squoosh, legacy) needs no isolation and opens in the panel like the other tools
            squoosh = next(t for t in tools if t['id'] == 'squoosh')
            assert squoosh['group'] == 'Legacy' and not squoosh.get('window') and squoosh['href'] == TOOLS_SITE + 'squoosh/', squoosh
            assert page.locator('.tools-item[data-tool-id="squoosh"]').get_attribute('target') is None
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
            assert panel_state == {'title': 'PDF signer (legacy)', 'src': './labs/pdf/index.html', 'full': './labs/pdf/index.html'}, panel_state
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
            page.goto(BASE + '/index.html', wait_until='load')
            page.evaluate(unhide)
            # quick tools row on the Home: Convert, OCR, the PDF toolkit and Terminal open their tools directly; the
            # Advanced tools button ends the same row
            row = page.locator('.quick-tools button')
            assert [row.nth(i).get_attribute('data-quick-group') or row.nth(i).get_attribute('data-quick-tool') or row.nth(i).get_attribute('id')
                    for i in range(row.count())] == ['Convert', 'ocr-pdf', 'bentopdf', 'python', 'advancedToolsButton']
            # Convert opens the list with only the conversions (light, inside InkDOS); searching shows every group again
            page.click('[data-quick-group="Convert"]')
            overlay.wait_for(state='visible')
            groups = page.locator('.tools-group').all_inner_texts()
            assert [g.strip().lower() for g in groups] == ['convert'], groups
            page.fill('#advancedToolsSearch', 'pdf')
            assert page.locator('.tools-group').count() > 1
            page.keyboard.press('Escape'); overlay.wait_for(state='hidden')
            with context.expect_page() as opened:
                page.click('[data-quick-tool="ocr-pdf"]')
            assert opened.value.url.startswith(TOOLS_SITE + 'bentopdf/ocr-pdf.html?inkdos-theme='), opened.value.url
            opened.value.close()
            with context.expect_page() as opened:
                page.click('[data-quick-tool="bentopdf"]')
            assert opened.value.url.startswith(TOOLS_SITE + 'bentopdf/?inkdos-theme='), opened.value.url
            opened.value.close()
            # the main PDF tools are direct shortcuts (a toolkit page in its own tab), not only inside the toolkit
            assert {'edit-pdf', 'sign-pdf', 'split-pdf', 'form-filler', 'encrypt-pdf'} <= {t['id'] for t in tools}
            page.click('[data-quick-tool="python"]')
            page.locator('#toolPanel').wait_for(state='visible')
            assert page.get_attribute('#toolPanel iframe', 'src').startswith(TOOLS_SITE + 'python/?inkdos-theme=')
            page.keyboard.press('Escape'); page.locator('#toolPanel').wait_for(state='hidden')
            assert page.evaluate("() => document.activeElement.dataset.quickTool") == 'python'
            # legacy-home-tools: the tools outside the maintained set (PDF toolkit, Python) come last, in Legacy
            tools = page.evaluate("() => InkDOSAdvancedTools.tools")
            assert [t['id'] for t in tools if t['group'] == 'Legacy'] == ['pdf-tools', 'squoosh', 'archivedrop', 'cyberchef', 'it-tools']
            assert [t['group'] for t in tools[-5:]] == ['Legacy'] * 5, tools[-5:]
            assert next(t for t in tools if t['id'] == 'python')['group'] == 'Data analysis'
            # desktop app: no Advanced tools button
            page.goto(BASE + '/index.html', wait_until='load')
            page.evaluate("() => { document.documentElement.dataset.inkdosHost = 'tauri'; }")
            assert button.is_hidden() and page.locator('.quick-tools').is_hidden()
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Home Advanced tools: central searchable list over a blurred background, entries open existing tools')


if __name__ == '__main__':
    main()

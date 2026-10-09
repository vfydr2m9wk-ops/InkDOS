#!/usr/bin/env python3
"""Presentations: Preview shows the open deck with the layout of the PowerPoint file.

The first toolbar button writes the deck to PPTX (as Save copy would) and hands it to the pptx viewer
published by InkDOS-tools (pptx-renderer), embedded in the workspace. A stub speaking the viewer protocol
stands in for it on another origin (localhost instead of 127.0.0.1). Checked here: the button comes first,
the stub receives a PPTX with every slide, editing controls rest while the preview is shown, Preview again
returns to the editable slide, and a new presentation closes the preview.
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
PORT = 8819
BASE = f'http://127.0.0.1:{PORT}'
TOOLS = f'http://localhost:{PORT}/InkDOS-tools/'

STUB = """<!doctype html><meta charset="utf-8"><title>stub viewer</title><body>waiting
<script src="jszip.min.js"></script>
<script>
const inkdos = new URL(document.referrer).origin;
addEventListener('message', async e => {
  if (e.origin !== inkdos || !e.data || e.data.type !== 'inkdos-viewer-open') return;
  const file = e.data.file, zip = await JSZip.loadAsync(await file.arrayBuffer());
  const slides = Object.keys(zip.files).filter(n => /^ppt\\/slides\\/slide\\d+\\.xml$/.test(n)).length;
  document.body.textContent = 'PPTX ' + file.name + ' | slides ' + slides;
  parent.postMessage({type: 'inkdos-viewer-loaded', ok: true}, inkdos);
});
parent.postMessage({type: 'inkdos-viewer-ready'}, inkdos);
</script>"""


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        site = Path(td)
        (site / 'InkDOS').symlink_to(ROOT)
        viewer = site / 'InkDOS-tools' / 'pptx'
        viewer.mkdir(parents=True)
        (viewer / 'index.html').write_text(STUB, encoding='utf-8')
        (viewer / 'jszip.min.js').write_bytes((ROOT / 'apps' / 'presentations' / 'vendor' / 'jszip.min.js').read_bytes())
        server = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=site,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        errors: list[str] = []
        try:
            wait_port()
            with sync_playwright() as pw:
                browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
                # the pages allow only the published tools origin in frame-src; the stub runs on another one
                context = browser.new_context(service_workers='block', viewport={'width': 1280, 'height': 860}, bypass_csp=True)
                context.add_init_script(f'window.InkDOSToolsBase = {TOOLS!r};')
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(BASE + '/InkDOS/apps/presentations/index.html', wait_until='load')
                page.wait_for_function("() => !!globalThis.__inkdosPresentations && !!globalThis.InkDOS2Presentations?.PptxPreview")
                first = page.evaluate("() => document.querySelector('#editbar button')?.id")
                assert first == 'pptPreviewBtn', first
                csp = page.get_attribute('meta[http-equiv="Content-Security-Policy"]', 'content')
                assert 'frame-src' in csp and 'https://inkdos-offic.pages.dev' in csp, csp

                page.click('#startNew')
                page.wait_for_function('() => globalThis.__inkdosPresentations.session.active')
                page.click('#addSlideBtn')
                page.wait_for_function('() => globalThis.__inkdosPresentations.session.slides.length === 2')
                page.click('#pptPreviewBtn')
                frame = page.frame_locator('.external-viewer iframe')
                frame.locator('body', has_text='PPTX ').wait_for(timeout=20000)
                text = frame.locator('body').inner_text()
                assert text.endswith('| slides 2') and '.pptx' in text, text
                src = page.get_attribute('.external-viewer iframe', 'src')
                assert src == TOOLS + 'pptx/?embed=1&inkdos-theme=light', src
                page.wait_for_function("() => (document.getElementById('statusText')?.textContent || '').includes('Preview ·')", timeout=10000)
                state = page.evaluate("""() => ({ pressed: pptPreviewBtn.getAttribute('aria-pressed'),
                    resting: getComputedStyle(document.getElementById('addSlideBtn')).pointerEvents,
                    canvas: getComputedStyle(document.getElementById('viewport')).display })""")
                assert state == {'pressed': 'true', 'resting': 'none', 'canvas': 'none'}, state

                page.click('#pptPreviewBtn')
                assert page.locator('.external-viewer').count() == 0
                state = page.evaluate("""() => ({ pressed: pptPreviewBtn.getAttribute('aria-pressed'),
                    resting: getComputedStyle(document.getElementById('addSlideBtn')).pointerEvents,
                    canvas: getComputedStyle(document.getElementById('viewport')).display === 'none' })""")
                assert state == {'pressed': 'false', 'resting': 'auto', 'canvas': False}, state

                # a new presentation while the preview is shown returns to editing
                page.click('#pptPreviewBtn')
                frame.locator('body', has_text='PPTX ').wait_for(timeout=20000)
                page.evaluate('() => { globalThis.__inkdosPresentations.newPresentation(); }')
                deadline = time.time() + 10
                while time.time() < deadline and page.locator('.external-viewer').count():
                    discard = page.locator('#presentationsUnsavedDialog [data-choice="discard"]')
                    if discard.count() and discard.first.is_visible():
                        discard.first.click()
                    page.wait_for_timeout(200)
                assert page.locator('.external-viewer').count() == 0
                assert page.evaluate("() => globalThis.__inkdosPresentations.session.slides.length") == 1
                assert not errors, errors
                browser.close()
        finally:
            server.terminate()
    print('Presentations: Preview shows the deck in the InkDOS-tools pptx viewer and returns to editing')


if __name__ == '__main__':
    main()

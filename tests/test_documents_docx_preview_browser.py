#!/usr/bin/env python3
"""Documents: Preview shows the open document with the layout of the Word file.

The first toolbar button writes the document to DOCX (as Save copy would) and hands it to the docx viewer
published by InkDOS-tools (docx-preview), embedded in the workspace. A stub speaking the viewer protocol
stands in for it on another origin (localhost instead of 127.0.0.1). Checked here: the button comes first,
the stub receives a DOCX holding the current (edited) text, editing controls rest while the preview is
shown, Preview again returns to the editable pages, and opening a document closes the preview.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_documents_external_viewer_browser import BASE, PORT, ROOT, minimal_docx, tools_base, use_stub_tools, wait_port  # noqa: E402

STUB = """<!doctype html><meta charset="utf-8"><title>stub viewer</title><body>waiting
<script src="jszip.min.js"></script>
<script>
const inkdos = new URL(document.referrer).origin;
addEventListener('message', async e => {
  if (e.origin !== inkdos || !e.data || e.data.type !== 'inkdos-viewer-open') return;
  const file = e.data.file, zip = await JSZip.loadAsync(await file.arrayBuffer());
  const xml = await zip.file('word/document.xml').async('string');
  const text = [...new DOMParser().parseFromString(xml, 'application/xml').getElementsByTagNameNS('*', 't')].map(t => t.textContent).join('');
  document.body.textContent = 'DOCX ' + file.name + ' | ' + text;
  parent.postMessage({type: 'inkdos-viewer-loaded', ok: true}, inkdos);
});
parent.postMessage({type: 'inkdos-viewer-ready'}, inkdos);
</script>"""


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        site = Path(td)
        (site / 'InkDOS').symlink_to(ROOT)
        viewer = site / 'InkDOS-tools' / 'docx'
        viewer.mkdir(parents=True)
        (viewer / 'index.html').write_text(STUB, encoding='utf-8')
        (viewer / 'jszip.min.js').write_bytes((ROOT / 'apps' / 'documents' / 'vendor' / 'jszip.min.js').read_bytes())
        files = site / 'files'
        files.mkdir()
        (files / 'Letter.docx').write_bytes(minimal_docx())
        server = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=site,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        errors: list[str] = []
        try:
            wait_port()
            with sync_playwright() as pw:
                browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
                context = browser.new_context(service_workers='block', viewport={'width': 1280, 'height': 860}, bypass_csp=True)
                use_stub_tools(context, PORT)
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(BASE + '/InkDOS/apps/documents/index.html', wait_until='load')
                page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!globalThis.InkDOS2Documents?.DocxPreview")
                first = page.evaluate("() => document.querySelector('#formatbar > button')?.id")
                assert first == 'docPreviewBtn', first

                page.set_input_files('#fileInput', str(files / 'Letter.docx'))
                page.wait_for_function("() => InkDOS2Documents.DocumentsApp.session.kind === 'docx'", timeout=15000)
                # an edit made in InkDOS is part of the preview
                page.evaluate("""() => { const p = document.querySelector('.page-content p') || document.querySelector('.page-content');
                    p.append(' plus edit'); p.dispatchEvent(new InputEvent('input', {bubbles: true})); }""")
                page.click('#docPreviewBtn')
                frame = page.frame_locator('.external-viewer iframe')
                frame.locator('body', has_text='DOCX ').wait_for(timeout=15000)
                text = frame.locator('body').inner_text()
                assert text.startswith('DOCX Letter.docx | ') and 'Editable docx plus edit' in text, text
                src = page.get_attribute('.external-viewer iframe', 'src')
                assert src == tools_base(PORT) + 'docx/?embed=1&inkdos-theme=light', src
                page.wait_for_function("() => (document.getElementById('statusText')?.textContent || '').includes('Preview')", timeout=10000)
                state = page.evaluate("""() => ({ pressed: docPreviewBtn.getAttribute('aria-pressed'),
                    resting: getComputedStyle(document.getElementById('undoBtn')).pointerEvents,
                    pages: document.getElementById('pagesHost').style.display })""")
                assert state == {'pressed': 'true', 'resting': 'none', 'pages': 'none'}, state

                # Preview again: back to the editable pages
                page.click('#docPreviewBtn')
                assert page.locator('.external-viewer').count() == 0
                state = page.evaluate("""() => ({ pressed: docPreviewBtn.getAttribute('aria-pressed'),
                    resting: getComputedStyle(document.getElementById('undoBtn')).pointerEvents,
                    pages: document.getElementById('pagesHost').style.display,
                    editable: [...document.querySelectorAll('.page-content')].some(p => p.isContentEditable) })""")
                assert state == {'pressed': 'false', 'resting': 'auto', 'pages': '', 'editable': True}, state

                # opening a document while the preview is shown returns to editing
                page.click('#docPreviewBtn')
                frame.locator('body', has_text='DOCX ').wait_for(timeout=15000)
                assert page.locator('.external-viewer').count() == 1
                page.set_input_files('#fileInput', str(files / 'Letter.docx'))
                page.get_by_role('button', name='Discard').click()  # the edit above is unsaved
                page.wait_for_function("() => !document.querySelector('.external-viewer') && document.getElementById('pagesHost').style.display === ''", timeout=15000)
                assert not errors, errors
                browser.close()
        finally:
            server.terminate()
    print('Documents: Preview shows the document in the InkDOS-tools docx viewer and returns to editing')


if __name__ == '__main__':
    main()

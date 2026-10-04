#!/usr/bin/env python3
"""Work safety: unsaved work survives a closed tab in Documents, Spreadsheets and Presentations.

For each workspace: make an unsaved change, let the recovery draft be written, close the tab
(pagehide), open the workspace again in a new tab: the recovery notice must appear, and
'Recover' must bring the change back as an unsaved document. Saving (not dirty) removes the
draft. Everything is built in the page; nothing leaves the browser profile.
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
PORT = 8793

CASES = {
    'documents': {
        'ready': "() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!globalThis.InkDOSWorkSafety",
        'edit': """async () => { const A=globalThis.InkDOS2Documents.DocumentsApp; await A.newDocument();
            await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
            const pc=document.querySelector('.page-content'); pc.innerHTML='<p>RECOVERYMARKER words</p>'; A.session.markDirty(); }""",
        'check': "() => ({ dirty: globalThis.InkDOS2Documents.DocumentsApp.session.dirty, text: [...document.querySelectorAll('.page-content')].map(p=>p.innerText).join(' ') })",
        'marker': 'RECOVERYMARKER',
    },
    'spreadsheets': {
        'ready': "() => !!globalThis.__inkdosSpreadsheetsS1 && !!globalThis.InkDOSWorkSafety",
        'edit': """async () => { const api=globalThis.__inkdosSpreadsheetsS1; await api.openController.newWorkbook();
            api.editor.editor.commitValue('RECOVERYMARKER',0,0); }""",
        'check': "() => { const s=globalThis.__inkdosSpreadsheetsS1.session; return { dirty: s.dirty, text: String(s.book?.sheets?.[0]?.cells?.get('A1')?.v ?? '') } }",
        'marker': 'RECOVERYMARKER',
    },
    'presentations': {
        'ready': "() => !!globalThis.__inkdosPresentations && !!globalThis.InkDOSWorkSafety",
        'edit': """async () => { const api=globalThis.__inkdosPresentations; await api.newPresentation();
            const o=api.session.addText(); o.text='RECOVERYMARKER'; if(o.paragraphs) o.paragraphs=[{runs:[{text:'RECOVERYMARKER'}]}]; api.session.markDirty(); }""",
        'check': "() => { const s=globalThis.__inkdosPresentations.session; return { dirty: !!s.dirty, text: JSON.stringify(s.slides?.map(x=>x.objects?.map(o=>o.text))) } }",
        'marker': 'RECOVERYMARKER',
    },
}


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
            context = browser.new_context(service_workers='block', viewport={'width': 1280, 'height': 900})
            for app, case in CASES.items():
                url = f'http://127.0.0.1:{PORT}/apps/{app}/index.html'
                first = context.new_page()
                first.on('pageerror', lambda e, a=app: errors.append(f'{a}: {e}'))
                first.on('dialog', lambda d: d.accept())
                first.goto(url, wait_until='load')
                first.wait_for_function(case['ready'], timeout=30000)
                first.evaluate(case['edit'])
                first.evaluate("async () => { for (const h of InkDOSWorkSafety._test.handles) await h.snapshotNow(); }")
                drafts = first.evaluate(f"async () => (await InkDOSWorkSafety._test.allDrafts()).filter(d=>d.app==='{app}').length")
                assert drafts == 1, (app, drafts)
                # stored encrypted: no plaintext body or file name in the record
                sealed = first.evaluate(f"""async () => {{ const d=(await InkDOSWorkSafety._test.allDrafts()).find(d=>d.app==='{app}');
                    const hay=new TextDecoder('latin1').decode(d.body.ct); return {{ v:d.v, plain:'data' in d, marker:hay.includes('RECOVERYMARKER'), nameIsBytes: d.name.ct instanceof Uint8Array }} }}""")
                assert sealed == {'v': 2, 'plain': False, 'marker': False, 'nameIsBytes': True}, (app, sealed)
                first.close(run_before_unload=False)

                second = context.new_page()
                second.on('pageerror', lambda e, a=app: errors.append(f'{a}: {e}'))
                second.goto(url, wait_until='load')
                second.wait_for_function(case['ready'], timeout=30000)
                second.wait_for_selector('.inkdos-safety-bar', timeout=15000)
                second.locator('.inkdos-safety-bar button').first.click()
                second.wait_for_function(f"() => ({case['check']})().text.includes('{case['marker']}')", timeout=30000)
                got = second.evaluate(case['check'])
                assert got['dirty'], (app, 'recovered work must stay unsaved', got)
                # once this page has a draft and is saved (not dirty), its draft goes away
                second.evaluate("async () => { for (const h of InkDOSWorkSafety._test.handles) await h.snapshotNow(); }")
                left = second.evaluate(f"async () => (await InkDOSWorkSafety._test.allDrafts()).filter(d=>d.app==='{app}').length")
                assert left == 1, (app, 'the recovered draft is replaced by this page draft', left)
                second.close(run_before_unload=False)
            # turning drafts off deletes them and stops new ones
            page = context.new_page()
            page.goto(f'http://127.0.0.1:{PORT}/apps/spreadsheets/index.html', wait_until='load')
            page.wait_for_function(CASES['spreadsheets']['ready'], timeout=30000)
            page.evaluate(CASES['spreadsheets']['edit'])
            page.evaluate("async () => { await InkDOSWorkSafety.setDraftsEnabled(false); for (const h of InkDOSWorkSafety._test.handles) await h.snapshotNow(); }")
            assert page.evaluate("async () => (await InkDOSWorkSafety._test.allDrafts()).length") == 0
            page.evaluate("() => InkDOSWorkSafety.setDraftsEnabled(true)")
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('Work safety: unsaved work recovered after a closed tab in Documents, Spreadsheets and Presentations')


if __name__ == '__main__':
    main()

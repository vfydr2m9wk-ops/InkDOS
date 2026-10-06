#!/usr/bin/env python3
"""Spreadsheets and Presentations: OpenDocument and Apple iWork files open view-only in the workspace.

.ods/.numbers (Spreadsheets) and .odp/.key (Presentations) are shown by the InkDOS-tools viewer on the
same origin; a stub speaking the viewer protocol stands in for it (see
test_documents_external_viewer_browser.py). Checked: the right viewer is embedded and gets the file,
the session cannot be saved, shared, renamed, edited or presented, and a new workbook/presentation
afterwards closes the viewer and is editable again.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_documents_external_viewer_browser import STUB  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PORT = 8819
BASE = f'http://127.0.0.1:{PORT}'


def wait_port() -> None:
    import socket
    import time
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def check_spreadsheets(page, files: Path) -> None:
    page.goto(BASE + '/InkDOS/apps/spreadsheets/index.html', wait_until='load')
    page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1 && !!globalThis.InkDOS2Spreadsheets?.ExternalViewer")
    accept = page.get_attribute('#fileInput', 'accept')
    assert '.ods' in accept and '.numbers' in accept, accept
    for name, viewer in (('Budget.ods', 'odf'), ('Budget.numbers', 'pnk')):
        page.set_input_files('#fileInput', str(files / name))
        page.wait_for_function("(n) => (document.getElementById('statusText')?.textContent || '').includes(n + ' · View only · shown')", arg=name, timeout=15000)
        assert f'VIEWER {viewer} {name}' in page.frame_locator('.external-viewer iframe').locator('body').inner_text(timeout=10000)
        assert page.get_attribute('.external-viewer iframe', 'src').endswith(f'/InkDOS-tools/{viewer}/?embed=1')
        state = page.evaluate("""async () => {
            const api = globalThis.__inkdosSpreadsheetsS1, s = api.session;
            return { kind: s.sourceKind, name: s.fileName, rename: s.rename('Other.xlsx'),
                     save: await api.saveController.save(), share: await api.saveController.share(),
                     xlsx: await api.saveController.exportAs('xlsx'), pdf: await api.saveController.exportPdf({}),
                     bold: api.editor.commands.execute('format.bold'), dirty: s.dirty,
                     menuSave: document.getElementById('menuSave').disabled };
        }""")
        assert state == {'kind': 'view', 'name': name, 'rename': name, 'save': False, 'share': False, 'xlsx': False,
                         'pdf': False, 'bold': False, 'dirty': False, 'menuSave': True}, state
    page.evaluate("async () => { await globalThis.__inkdosSpreadsheetsS1.openController.newWorkbook(); }")
    page.wait_for_function("() => globalThis.__inkdosSpreadsheetsS1.session.sourceKind !== 'view'")
    assert page.locator('.external-viewer').count() == 0
    assert page.evaluate("() => document.getElementById('gridStage').style.display") == ''
    assert page.evaluate("() => globalThis.__inkdosSpreadsheetsS1.editor.editor.commitValue('fresh', 0, 0) !== false")


def check_presentations(page, files: Path) -> None:
    page.goto(BASE + '/InkDOS/apps/presentations/index.html', wait_until='load')
    page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p2Tools && !!globalThis.InkDOS2Presentations?.ExternalViewer")
    accept = page.get_attribute('#fileInput', 'accept')
    assert '.odp' in accept and '.key' in accept, accept
    for name, viewer in (('Deck.odp', 'odf'), ('Deck.key', 'pnk')):
        page.set_input_files('#fileInput', str(files / name))
        page.wait_for_function("(n) => (document.getElementById('statusText')?.textContent || '').includes(n + ' · View only · shown')", arg=name, timeout=15000)
        assert f'VIEWER {viewer} {name}' in page.frame_locator('.external-viewer iframe').locator('body').inner_text(timeout=10000)
        state = page.evaluate("""() => {
            const a = globalThis.__inkdosPresentations, run = id => a.executeCommand(id);
            return { kind: a.session.sourceKind, title: document.getElementById('titleText').value,
                     save: run('file.save'), share: run('file.share'), slide: run('slide.add'),
                     present: run('presentation.present.start'), dirty: a.session.dirty,
                     saveBtn: document.getElementById('saveMenuBtn').disabled };
        }""")
        assert state == {'kind': 'view', 'title': name, 'save': False, 'share': False, 'slide': False,
                         'present': False, 'dirty': False, 'saveBtn': True}, state
    page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('file.new')")
    page.wait_for_function("() => globalThis.__inkdosPresentations.session.sourceKind === 'new'")
    assert page.locator('.external-viewer').count() == 0
    assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('slide.add')") is True


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        site = Path(td)
        (site / 'InkDOS').symlink_to(ROOT)
        for viewer in ('odf', 'pnk'):
            (site / 'InkDOS-tools' / viewer).mkdir(parents=True)
            (site / 'InkDOS-tools' / viewer / 'index.html').write_text(STUB.replace('__NAME__', viewer), encoding='utf-8')
        files = site / 'files'
        files.mkdir()
        for name in ('Budget.ods', 'Budget.numbers', 'Deck.odp', 'Deck.key'):
            (files / name).write_bytes(b'PK stand-in')
        server = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=site,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        errors: list[str] = []
        try:
            wait_port()
            with sync_playwright() as pw:
                browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
                for check in (check_spreadsheets, check_presentations):
                    context = browser.new_context(service_workers='block', viewport={'width': 1280, 'height': 860})
                    page = context.new_page()
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    check(page, files)
                    context.close()
                assert not errors, errors
                browser.close()
        finally:
            server.terminate()
    print('Spreadsheets and Presentations: ODF and iWork files open view-only in the embedded viewer')


if __name__ == '__main__':
    main()

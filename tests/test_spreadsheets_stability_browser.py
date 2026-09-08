#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

ROOT_PORT = 8784
BASE = f'http://127.0.0.1:{ROOT_PORT}'


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', ROOT_PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local Spreadsheets test server did not start')


def stop_server(server: subprocess.Popen | None) -> None:
    if server is None or server.poll() is not None:
        return
    server.terminate()
    try:
        server.wait(timeout=3)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=3)


def main() -> None:
    browser_name = os.environ.get('BROWSER', 'chromium').strip().lower()
    if browser_name not in {'chromium', 'firefox', 'webkit'}:
        raise RuntimeError(f'Unsupported BROWSER={browser_name}')

    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    server: subprocess.Popen | None = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(ROOT_PORT), '--bind', '127.0.0.1'],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={'width': 1360, 'height': 900})
            page = context.new_page()
            page.on('pageerror', lambda exc: errors.append(f'pageerror: {exc}'))
            page.on('console', lambda msg: errors.append(f'console.error: {msg.text}') if msg.type == 'error' else None)

            # Install and activate the suite service worker, then enter the workspace
            # through a controlled page so offline reload exercises the real app shell.
            page.goto(BASE + '/index.html', wait_until='load')
            assert page.evaluate("() => 'serviceWorker' in navigator") is True, browser_name
            page.evaluate('async () => { await navigator.serviceWorker.ready; return true; }')
            page.reload(wait_until='load')
            page.wait_for_function('() => !!navigator.serviceWorker.controller')

            page.goto(BASE + '/apps/spreadsheets/', wait_until='load')
            page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')
            page.wait_for_selector('.inkdos-toolbar-rail')

            boot = page.evaluate("""() => ({
                startVisible:!document.getElementById('startState').hidden,
                railCount:document.querySelectorAll('.inkdos-toolbar-rail').length,
                toolbarInside:!!document.querySelector('.inkdos-toolbar-rail > #formatbar'),
                arrows:document.querySelectorAll('.inkdos-toolbar-arrow').length,
                xlsx:!!globalThis.LocalXLSX,
                xls:!!globalThis.LocalXLS,
            })""")
            assert boot == {
                'startVisible': True,
                'railCount': 1,
                'toolbarInside': True,
                'arrows': 2,
                'xlsx': True,
                'xls': True,
            }, (browser_name, boot)

            created = page.evaluate("""async () => {
                const api=globalThis.__inkdosSpreadsheetsS1;
                const ok=await api.openController.newWorkbook();
                return {
                    ok,
                    loaded:!!api.session.book?.loaded,
                    sheets:api.session.book?.sheets?.length||0,
                    fileName:api.session.fileName,
                    editor:!!api.editor?.editor,
                    dirty:api.session.dirty,
                };
            }""")
            assert created == {
                'ok': True,
                'loaded': True,
                'sheets': 1,
                'fileName': 'Untitled.xlsx',
                'editor': True,
                'dirty': False,
            }, (browser_name, created)

            # Semantic mutation and toolbar projection share one history model.
            edited = page.evaluate("""() => {
                const api=globalThis.__inkdosSpreadsheetsS1;
                api.editor.editor.commitValue('42',0,0);
                const cell=api.session.activeSheet().cells.get('A1');
                return {value:cell?.v,dirty:api.session.dirty,undo:!document.getElementById('undoBtn').disabled};
            }""")
            assert edited == {'value': 42, 'dirty': True, 'undo': True}, (browser_name, edited)

            page.click('#boldBtn')
            bold = page.evaluate("() => !!globalThis.__inkdosSpreadsheetsS1.session.activeSheet().cells.get('A1')?.style?.font?.bold")
            assert bold is True, browser_name
            page.click('#undoBtn')
            bold_after_undo = page.evaluate("() => !!globalThis.__inkdosSpreadsheetsS1.session.activeSheet().cells.get('A1')?.style?.font?.bold")
            assert bold_after_undo is False, browser_name
            page.click('#redoBtn')
            bold_after_redo = page.evaluate("() => !!globalThis.__inkdosSpreadsheetsS1.session.activeSheet().cells.get('A1')?.style?.font?.bold")
            assert bold_after_redo is True, browser_name

            # A command is a semantic operation, not the toolbar control that happens
            # to invoke it. Removing Italic must not destroy formatting or Undo.
            command_probe = page.evaluate("""() => {
                const api=globalThis.__inkdosSpreadsheetsS1;
                document.getElementById('italicBtn').remove();
                const registered=api.editor.commands.has('format.italic');
                api.editor.commands.execute('format.italic');
                const applied=!!api.session.activeSheet().cells.get('A1')?.style?.font?.italic;
                api.editor.commands.execute('edit.undo');
                const undone=!api.session.activeSheet().cells.get('A1')?.style?.font?.italic;
                return {registered,applied,undone};
            }""")
            assert command_probe == {'registered': True, 'applied': True, 'undone': True}, (browser_name, command_probe)

            # Writer -> parser round-trip must preserve the edited cell, and the same
            # generated XLSX must be accepted transactionally by FileOpenController.
            roundtrip = page.evaluate("""async () => {
                const api=globalThis.__inkdosSpreadsheetsS1;
                const blob=await globalThis.LocalXLSX.saveCopy(api.session.book);
                const bytes=await blob.arrayBuffer();
                const parsed=await globalThis.LocalXLSX.parseWorkbook(bytes,'roundtrip.xlsx');
                const parsedCell=parsed.sheets[0].cells.get('A1');
                const file=new File([blob],'roundtrip.xlsx',{
                    type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    lastModified:Date.now(),
                });
                const result=await api.openController.handle(file);
                const reopened=api.session.activeSheet().cells.get('A1');
                return {
                    blobSize:blob.size,
                    parsedValue:parsedCell?.v,
                    status:result.status,
                    reopenedValue:reopened?.v,
                    sourceKind:api.session.sourceKind,
                    fileName:api.session.fileName,
                    dirty:api.session.dirty,
                };
            }""")
            assert roundtrip['blobSize'] > 500, (browser_name, roundtrip)
            assert roundtrip['parsedValue'] == 42, (browser_name, roundtrip)
            assert roundtrip['status'] == 'committed', (browser_name, roundtrip)
            assert roundtrip['reopenedValue'] == 42, (browser_name, roundtrip)
            assert roundtrip['sourceKind'] == 'xlsx', (browser_name, roundtrip)
            assert roundtrip['fileName'] == 'roundtrip.xlsx', (browser_name, roundtrip)
            assert roundtrip['dirty'] is False, (browser_name, roundtrip)

            if errors:
                raise AssertionError('\n'.join(errors))

            # Real offline boot: remove the origin rather than relying on browser
            # offline emulation, which has historically been unreliable in WebKit.
            errors.clear()
            stop_server(server)
            server = None
            page.reload(wait_until='load', timeout=20_000)
            page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1', timeout=15_000)
            offline = page.evaluate("""() => ({
                xlsx:!!globalThis.LocalXLSX,
                workbookEditor:!!globalThis.InkDOS2Spreadsheets?.WorkbookEditor,
                fileOpen:!!globalThis.InkDOS2Spreadsheets?.FileOpenController,
                rail:document.querySelectorAll('.inkdos-toolbar-rail').length===1,
                startVisible:!document.getElementById('startState').hidden,
            })""")
            assert all(offline.values()), (browser_name, offline)
            if errors:
                raise AssertionError('\n'.join(errors))

            browser.close()
        print(f'Spreadsheets stability browser ({browser_name}): OK')
    finally:
        stop_server(server)


if __name__ == '__main__':
    main()

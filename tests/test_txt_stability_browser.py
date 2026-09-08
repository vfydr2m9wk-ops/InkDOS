#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8782
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def main() -> None:
    browser_name = os.environ.get('BROWSER', 'chromium').strip().lower()
    if browser_name not in {'chromium', 'firefox', 'webkit'}:
        raise RuntimeError(f'Unsupported BROWSER={browser_name}')

    server = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={'width': 1360, 'height': 900})
            page.on('pageerror', lambda exc: errors.append(f'pageerror: {exc}'))
            page.on('console', lambda msg: errors.append(f'console.error: {msg.text}') if msg.type == 'error' else None)
            page.goto(BASE + '/apps/txt/', wait_until='load')
            page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")

            # Empty-state start actions are semantic commands, not drawer-button delegation.
            assert page.locator('#startState').is_visible()
            empty = page.evaluate("() => ({loaded:InkDOS2.TxtAppDebug.state.loaded, save:document.getElementById('saveBtn').disabled, share:document.getElementById('shareBtn').disabled})")
            assert empty == {'loaded': False, 'save': True, 'share': True}, empty
            start_probe = page.evaluate(
                """() => {
                    const d=InkDOS2.TxtAppDebug;
                    const input=document.getElementById('fileInput');
                    globalThis.__txtStartOpenRequested=false;
                    input.click=()=>{globalThis.__txtStartOpenRequested=true};
                    document.getElementById('openBtn').remove();
                    return {open:d.commands.has('file.open.request'),newDoc:d.commands.has('file.new')};
                }"""
            )
            assert start_probe == {'open': True, 'newDoc': True}, start_probe
            page.click('#startOpen')
            assert page.evaluate("() => globalThis.__txtStartOpenRequested") is True
            page.evaluate("() => document.getElementById('newBtn').remove()")
            page.click('#startNew')
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.loaded && document.getElementById('startState').hidden")
            assert not page.locator('#saveBtn').is_disabled()
            assert not page.locator('#shareBtn').is_disabled()

            # Typing drives authoritative history/session state.
            editor = page.locator('#editor')
            editor.fill('alpha beta alpha')
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.session.dirty && InkDOS2.TxtAppDebug.state.history.canUndo")
            assert page.locator('#counts').inner_text().startswith('1 line · 3 words')

            # Semantic history survives removal of its toolbar controls.
            command_probe = page.evaluate(
                """() => {
                    const d=InkDOS2.TxtAppDebug;
                    document.getElementById('undoBtn').remove();
                    document.getElementById('redoBtn').remove();
                    return {undo:d.commands.has('history.undo'),redo:d.commands.has('history.redo')};
                }"""
            )
            assert command_probe == {'undo': True, 'redo': True}, command_probe
            page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('history.undo')")
            assert editor.input_value() == ''
            page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('history.redo')")
            assert editor.input_value() == 'alpha beta alpha'

            # Find/replace semantics survive removal of their command controls.
            page.click('#findBtn')
            page.locator('#findInput').fill('alpha')
            page.wait_for_function("() => document.getElementById('findStatus').textContent.includes('2 match')")
            find_probe = page.evaluate(
                """() => {
                    const d=InkDOS2.TxtAppDebug;
                    for(const id of ['findPrev','findNext','replaceOneBtn','replaceAllBtn'])document.getElementById(id)?.remove();
                    return {
                        prev:d.commands.has('find.prev'),
                        next:d.commands.has('find.next'),
                        one:d.commands.has('replace.one'),
                        all:d.commands.has('replace.all'),
                    };
                }"""
            )
            assert find_probe == {'prev': True, 'next': True, 'one': True, 'all': True}, find_probe
            assert page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('find.next','alpha')") is True
            assert page.evaluate("() => document.getElementById('editor').value.slice(document.getElementById('editor').selectionStart,document.getElementById('editor').selectionEnd)") == 'alpha'
            replaced = page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('replace.all','alpha','gamma')")
            assert replaced == 2, replaced
            assert editor.input_value() == 'gamma beta gamma'
            assert 'replacement' in page.locator('#status').inner_text().lower()
            page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('history.undo')")
            assert editor.input_value() == 'alpha beta alpha'
            page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('history.redo')")
            assert editor.input_value() == 'gamma beta gamma'

            # Line numbers follow semantic view policy even after view controls are removed.
            before_text = editor.input_value()
            page.evaluate("() => InkDOS2.TxtAppDebug.txtT1.setLineNumbers(true)")
            page.wait_for_function("() => document.querySelectorAll('#lineNumberLayer .t1-line-number').length > 0")
            view_probe = page.evaluate(
                """() => {
                    const d=InkDOS2.TxtAppDebug;
                    for(const id of ['wrapBtn','fontSize','fontDownBtn','fontUpBtn'])document.getElementById(id)?.remove();
                    return {wrap:d.commands.has('view.wrap.toggle'),font:d.commands.has('view.font.set')};
                }"""
            )
            assert view_probe == {'wrap': True, 'font': True}, view_probe
            page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('view.wrap.toggle')")
            page.evaluate("() => InkDOS2.TxtAppDebug.commands.execute('view.font.set',20)")
            page.wait_for_function(
                """() => {
                    const mirror=document.getElementById('lineNumberMirror'),editor=document.getElementById('editor');
                    return mirror.classList.contains('no-wrap') && getComputedStyle(mirror).fontSize===getComputedStyle(editor).fontSize && document.querySelectorAll('#lineNumberLayer .t1-line-number').length>0;
                }"""
            )
            semantic_view = page.evaluate(
                """() => ({
                    wrap:InkDOS2.TxtAppDebug.state.wrap,
                    fontSize:InkDOS2.TxtAppDebug.state.fontSize,
                    mirrorNoWrap:document.getElementById('lineNumberMirror').classList.contains('no-wrap'),
                    mirrorFont:getComputedStyle(document.getElementById('lineNumberMirror')).fontSize,
                    editorFont:getComputedStyle(document.getElementById('editor')).fontSize,
                    lineNumbers:document.querySelectorAll('#lineNumberLayer .t1-line-number').length,
                })"""
            )
            assert semantic_view['wrap'] is False, semantic_view
            assert semantic_view['fontSize'] == 20, semantic_view
            assert semantic_view['mirrorNoWrap'] is True, semantic_view
            assert semantic_view['mirrorFont'] == semantic_view['editorFont'], semantic_view
            assert semantic_view['lineNumbers'] > 0, semantic_view
            assert editor.input_value() == before_text

            # Transactional open decodes TXT bytes and resets history without using the file picker.
            page.evaluate("() => InkDOS2.TxtAppDebug.initializeEmptyState()")
            opened = page.evaluate(
                """async () => {
                    const d = InkDOS2.TxtAppDebug;
                    const bytes = new Uint8Array([111,110,101,13,10,116,119,111]);
                    await d.openBytes('sample.txt', bytes);
                    return {
                        loaded:d.state.loaded,
                        fileName:d.state.fileName,
                        text:document.getElementById('editor').value,
                        encoding:d.state.encoding,
                        lineEnding:d.state.lineEnding,
                        canUndo:d.state.history.canUndo,
                    };
                }"""
            )
            assert opened['loaded'] is True, opened
            assert opened['fileName'] == 'sample.txt', opened
            assert opened['text'] == 'one\ntwo', opened
            assert opened['encoding'] == 'utf-8', opened
            assert opened['lineEnding'] == '\r\n', opened
            assert opened['canUndo'] is False, opened

            # Encoding/BOM/line endings affect export bytes while preserving editor text.
            page.click('#textToolsBtn')
            page.locator('#encodingSelect').select_option('utf-16le')
            page.locator('#lineEndingSelect').select_option('crlf')
            export_probe = page.evaluate(
                """() => ({
                    bytes:Array.from(InkDOS2.TxtAppDebug.exportBytes()),
                    text:document.getElementById('editor').value,
                    encoding:InkDOS2.TxtAppDebug.state.encoding,
                    bom:InkDOS2.TxtAppDebug.state.bom,
                    lineEnding:InkDOS2.TxtAppDebug.state.lineEnding,
                })"""
            )
            assert export_probe['text'] == 'one\ntwo', export_probe
            assert export_probe['encoding'] == 'utf-16le', export_probe
            assert export_probe['bom'] is True, export_probe
            assert export_probe['lineEnding'] == '\r\n', export_probe
            assert export_probe['bytes'][:2] == [255, 254], export_probe
            encoded = bytes(export_probe['bytes'])
            assert b'o\x00n\x00e\x00\r\x00\n\x00t\x00w\x00o\x00' in encoded, export_probe

            # Viewport remains measurable after the editing and IO churn above.
            viewport = page.evaluate("() => InkDOS2.TxtAppDebug.viewport()")
            assert viewport and viewport['availableWidth'] > 0 and viewport['availableHeight'] > 0, viewport
            browser.close()

        if errors:
            raise AssertionError({'browser': browser_name, 'errors': errors})
        print(f'Plain Text stability browser baseline passed on {browser_name}.')
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == '__main__':
    main()

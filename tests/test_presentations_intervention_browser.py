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
PORT = 8786
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
    browser_name = os.environ.get('BROWSER', 'chromium').strip().lower()
    if browser_name not in {'chromium', 'firefox', 'webkit'}:
        raise RuntimeError(f'Unsupported BROWSER={browser_name}')
    server = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={'width': 1360, 'height': 900})
            page.goto(BASE + '/apps/presentations/', wait_until='load')
            page.wait_for_function('() => !!globalThis.__inkdosPresentations?.p1Tools')
            page.click('#startNew')
            page.wait_for_function('() => globalThis.__inkdosPresentations.session.active')
            page.click('#insertTextBtn')
            page.wait_for_function('() => !!globalThis.__inkdosPresentations.selection.objectId')

            textbox = page.locator('.slide-textbox.selected')
            content = textbox.locator('.rich-text-content')
            assert textbox.count() == 1

            # Object mode is the default: insertion/first selection must not silently enter text editing.
            assert content.get_attribute('contenteditable') == 'false', (browser_name, 'text editing activated on selection')
            assert textbox.get_attribute('data-text-editing') != 'true'

            # A deliberate second activation enters text-edit mode.
            textbox.dblclick()
            page.wait_for_function("() => document.querySelector('.slide-textbox.selected')?.dataset.textEditing === 'true'")
            assert content.get_attribute('contenteditable') == 'true'

            # Overflowing text remains present and is not clipped by the text-content box itself.
            page.evaluate(
                """() => {
                    const content=document.querySelector('.slide-textbox.selected .rich-text-content');
                    content.textContent='Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6';
                    content.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:null}));
                }"""
            )
            overflow = page.evaluate(
                """() => {
                    const content=document.querySelector('.slide-textbox.selected .rich-text-content');
                    return {overflow:getComputedStyle(content).overflow,scrollHeight:content.scrollHeight,clientHeight:content.clientHeight,text:content.innerText};
                }"""
            )
            assert overflow['overflow'] == 'visible', (browser_name, overflow)
            assert 'Line 6' in overflow['text'], overflow

            # Escape commits/exits editing and returns to object mode.
            page.keyboard.press('Escape')
            page.wait_for_function("() => document.querySelector('.slide-textbox.selected')?.dataset.textEditing !== 'true'")
            assert content.get_attribute('contenteditable') == 'false'

            # Dragging the selected object body changes geometry; undo restores it.
            before = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations;
                    const o=app.selection.getObject(app.session);
                    return {x:o.x,y:o.y};
                }"""
            )
            box = textbox.bounding_box()
            assert box
            sx, sy = box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.5
            page.mouse.move(sx, sy)
            page.mouse.down()
            page.mouse.move(sx + 40, sy + 30, steps=4)
            page.mouse.up()
            after = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations;
                    const o=app.selection.getObject(app.session);
                    return {x:o.x,y:o.y};
                }"""
            )
            assert (after['x'], after['y']) != (before['x'], before['y']), (browser_name, before, after)
            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.undo')") is True
            restored = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations;
                    const o=app.selection.getObject(app.session);
                    return {x:o.x,y:o.y};
                }"""
            )
            assert restored == before, (browser_name, before, restored)
            browser.close()
        print(f'Presentations intervention browser RED/GREEN probe passed on {browser_name}.')
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == '__main__':
    main()

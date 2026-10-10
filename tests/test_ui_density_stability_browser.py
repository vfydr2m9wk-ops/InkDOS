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
PORT = 8799
BASE = f'http://127.0.0.1:{PORT}'
POINTER_QUERY = '(hover: hover) and (pointer: fine)'

WORKSPACES = [
    '/index.html',
    '/apps/documents/index.html?suite=1',
    '/apps/spreadsheets/index.html?suite=1',
    '/apps/presentations/index.html?suite=1',
    '/apps/pdf/index.html?suite=1',
    '/apps/txt/index.html?suite=1',
    '/apps/epub/index.html?suite=1',
]


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')


def fine_pointer_script(matches: bool) -> str:
    value = 'true' if matches else 'false'
    return f"""
(() => {{
  const nativeMatchMedia = window.matchMedia.bind(window);
  let finePointer = {value};
  const listeners = new Set();
  const pointerMql = {{
    media:{POINTER_QUERY!r},
    onchange:null,
    get matches(){{ return finePointer; }},
    addListener(fn){{ listeners.add(fn); }},
    removeListener(fn){{ listeners.delete(fn); }},
    addEventListener(type,fn){{ if(type==='change') listeners.add(fn); }},
    removeEventListener(type,fn){{ if(type==='change') listeners.delete(fn); }},
    dispatchEvent(){{ return true; }}
  }};
  window.__inkdosSetFinePointer = next => {{
    finePointer = !!next;
    const event = {{matches:finePointer,media:pointerMql.media}};
    listeners.forEach(fn => fn.call(pointerMql,event));
    if(typeof pointerMql.onchange === 'function') pointerMql.onchange.call(pointerMql,event);
  }};
  window.matchMedia = query => query === {POINTER_QUERY!r} ? pointerMql : nativeMatchMedia(query);
}})();
"""


def root_state(page):
    return page.evaluate("""()=>({
      density:document.documentElement.getAttribute('data-ui-density'),
      preference:document.documentElement.getAttribute('data-ui-density-preference'),
      controlCount:document.querySelectorAll('[data-inkdos-density-control]').length,
      storageKey:globalThis.InkDOSUiDensity?.STORAGE_KEY||'',
      stored:globalThis.InkDOSUiDensity?localStorage.getItem(globalThis.InkDOSUiDensity.STORAGE_KEY):null,
      legacy:localStorage.getItem('inkdos2:ui-density'),
      control:getComputedStyle(document.documentElement).getPropertyValue('--control').trim(),
      topbar:document.querySelector('.topbar')?.getBoundingClientRect().height||0
    })""")


def main() -> None:
    browser_name = os.environ.get('BROWSER', 'chromium')
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

            # Owner decision (2026-10-10): always the desktop density, on any screen and pointer, with no density
            # controls; a stored or requested 'mobile' no longer changes it.
            for viewport, fine in (({'width': 1360, 'height': 900}, True), ({'width': 720, 'height': 900}, False), ({'width': 390, 'height': 844}, False)):
                context = browser.new_context(viewport=viewport)
                context.add_init_script(fine_pointer_script(fine))
                context.add_init_script("localStorage.setItem('inkdos2:documents:ui-density','mobile')")
                page = context.new_page()
                for path in WORKSPACES:
                    page.goto(BASE + path, wait_until='load')
                    page.wait_for_function("() => !!globalThis.InkDOSUiDensity")
                    page.wait_for_timeout(300)
                    state = root_state(page)
                    assert state['density'] == 'desktop', (viewport, path, state)
                    assert state['preference'] == 'desktop', (viewport, path, state)
                    assert state['controlCount'] == 0, (viewport, path, state)
                page.goto(BASE + '/apps/documents/index.html?suite=1', wait_until='load')
                page.wait_for_function("() => !!globalThis.InkDOSUiDensity")
                switched = page.evaluate("() => globalThis.InkDOSUiDensity.set('mobile')")
                state = root_state(page)
                assert switched == 'desktop' and state['density'] == 'desktop' and state['control'] == '30px', (viewport, state)
                context.close()

            browser.close()

        print(f'Desktop-only interface density browser ({browser_name}): OK')
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == '__main__':
    main()

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
  window.matchMedia = query => {{
    if (query === {POINTER_QUERY!r}) {{
      return {{matches:{value},media:query,onchange:null,addListener(){{}},removeListener(){{}},addEventListener(){{}},removeEventListener(){{}},dispatchEvent(){{return true}}}};
    }}
    return nativeMatchMedia(query);
  }};
}})();
"""


def root_state(page):
    return page.evaluate("""()=>({
      density:document.documentElement.getAttribute('data-ui-density'),
      preference:document.documentElement.getAttribute('data-ui-density-preference'),
      controlCount:document.querySelectorAll('[data-inkdos-density-control]').length,
      stored:localStorage.getItem('inkdos2:ui-density'),
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

            desktop_context = browser.new_context(viewport={'width': 1360, 'height': 900})
            desktop_context.add_init_script(fine_pointer_script(True))
            page = desktop_context.new_page()

            for path in WORKSPACES:
                page.goto(BASE + path, wait_until='load')
                page.wait_for_function("() => !!globalThis.InkDOSUiDensity")
                page.wait_for_function("() => document.querySelectorAll('[data-inkdos-density-control]').length === 1")
                state = root_state(page)
                assert state['density'] == 'desktop', (path, state)
                assert state['preference'] == 'auto', (path, state)
                assert state['controlCount'] == 1, (path, state)

            page.goto(BASE + '/apps/documents/index.html?suite=1', wait_until='load')
            page.wait_for_function("() => document.querySelectorAll('[data-inkdos-density-control]').length === 1")
            desktop = root_state(page)
            assert desktop['control'] == '30px', desktop
            assert 0 < desktop['topbar'] <= 46, desktop

            switched = page.evaluate("""()=>{
              const before=location.href;
              const effective=globalThis.InkDOSUiDensity.set('mobile');
              return {before,after:location.href,effective,
                density:document.documentElement.dataset.uiDensity,
                preference:globalThis.InkDOSUiDensity.preference,
                stored:localStorage.getItem('inkdos2:ui-density'),
                control:getComputedStyle(document.documentElement).getPropertyValue('--control').trim()};
            }""")
            assert switched['before'] == switched['after'], switched
            assert switched['effective'] == 'mobile', switched
            assert switched['density'] == 'mobile', switched
            assert switched['preference'] == 'mobile', switched
            assert switched['stored'] == 'mobile', switched
            assert switched['control'] == '42px', switched

            page.goto(BASE + '/apps/spreadsheets/index.html?suite=1', wait_until='load')
            page.wait_for_function("() => !!globalThis.InkDOSUiDensity")
            persisted = root_state(page)
            assert persisted['density'] == 'mobile', persisted
            assert persisted['preference'] == 'mobile', persisted
            assert persisted['stored'] == 'mobile', persisted

            returned = page.evaluate("""()=>({
              effective:globalThis.InkDOSUiDensity.set('auto'),
              density:document.documentElement.dataset.uiDensity,
              preference:globalThis.InkDOSUiDensity.preference,
              stored:localStorage.getItem('inkdos2:ui-density')
            })""")
            assert returned['effective'] == 'desktop', returned
            assert returned['density'] == 'desktop', returned
            assert returned['preference'] == 'auto', returned
            assert returned['stored'] == 'auto', returned
            desktop_context.close()

            mobile_context = browser.new_context(viewport={'width': 720, 'height': 900})
            mobile_context.add_init_script(fine_pointer_script(False))
            mobile = mobile_context.new_page()
            mobile.goto(BASE + '/apps/documents/index.html?suite=1', wait_until='load')
            mobile.wait_for_function("() => !!globalThis.InkDOSUiDensity")
            mobile.wait_for_function("() => document.querySelectorAll('[data-inkdos-density-control]').length === 1")
            mobile_state = root_state(mobile)
            assert mobile_state['density'] == 'mobile', mobile_state
            assert mobile_state['preference'] == 'auto', mobile_state
            assert mobile_state['control'] == '42px', mobile_state
            mobile_context.close()

            browser.close()

        print(f'Adaptive interface density browser ({browser_name}): OK')
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == '__main__':
    main()

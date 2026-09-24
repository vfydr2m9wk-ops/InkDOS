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
                expected_key = 'inkdos2:ui-density' if path == '/index.html' else 'inkdos2:' + path.split('/')[2].split('?')[0] + ':ui-density'
                assert state['storageKey'] == expected_key, (path, state)

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
                storageKey:globalThis.InkDOSUiDensity.STORAGE_KEY,
                stored:localStorage.getItem(globalThis.InkDOSUiDensity.STORAGE_KEY),
                legacy:localStorage.getItem('inkdos2:ui-density'),
                control:getComputedStyle(document.documentElement).getPropertyValue('--control').trim()};
            }""")
            assert switched['before'] == switched['after'], switched
            assert switched['effective'] == 'mobile', switched
            assert switched['density'] == 'mobile', switched
            assert switched['preference'] == 'mobile', switched
            assert switched['storageKey'] == 'inkdos2:documents:ui-density', switched
            assert switched['stored'] == 'mobile', switched
            assert switched['legacy'] is None, switched
            assert switched['control'] == '42px', switched

            # A workspace-local choice in Documents must not carry into Spreadsheets.
            page.goto(BASE + '/apps/spreadsheets/index.html?suite=1', wait_until='load')
            page.wait_for_function("() => !!globalThis.InkDOSUiDensity")
            independent = root_state(page)
            assert independent['density'] == 'desktop', independent
            assert independent['preference'] == 'auto', independent
            assert independent['stored'] is None, independent
            assert independent['storageKey'] == 'inkdos2:spreadsheets:ui-density', independent

            # Returning to Documents sees its own persisted preference.
            page.goto(BASE + '/apps/documents/index.html?suite=1', wait_until='load')
            page.wait_for_function("() => !!globalThis.InkDOSUiDensity")
            returned = root_state(page)
            assert returned['density'] == 'mobile', returned
            assert returned['preference'] == 'mobile', returned
            assert returned['stored'] == 'mobile', returned
            assert returned['storageKey'] == 'inkdos2:documents:ui-density', returned
            page.evaluate("() => globalThis.InkDOSUiDensity.set('auto')")
            reset = root_state(page)
            assert reset['density'] == 'desktop', reset
            assert reset['preference'] == 'auto', reset
            assert reset['stored'] == 'auto', reset

            # Automatic density must follow viewport changes without a reload.
            page.set_viewport_size({'width': 720, 'height': 900})
            page.wait_for_function("() => document.documentElement.dataset.uiDensity === 'mobile'")
            resized_mobile = root_state(page)
            assert resized_mobile['preference'] == 'auto', resized_mobile
            assert resized_mobile['density'] == 'mobile', resized_mobile

            page.set_viewport_size({'width': 1360, 'height': 900})
            page.wait_for_function("() => document.documentElement.dataset.uiDensity === 'desktop'")
            resized_desktop = root_state(page)
            assert resized_desktop['density'] == 'desktop', resized_desktop

            # Automatic density must also follow a pointer capability change.
            page.evaluate("() => window.__inkdosSetFinePointer(false)")
            page.wait_for_function("() => document.documentElement.dataset.uiDensity === 'mobile'")
            pointer_mobile = root_state(page)
            assert pointer_mobile['density'] == 'mobile', pointer_mobile
            page.evaluate("() => window.__inkdosSetFinePointer(true)")
            page.wait_for_function("() => document.documentElement.dataset.uiDensity === 'desktop'")
            pointer_desktop = root_state(page)
            assert pointer_desktop['density'] == 'desktop', pointer_desktop
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

        print(f'Workspace-local adaptive interface density browser ({browser_name}): OK')
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == '__main__':
    main()

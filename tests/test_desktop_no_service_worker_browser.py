#!/usr/bin/env python3
"""Desktop host: the web edition's offline service worker is never used inside the desktop app.

On Windows the desktop pages are served from http://tauri.localhost, so the web service worker
registered itself and kept serving the previous version's cached Home after a desktop update.
The bridge (desktop/desktop-host.js, injected first in every page) must refuse registration,
remove an earlier worker and its caches, and reload a page that the old worker served.
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
PORT = 8807
BASE = f"http://127.0.0.1:{PORT}"

MOCK = r"""
window.__TAURI__ = {
  dialog: { message: async () => {}, open: async () => null, save: async () => null },
  fs: { readFile: async () => new Uint8Array(), writeFile: async () => {} },
  opener: {},
  core: { invoke: async () => null }
};
"""


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


STATE = """async () => ({
  controlled: !!navigator.serviceWorker.controller,
  registrations: (await navigator.serviceWorker.getRegistrations()).length,
  caches: (await caches.keys()).filter(name => name.startsWith('inkdos-v')).length
})"""


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    host = (ROOT / "desktop" / "desktop-host.js").read_text(encoding="utf-8")
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 900})

            # an earlier install: the web service worker controls the Home and caches the app shell
            web = context.new_page()
            web.goto(BASE + "/index.html", wait_until="load")
            web.evaluate("() => navigator.serviceWorker.ready")
            web.reload(wait_until="load")
            before = web.evaluate(STATE)
            assert before["controlled"] and before["registrations"] == 1 and before["caches"] >= 1, before
            web.close()

            # the desktop bridge runs before the page's own scripts, as the staged desktop pages do
            desktop = context.new_page()
            errors: list[str] = []
            desktop.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            # like the staged <head> injection: run once the document element exists
            desktop.add_init_script(MOCK + "\nfunction __inkdosHost(){\n" + host + "\n}\n"
                                    "(function run(){if(document.documentElement){__inkdosHost();return}"
                                    "new MutationObserver((_, observer)=>{if(document.documentElement){observer.disconnect();__inkdosHost()}})"
                                    ".observe(document,{childList:true})})();")
            desktop.goto(BASE + "/index.html", wait_until="load")
            desktop.wait_for_function("() => sessionStorage.getItem('inkdos:desktop-sw-cleared') === '1' && !navigator.serviceWorker.controller",
                                      timeout=15000)
            desktop.wait_for_load_state("load")
            time.sleep(1.0)
            after = desktop.evaluate(STATE)
            assert after == {"controlled": False, "registrations": 0, "caches": 0}, after
            refused = desktop.evaluate("() => navigator.serviceWorker.register('./service-worker.js').then(() => 'registered', () => 'refused')")
            assert refused == "refused", refused
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"Desktop app does not use the web service worker ({browser_name}): OK")


if __name__ == "__main__":
    main()

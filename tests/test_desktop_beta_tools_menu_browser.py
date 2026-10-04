#!/usr/bin/env python3
"""Desktop host: Settings lists the installed beta tools and opens them through the host.

The Tauri bridge (desktop/desktop-host.js) runs against a mocked __TAURI__: the menu shows the
tools of the installed (signed) bundle, a click checks for a newer bundle and then opens the tool
in the host; if the host cannot open it, the user gets the host's error. Web behavior (new tab)
is covered by test_pdf_beta_tools_handoff_browser.py.
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
PORT = 8806
BASE = f"http://127.0.0.1:{PORT}"

MOCK = r"""
window.__mockCalls = [];
window.__mockFailOpen = false;
window.__TAURI__ = {
  dialog: { message: async (text, opts) => { window.__mockCalls.push(['dialog', text]); },
            open: async () => null, save: async () => null },
  fs: { readFile: async () => new Uint8Array(), writeFile: async () => {} },
  opener: {},
  core: { invoke: async (cmd, args) => {
    window.__mockCalls.push([cmd, args || null]);
    if (cmd === 'inkdos_beta_status') return { configured: true, installedVersion: 4,
      tools: [{ id: 'pdf', title: 'PDF tools (beta)', entry: 'labs/pdf/index.html' },
              { id: 'scan', title: 'Scanner (beta)', entry: 'labs/scan/index.html' }] };
    if (cmd === 'inkdos_beta_update') throw 'offline';
    if (cmd === 'inkdos_beta_open') { if (window.__mockFailOpen) throw 'Beta tool not found: pdf'; return null; }
    return null;
  } }
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


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(service_workers="block", viewport={"width": 1280, "height": 900})
            context.add_init_script(MOCK)
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.goto(BASE + "/apps/pdf/index.html", wait_until="load")
            page.add_script_tag(url=BASE + "/desktop/desktop-host.js")
            page.wait_for_function("() => globalThis.InkDOSDesktop?.betaTools?.tools.length === 2")
            page.wait_for_selector('[data-frame-action="sun"]', timeout=15000)

            # the menu lists the installed bundle's tools
            page.click('[data-frame-action="sun"]')
            options = page.eval_on_selector_all(".inkdos-settings-option[data-settings-value^='beta-']",
                                                "els => els.map(e => [e.dataset.settingsValue, e.textContent])")
            assert options == [["beta-pdf", "PDF tools (beta)"], ["beta-scan", "Scanner (beta)"]], options
            page.keyboard.press("Escape")
            page.evaluate("() => { window.__mockCalls = []; }")

            # update check first (offline is tolerated), then open in the host
            page.click('[data-frame-action="sun"]')
            page.click(".inkdos-settings-option[data-settings-value='beta-pdf']")
            page.wait_for_function("() => window.__mockCalls.some(c => c[0] === 'inkdos_beta_open')")
            calls = [c for c in page.evaluate("() => window.__mockCalls") if c[0].startswith("inkdos_beta_") and c[0] != "inkdos_beta_status"]
            assert calls == [["inkdos_beta_update", None], ["inkdos_beta_open", {"tool": "pdf"}]], calls
            assert len(context.pages) == 1, "desktop must not open a browser tab"

            # the host's error reaches the user when it cannot open the tool
            page.evaluate("() => { window.__mockFailOpen = true; window.__mockCalls = []; }")
            page.click('[data-frame-action="sun"]')
            page.click(".inkdos-settings-option[data-settings-value='beta-pdf']")
            page.wait_for_function("() => window.__mockCalls.some(c => c[0] === 'dialog')")
            message = [c for c in page.evaluate("() => window.__mockCalls") if c[0] == "dialog"][0][1]
            assert "Beta tool not found" in message, message
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"Desktop beta tools menu ({browser_name}): OK")


if __name__ == "__main__":
    main()

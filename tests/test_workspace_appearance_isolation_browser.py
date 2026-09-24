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
PORT = 8820
BASE = f"http://127.0.0.1:{PORT}"

WORKSPACES = {
    "documents": ("/apps/documents/index.html?suite=1", "inkdos2:documents:appearance", "globalThis.InkDOS2Documents?.Appearance?.set"),
    "spreadsheets": ("/apps/spreadsheets/index.html?suite=1", "inkdos2:spreadsheets:appearance", "globalThis.InkDOS2Spreadsheets?.Appearance?.set"),
    "presentations": ("/apps/presentations/index.html?suite=1", "inkdos2:presentations:appearance", "globalThis.InkDOS2Presentations?.Appearance?.set"),
    "pdf": ("/apps/pdf/index.html?suite=1", "inkdos2:pdf:p1:appearance", "globalThis.InkDOS2PdfP4?.Appearance?.set"),
    "epub": ("/apps/epub/index.html?suite=1", "inkdos2:epub:appearance", "globalThis.InkDOS2Epub?.AppearanceController?.apply"),
    "txt": ("/apps/txt/index.html?suite=1", "inkdos2:txt:appearance", "globalThis.InkDOS2?.AppearanceController?.apply"),
}


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")


def set_mode(page, app: str, mode: str) -> None:
    _, _, setter = WORKSPACES[app]
    page.wait_for_function(f"() => typeof {setter} === 'function'")
    page.evaluate(f"() => {setter}({mode!r})")
    page.wait_for_function(f"() => document.documentElement.dataset.appearanceMode === {mode!r}")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 820})
            page = context.new_page()

            docs_path, docs_key, _ = WORKSPACES["documents"]
            page.goto(BASE + docs_path, wait_until="load")
            set_mode(page, "documents", "dark")
            assert page.evaluate(f"() => localStorage.getItem({docs_key!r})") == "dark"
            assert page.evaluate("() => localStorage.getItem('inkdos2:appearance')") is None

            sheets_path, sheets_key, _ = WORKSPACES["spreadsheets"]
            page.goto(BASE + sheets_path, wait_until="load")
            page.wait_for_function("() => document.documentElement.dataset.appearanceMode === 'system'")
            set_mode(page, "spreadsheets", "light")
            assert page.evaluate(f"() => localStorage.getItem({sheets_key!r})") == "light"
            assert page.evaluate(f"() => localStorage.getItem({docs_key!r})") == "dark"
            assert page.evaluate("() => localStorage.getItem('inkdos2:appearance')") is None

            page.goto(BASE + docs_path, wait_until="load")
            page.wait_for_function("() => document.documentElement.dataset.appearanceMode === 'dark'")
            assert page.evaluate(f"() => localStorage.getItem({sheets_key!r})") == "light"

            # 2.5.2 suite appearance migrates once into an app-local key.
            migration = browser.new_context(viewport={"width": 1280, "height": 820})
            migration.add_init_script("""(() => {
              localStorage.setItem('inkdos2:appearance','dark');
            })();""")
            migrated = migration.new_page()
            epub_path, epub_key, _ = WORKSPACES["epub"]
            migrated.goto(BASE + epub_path, wait_until="load")
            migrated.wait_for_function("() => document.documentElement.dataset.appearanceMode === 'dark'")
            assert migrated.evaluate(f"() => localStorage.getItem({epub_key!r})") == "dark"
            set_mode(migrated, "epub", "light")
            assert migrated.evaluate(f"() => localStorage.getItem({epub_key!r})") == "light"
            assert migrated.evaluate("() => localStorage.getItem('inkdos2:appearance')") == "dark"
            migration.close()

            # Existing app-local preference wins over the legacy suite value on first paint.
            priority = browser.new_context(viewport={"width": 1280, "height": 820})
            priority.add_init_script("""(() => {
              localStorage.setItem('inkdos2:appearance','dark');
              localStorage.setItem('inkdos2:txt:appearance','light');
            })();""")
            priority_page = priority.new_page()
            txt_path, _, _ = WORKSPACES["txt"]
            priority_page.goto(BASE + txt_path, wait_until="load")
            priority_page.wait_for_function("() => document.documentElement.dataset.appearanceMode === 'light'")
            priority.close()

            context.close()
            browser.close()
        print(f"InkDOS 2.6 workspace-local appearance browser ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

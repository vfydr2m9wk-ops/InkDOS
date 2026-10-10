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
    "documents": ("/apps/documents/index.html?suite=1", "inkdos2:appearance", "globalThis.InkDOS2Documents?.Appearance?.set"),
    "spreadsheets": ("/apps/spreadsheets/index.html?suite=1", "inkdos2:appearance", "globalThis.InkDOS2Spreadsheets?.Appearance?.set"),
    "presentations": ("/apps/presentations/index.html?suite=1", "inkdos2:appearance", "globalThis.InkDOS2Presentations?.Appearance?.set"),
    "pdf": ("/apps/pdf/index.html?suite=1", "inkdos2:appearance", "globalThis.InkDOS2PdfP4?.Appearance?.set"),
    "epub": ("/apps/epub/index.html?suite=1", "inkdos2:appearance", "globalThis.InkDOS2Epub?.AppearanceController?.apply"),
    "txt": ("/apps/txt/index.html?suite=1", "inkdos2:appearance", "globalThis.InkDOS2?.AppearanceController?.apply"),
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

            # Owner decision (2026-10-09): one InkDOS theme shared by every workspace, never the system's.
            docs_path, key, _ = WORKSPACES["documents"]
            page.goto(BASE + docs_path, wait_until="load")
            set_mode(page, "documents", "dark")
            assert page.evaluate(f"() => localStorage.getItem({key!r})") == "dark"

            # another workspace opens in the same theme, and changing it there changes it for all
            for app in ("spreadsheets", "presentations", "pdf", "epub", "txt"):
                path, _, _ = WORKSPACES[app]
                page.goto(BASE + path, wait_until="load")
                page.wait_for_function("() => document.documentElement.dataset.theme === 'dark'")
            set_mode(page, "txt", "light")
            page.goto(BASE + docs_path, wait_until="load")
            page.wait_for_function("() => document.documentElement.dataset.theme === 'light'")

            # an open workspace follows a change made in another one at once
            other = context.new_page()
            sheets_path, _, _ = WORKSPACES["spreadsheets"]
            other.goto(BASE + sheets_path, wait_until="load")
            set_mode(other, "spreadsheets", "dark")
            page.wait_for_function("() => document.documentElement.dataset.theme === 'dark'")
            set_mode(other, "spreadsheets", "light")
            other.close()

            # an old System value counts as Light; the system's dark mode is never followed
            system = browser.new_context(viewport={"width": 1280, "height": 820}, color_scheme="dark")
            system.add_init_script("(() => { localStorage.setItem('inkdos2:appearance','system'); })();")
            system_page = system.new_page()
            for app in ("documents", "epub", "txt"):
                path, _, _ = WORKSPACES[app]
                system_page.goto(BASE + path, wait_until="load")
                system_page.wait_for_function("() => document.documentElement.dataset.theme === 'light'")
            system.close()

            # Native WebKit/XeOS controls must follow the workspace-selected theme,
            # not the host OS scheme. Reproduce dark host + explicitly light app.
            native = browser.new_context(viewport={"width": 1280, "height": 820}, color_scheme="dark")
            native_page = native.new_page()
            native_page.goto(BASE + docs_path, wait_until="load")
            set_mode(native_page, "documents", "light")
            native_scheme = native_page.evaluate("""() => ({
              root: getComputedStyle(document.documentElement).colorScheme,
              controls: [...document.querySelectorAll('#styleSelect,#fontSelect,#sizeSelect,#alignmentSelect,#lineSpacing')]
                .map(el => getComputedStyle(el).colorScheme)
            })""")
            assert native_scheme["root"] == "light", native_scheme
            assert native_scheme["controls"] and all(x == "light" for x in native_scheme["controls"]), native_scheme
            native.close()

            context.close()
            browser.close()
        print(f"InkDOS shared appearance browser ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

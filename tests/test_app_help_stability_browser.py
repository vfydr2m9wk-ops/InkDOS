#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

PORT = 8791
BASE = f"http://127.0.0.1:{PORT}"
APPS = {
    "documents": "Documents",
    "epub": "EPUB Reader",
    "pdf": "PDF Workspace",
    "presentations": "Presentations",
    "spreadsheets": "Spreadsheets",
    "txt": "Plain Text",
}


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local App Help test server did not start")


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
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    server: subprocess.Popen | None = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []

    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)

            for app, title in APPS.items():
                errors.clear()
                page.goto(f"{BASE}/apps/{app}/", wait_until="load")
                page.wait_for_selector("[data-inkdos-help-entry]", state="attached", timeout=10000)

                result = page.evaluate(
                    """(expectedTitle) => {
                        const entry = document.querySelector('[data-inkdos-help-entry]');
                        const icon = entry?.querySelector('svg[data-icon="CircleHelp"]');
                        const dialog = document.querySelector('[data-inkdos-help-dialog]');
                        entry?.click();
                        const opened = !!dialog?.open;
                        const heading = dialog?.querySelector('h2')?.textContent?.trim() || '';
                        dialog?.querySelector('[data-inkdos-help-close]')?.click();
                        return {
                            label: entry?.textContent?.trim() || '',
                            icon: !!icon,
                            hasPopup: entry?.getAttribute('aria-haspopup') === 'dialog',
                            opened,
                            heading,
                            closed: !dialog?.open,
                            titleMatch: heading.includes(expectedTitle),
                        };
                    }""",
                    title,
                )
                assert result == {
                    "label": "Help",
                    "icon": True,
                    "hasPopup": True,
                    "opened": True,
                    "heading": f"{title} Help",
                    "closed": True,
                    "titleMatch": True,
                }, (browser_name, app, result)
                assert not errors, (browser_name, app, errors)

            context.close()
            browser.close()
    finally:
        stop_server(server)

    print(f"App Help browser behavior: PASS ({browser_name})")


if __name__ == "__main__":
    main()

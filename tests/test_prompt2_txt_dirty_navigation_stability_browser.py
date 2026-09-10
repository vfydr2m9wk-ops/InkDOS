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
PORT = 8789
BASE = f"http://127.0.0.1:{PORT}"


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
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1360, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/txt/", wait_until="load")
            page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")

            page.click("#startNew")
            editor = page.locator("#editor")
            editor.fill("unsaved prompt 2 change")
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.session.dirty === true")

            # INKBUG-001: in-app Home navigation must be guarded before leaving.
            home = page.locator("#homeBtn")
            assert home.count() == 1, "Plain Text Home control must expose a guarded semantic target"
            home.click()
            assert page.url.endswith("/apps/txt/"), page.url
            assert page.locator("#discardDialog").is_visible()
            assert page.locator("#discardSave").is_visible()
            assert page.locator("#discardContinue").is_visible()
            assert page.locator("#discardCancel").is_visible()

            # Cancel keeps the editor and dirty state intact.
            page.click("#discardCancel")
            assert page.url.endswith("/apps/txt/"), page.url
            assert editor.input_value() == "unsaved prompt 2 change"
            assert page.evaluate("() => InkDOS2.TxtAppDebug.state.session.dirty") is True

            # Successful Save clears only the saved revision and then continues navigation.
            page.evaluate(
                """() => {
                    InkDOS2.FileDelivery.deliver = async (blob, fileName) => ({
                        fileName,
                        method: 'file-system-access',
                        deliveryConfirmed: true,
                        bytes: blob.size,
                        sha256: 'a'.repeat(64),
                    });
                }"""
            )
            home.click()
            page.click("#discardSave")
            page.wait_for_url(BASE + "/index.html")

            # Re-enter, dirty again, and verify explicit Discard proceeds without saving.
            page.goto(BASE + "/apps/txt/", wait_until="load")
            page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")
            page.click("#startNew")
            page.locator("#editor").fill("discard me")
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.session.dirty === true")
            page.click("#homeBtn")
            page.click("#discardContinue")
            page.wait_for_url(BASE + "/index.html")

            browser.close()

        if errors:
            raise AssertionError("Browser runtime errors:\n" + "\n".join(errors))
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    main()

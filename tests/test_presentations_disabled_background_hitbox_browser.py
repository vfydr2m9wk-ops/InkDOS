#!/usr/bin/env python3
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8791
BASE = f"http://127.0.0.1:{PORT}"


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Presentations test server did not start")


def main():
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 810})
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(BASE + "/apps/presentations/index.html", wait_until="load")
            page.wait_for_timeout(200)

            bg = page.locator("#pptP1Background")
            assert bg.count() == 1
            assert bg.is_disabled()

            # A disabled full-size transparent color input must never become
            # the hit target above unrelated toolbar controls.
            pointer_events = bg.evaluate("el => getComputedStyle(el).pointerEvents")
            assert pointer_events == "none", pointer_events

            zoom = page.locator("#zoomMenuBtn")
            assert zoom.is_visible() and zoom.is_enabled()
            zoom.click(timeout=2500)
            page.wait_for_selector("#zoomPopover:not([hidden])")
            page.keyboard.press("Escape")

            right = page.get_by_role("button", name="Scroll toolbar right")
            assert right.is_visible() and right.is_enabled()
            right.click(timeout=2500)

            # Once a presentation becomes active, the background picker is
            # enabled. Its transparent input must remain contained by its
            # visible wrapper and must not overlap unrelated controls.
            page.locator("#startNew").click()
            page.wait_for_function("() => document.getElementById('startState')?.hidden === true")
            assert not bg.is_disabled()
            assert bg.evaluate("el => !!el.closest('.ppt-p1-color-control')")
            assert bg.evaluate("el => el.parentElement?.classList.contains('ppt-p1-color-control')")

            zoom.click(timeout=2500)
            page.wait_for_selector("#zoomPopover:not([hidden])")
            page.keyboard.press("Escape")

            present = page.locator("#presentBtn")
            assert present.is_visible() and present.is_enabled()
            present.click(timeout=2500)
            page.wait_for_selector("#presentOverlay:not([hidden])")
            page.locator("[data-present-exit]").click(timeout=2500)

            assert not errors, errors
            context.close()
            browser.close()
        print("Presentations disabled background hitbox regression passed.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

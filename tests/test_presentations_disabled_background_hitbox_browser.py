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
        browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
        if browser_name not in {"chromium", "firefox", "webkit"}:
            raise RuntimeError(f"Unsupported BROWSER={browser_name}")
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 810})
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(BASE + "/apps/presentations/index.html", wait_until="load")
            page.wait_for_timeout(200)

            icon = page.locator(".presentation-title .presentations-icon")
            assert icon.count() == 1 and icon.is_visible()
            assert icon.locator("use").get_attribute("href") == "#inkdosPresentationsIcon"
            assert page.locator(".presentation-title img.presentations-icon").count() == 0

            bg = page.locator("#pptP1Background")
            assert bg.count() == 1
            assert bg.is_disabled()
            assert bg.get_attribute("type") == "button"
            assert "Background" in bg.inner_text()
            assert page.locator("#pptBackgroundPopover").count() == 1
            assert page.locator("#pptBackgroundPopover [data-background-color]").count() == 12
            assert page.locator("#pptP1Background[type='color']").count() == 0

            # The background control is a normal toolbar button, not a hidden
            # native color input that can fail to open or create a bad hitbox.
            assert bg.get_attribute("aria-haspopup") == "dialog"
            assert bg.get_attribute("aria-expanded") == "false"

            zoom = page.locator("#zoomMenuBtn")
            assert zoom.is_visible() and zoom.is_enabled()
            zoom.click(timeout=2500)
            page.wait_for_selector("#zoomPopover:not([hidden])")
            page.keyboard.press("Escape")

            right = page.get_by_role("button", name="Scroll toolbar right")
            assert right.is_visible() and right.is_enabled()
            right.click(timeout=2500)

            # Once a presentation becomes active, Background opens an
            # InkDOS-owned compact palette instead of the platform color picker.
            page.locator("#startNew").click()
            page.wait_for_function("() => document.getElementById('startState')?.hidden === true")
            assert not bg.is_disabled()
            bg.click(timeout=2500)
            palette = page.locator("#pptBackgroundPopover")
            assert palette.is_visible()
            assert bg.get_attribute("aria-expanded") == "true"

            blue = palette.locator('[data-background-color="#DBEAFE"]')
            blue.click(timeout=2500)
            assert palette.is_hidden()
            assert bg.get_attribute("aria-expanded") == "false"
            assert page.evaluate("() => globalThis.__inkdosPresentations.session.currentSlide.background.toUpperCase()") == "#DBEAFE"

            bg.click(timeout=2500)
            assert palette.is_visible()
            page.keyboard.press("Escape")
            assert palette.is_hidden()

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

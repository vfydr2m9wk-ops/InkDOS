#!/usr/bin/env python3
"""Regression: Escape closes the EPUB menu drawer, like the other workspaces."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8846
BASE = f"http://127.0.0.1:{PORT}"

def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")

def main():
    browser_name = os.environ.get("BROWSER", "chromium")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/epub/", wait_until="load")
            page.wait_for_function("() => !!document.getElementById('menuBtn')")
            for _ in range(2):
                page.click("#menuBtn")
                page.wait_for_selector("#mainMenu:not([hidden])")
                page.keyboard.press("Escape")
                page.wait_for_selector("#mainMenu", state="hidden", timeout=3000)
                assert page.locator("#backdrop").is_hidden()
                assert page.locator("#menuBtn").get_attribute("aria-expanded") == "false"
            browser.close()
        print(f"EPUB Escape closes drawer ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

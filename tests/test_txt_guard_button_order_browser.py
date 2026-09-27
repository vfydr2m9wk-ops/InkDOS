#!/usr/bin/env python3
"""Regression: the Plain Text unsaved-changes guard offers Cancel · Discard · Save in the same
order and wording as the other workspaces, with Save as the emphasized action."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8849
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
            page.goto(BASE + "/apps/txt/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2?.TxtAppDebug")
            page.click("#startNew")
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.loaded")
            page.locator("#editor").click()
            page.keyboard.type("unsaved")
            page.evaluate("() => { window.__decision = InkDOS2.TxtAppDebug.decideUnsaved() }")
            page.wait_for_selector("#discardDialog:not([hidden])")
            labels = [t.strip() for t in page.locator("#discardDialog .confirm-actions button").all_text_contents()]
            assert labels == ["Cancel", "Discard", "Save"], labels
            assert "primary" in (page.locator("#discardSave").get_attribute("class") or "")
            page.click("#discardCancel")
            assert page.evaluate("async () => await window.__decision") == "cancel"
            assert page.evaluate("() => InkDOS2.TxtAppDebug.state.session.dirty") is True
            browser.close()
        print(f"TXT guard button order ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

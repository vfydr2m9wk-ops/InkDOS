#!/usr/bin/env python3
"""Regression: the EPUB window title shows the open book's file name (name.epub — EPUB),
like the other workspaces."""
from __future__ import annotations
import importlib.util, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8848
BASE = f"http://127.0.0.1:{PORT}"
_spec = importlib.util.spec_from_file_location("epub_stability_fixture", ROOT / "tests" / "test_epub_stability_browser.py")
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)

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
        with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
            path = Path(td) / "field-notes.epub"
            _fixture.build_epub(path)
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/epub/", wait_until="load")
            page.wait_for_selector("#fileInput", state="attached")
            empty = page.title()
            page.set_input_files("#fileInput", str(path))
            page.wait_for_function("() => document.getElementById('docTitle').value === 'field-notes.epub'", timeout=15000)
            assert page.title() == "field-notes.epub — EPUB", (empty, page.title())
            browser.close()
        print(f"EPUB window title ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

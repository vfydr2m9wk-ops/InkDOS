#!/usr/bin/env python3
"""Regression: line/word counts stay correct on long texts without recounting on every keystroke.

Each keystroke split the whole text twice (lines and words) to refresh the status bar, which cost tens
of milliseconds per key on large files. Long texts now refresh the counts after a pause in typing,
using a single-pass count equivalent to the previous split-based one; short texts still update at once.
"""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8851
BASE = f"http://127.0.0.1:{PORT}"
EXPECTED = r"""() => { const t = document.getElementById('editor').value;
  const lines = t.length ? t.split('\n').length : 1, words = t.trim() ? t.trim().split(/\s+/u).filter(Boolean).length : 0;
  return `${lines} line${lines===1?'':'s'} · ${words} word${words===1?'':'s'} · ${t.length} char${t.length===1?'':'s'}`; }"""


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
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "long.txt"
            path.write_text("".join(f"Line {i} has  several\twords and　spaces\n" for i in range(6000)), encoding="utf-8")
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                page = browser.new_page(viewport={"width": 1180, "height": 820})
                page.goto(BASE + "/apps/txt/", wait_until="load")
                page.set_input_files("#fileInput", str(path))
                page.wait_for_function("() => document.getElementById('startState')?.hidden === true && document.getElementById('editor').value.length > 100000", timeout=30000)
                page.wait_for_function(f"() => document.getElementById('counts').textContent === ({EXPECTED})()", timeout=5000)
                page.click("#editor")
                page.keyboard.press("Control+End")
                # Typing must not re-split the whole text on every keystroke.
                page.evaluate("""() => { window.__bigSplits = 0; const split = String.prototype.split;
                  String.prototype.split = function (...a) { if (this.length > 100000) window.__bigSplits++; return split.apply(this, a); }; }""")
                page.keyboard.type(" extra words and more")
                splits = page.evaluate("() => window.__bigSplits")
                assert splits == 0, f"whole text was split {splits} times while typing 21 characters"
                page.keyboard.press("Enter")
                page.keyboard.type("new line")
                page.wait_for_function(f"() => document.getElementById('counts').textContent === ({EXPECTED})()", timeout=5000)
                assert "6002 lines" in page.locator("#counts").inner_text(), page.locator("#counts").inner_text()
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Plain Text large-text counts ({browser_name}): OK")


if __name__ == "__main__":
    main()

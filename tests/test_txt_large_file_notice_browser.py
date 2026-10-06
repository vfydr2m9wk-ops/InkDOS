#!/usr/bin/env python3
"""Plain Text: a large file (>= 4 MB, large-file mode) shows "Preparing … large file" before the editor lays
out the text, so the pause that follows is explained, and opening does not scroll the page to the caret.
A small file opens without that notice."""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8824
BASE = f"http://127.0.0.1:{PORT}"


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main():
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors = []
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
            big, small = Path(td) / "big.txt", Path(td) / "small.txt"
            big.write_text("\n".join(f"line {i} lorem ipsum dolor sit amet consectetur" for i in range(110000)), encoding="utf-8")
            small.write_text("hello\nworld\n", encoding="utf-8")
            assert big.stat().st_size >= 4 * 1024 * 1024
            browser = getattr(pw, os.environ.get("BROWSER", "chromium")).launch(headless=True)
            for path, expect_notice in ((big, True), (small, False)):
                page = browser.new_context(service_workers="block").new_page()
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(BASE + "/apps/txt/", wait_until="load")
                page.evaluate("""() => { window.__statuses = []; const status = document.getElementById('status');
                    new MutationObserver(() => { const t = status.textContent || ''; if (t.startsWith('Preparing')) window.__statuses.push(t); })
                      .observe(status, {subtree: true, childList: true, characterData: true}); }""")
                page.set_input_files("#fileInput", str(path))
                page.wait_for_function("() => document.getElementById('startState')?.hidden === true && document.getElementById('editor').value.length > 5", timeout=60000)
                notices = [s for s in page.evaluate("window.__statuses") if s]
                if expect_notice:
                    assert notices and path.name in notices[0] and "large file" in notices[0], notices
                else:
                    assert not notices, notices
                assert page.evaluate("document.activeElement.id") == "editor"
                assert page.evaluate("document.getElementById('editor').scrollTop") == 0
                page.context.close()
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print("Plain Text large file: notice painted before layout, no scroll on open")


if __name__ == "__main__":
    main()

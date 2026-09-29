#!/usr/bin/env python3
"""Regression: Plain Text has a Print button that prints the whole text split into A4 pages.

The workspace had no Print button; browser printing output the editor UI with only the visible
part of the text. Printing now places the full text in a print-only sheet (on beforeprint, so the
browser shortcut works too) that the browser flows into A4 pages, and removes it afterwards.
"""
from __future__ import annotations
import os, re, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8848
BASE = f"http://127.0.0.1:{PORT}"
LINES = 400
STUB = ("window.__prints=[];window.print=()=>{window.dispatchEvent(new Event('beforeprint'));"
        "const s=document.getElementById('txtPrintSheet');window.__prints.push(s?s.textContent:null);"
        "window.dispatchEvent(new Event('afterprint'))}")


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
            path = Path(td) / "print.txt"
            text = "".join(f"Line {i}: plain text print regression\n" for i in range(1, LINES + 1))
            path.write_text(text, encoding="utf-8")
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                ctx = browser.new_context(viewport={"width": 1280, "height": 860})
                ctx.add_init_script(STUB)
                page = ctx.new_page()
                page.goto(BASE + "/apps/txt/", wait_until="load")
                page.wait_for_selector("#printBtn", state="attached")
                assert page.evaluate("() => document.getElementById('printBtn').disabled"), "Print must wait for a document"
                page.set_input_files("#fileInput", str(path))
                page.wait_for_function("() => document.getElementById('startState')?.hidden === true && (document.getElementById('editor')?.value || '').includes('Line 400:')", timeout=30000)
                page.wait_for_function("() => !document.getElementById('printBtn').disabled")
                order = page.evaluate("() => { const b = document.getElementById('printBtn'); return [b.previousElementSibling?.id, b.closest('#toolbar') ? 'toolbar' : null]; }")
                assert order == ["redoBtn", "toolbar"], order
                page.click("#printBtn")
                prints = page.evaluate("() => window.__prints")
                editor = page.evaluate("() => document.getElementById('editor').value")
                assert prints == [editor] and "Line 1:" in editor and "Line 400:" in editor, prints[:1]
                assert page.evaluate("() => !document.getElementById('txtPrintSheet') && !document.documentElement.classList.contains('txt-printing')")
                if browser_name == "chromium":
                    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
                    page.emulate_media(media="print")
                    visible = page.evaluate("() => [...document.body.children].filter(e => getComputedStyle(e).display !== 'none').map(e => e.id)")
                    assert visible == ["txtPrintSheet"], f"only the print sheet may print: {visible}"
                    page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
                    data = page.pdf(prefer_css_page_size=True)
                    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
                    assert pages >= 5, f"{LINES} lines must be split across A4 pages, got {pages}"
                    assert page.evaluate("() => !document.getElementById('txtPrintSheet')")
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Plain Text print ({browser_name}): OK")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Regression: printing a presentation prints every slide, one per page, without the editor UI.

The Print button called window.print() on the editor itself, so the output was the toolbar,
the thumbnail rail and only the current slide. Printing now builds a print-only sheet with
every slide (on beforeprint, so the browser shortcut works too) and removes it afterwards.
"""
from __future__ import annotations
import os, re, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8846
BASE = f"http://127.0.0.1:{PORT}"
API = "globalThis.__inkdosPresentations"


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
            ctx = browser.new_context(viewport={"width": 1280, "height": 860})
            ctx.add_init_script("window.__prints=0;window.print=()=>{window.__prints++;window.dispatchEvent(new Event('beforeprint'));window.__sheet=document.querySelectorAll('#pptPrintSheet .ppt-print-page').length;window.dispatchEvent(new Event('afterprint'))}")
            page = ctx.new_page()
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function(f"() => !!{API}")
            page.evaluate(f"async () => {{ await {API}.newPresentation(); }}")
            page.wait_for_function(f"() => {API}.session.active && {API}.session.slides.length >= 1", timeout=15000)
            page.evaluate(f"async () => {{ while ({API}.session.slides.length < 3) await {API}.executeCommand('slide.add'); }}")
            count = page.evaluate(f"() => {API}.session.slides.length")
            assert count == 3, count
            page.wait_for_selector("#pptP1PrintBtn", state="attached", timeout=15000)
            page.evaluate("() => document.getElementById('pptP1PrintBtn').click()")
            assert page.evaluate("() => [window.__prints, window.__sheet]") == [1, count]
            assert page.evaluate("() => !document.getElementById('pptPrintSheet') && !document.documentElement.classList.contains('ppt-printing')")
            if browser_name == "chromium":
                # Real print path: beforeprint builds the sheet; only it is visible; one page per slide.
                page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
                page.emulate_media(media="print")
                visible = page.evaluate("() => [...document.body.children].filter(e => getComputedStyle(e).display !== 'none').map(e => e.id)")
                assert visible == ["pptPrintSheet"], f"only the print sheet may print: {visible}"
                page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
                data = page.pdf(prefer_css_page_size=True)
                pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
                assert pages == count, f"printed {pages} pages, expected {count}"
                assert page.evaluate("() => !document.getElementById('pptPrintSheet')")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Presentations print ({browser_name}): OK")


if __name__ == "__main__":
    main()

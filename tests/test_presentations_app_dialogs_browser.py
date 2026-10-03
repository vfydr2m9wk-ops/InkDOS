#!/usr/bin/env python3
"""Regression: Presentations theme fonts and slide comments use the app dialog, never native prompt()."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8842
BASE = f"http://127.0.0.1:{PORT}"
NATIVE_GUARD = "window.__native=[];for(const n of ['prompt','confirm','alert'])window[n]=(...a)=>{window.__native.push([n,...a]);return null};"

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
            ctx = browser.new_context(viewport={"width": 1360, "height": 900})
            ctx.add_init_script(NATIVE_GUARD)
            page = ctx.new_page()
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p2Tools")
            page.click("#startNew")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.active && !!globalThis.InkDOS2Presentations?.PptP2Package")
            page.wait_for_function("() => { const b=document.getElementById('pptP2ThemeBtn'); return b && !b.disabled }")
            slide = "globalThis.__inkdosPresentations.session.currentSlide"

            # Cancel leaves the theme untouched.
            page.click("#pptP2ThemeBtn")
            page.wait_for_selector("#inkdosAskPanel:not([hidden])")
            assert page.locator("#inkdosAskField0").input_value() == "Aptos Display"
            assert page.locator("#inkdosAskField1").input_value() == "Aptos"
            page.keyboard.press("Escape")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            assert page.evaluate(f"()=>{slide}.theme.major") == "Aptos Display"

            # Both fonts come from one in-app dialog.
            page.click("#pptP2ThemeBtn")
            page.wait_for_selector("#inkdosAskPanel:not([hidden])")
            page.fill("#inkdosAskField0", "Georgia")
            page.fill("#inkdosAskField1", "Verdana")
            page.keyboard.press("Enter")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.wait_for_function(f"()=>{slide}.theme.major==='Georgia'&&{slide}.theme.minor==='Verdana'")

            # Slide comment through the dialog; Delete/Backspace typed in the field stays in the field.
            page.wait_for_function("() => { const b=document.getElementById('pptP2CommentBtn'); return b && !b.disabled }")
            slides_before = page.evaluate("()=>globalThis.__inkdosPresentations.session.slides.length")
            page.click("#pptP2CommentBtn")
            page.wait_for_selector("#inkdosAskPanel:not([hidden])")
            # The dialog focuses its field on the next animation frame; type only once it has focus.
            page.wait_for_function("() => document.activeElement?.id === 'inkdosAskField0'")
            page.keyboard.type("Reviewx")
            page.keyboard.press("Backspace")
            page.keyboard.press("Enter")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.wait_for_function(f"()=>({slide}.comments||[]).some(c=>c.text==='Review')")
            assert page.evaluate("()=>globalThis.__inkdosPresentations.session.slides.length") == slides_before

            native = page.evaluate("()=>window.__native")
            assert native == [], native
            browser.close()
        print(f"Presentations app dialogs ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

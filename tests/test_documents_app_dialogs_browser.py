#!/usr/bin/env python3
"""Regression: Documents table and hyperlink input use the app dialog, never native prompt()."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8840
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
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            ctx.add_init_script(NATIVE_GUARD)
            page = ctx.new_page()
            page.goto(BASE + "/apps/documents/?suite=1", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!globalThis.InkDOS2Documents?.DocumentsDebug")
            page.evaluate("async()=>{await globalThis.InkDOS2Documents.DocumentsApp.newDocument();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}")
            page.locator("#pagesHost [contenteditable='true']").first.click()
            page.keyboard.type("Link me")

            def run(command):
                page.evaluate(f"()=>{{window.__pending=globalThis.InkDOS2Documents.DocumentsDebug.executeCommand('{command}')}}")
                page.wait_for_selector("#inkdosAskPanel:not([hidden])")

            # Escape cancels without mutation.
            run("insert.table")
            page.keyboard.press("Escape")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.evaluate("()=>window.__pending")
            assert page.locator("#pagesHost table").count() == 0

            # Both dimensions come from one in-app dialog.
            run("insert.table")
            assert page.locator("#inkdosAskTitle").inner_text() == "Insert table"
            page.fill("#inkdosAskField0", "2")
            page.fill("#inkdosAskField1", "4")
            page.keyboard.press("Enter")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.evaluate("()=>window.__pending")
            page.wait_for_function("()=>document.querySelector('#pagesHost table')")
            dims = page.evaluate("()=>{const t=document.querySelector('#pagesHost table');return [t.rows.length,t.rows[0].cells.length]}")
            assert dims == [2, 4], dims

            # Hyperlink insertion goes through the dialog and keeps the text selection.
            page.evaluate("""async()=>{const el=[...document.querySelectorAll('#pagesHost p')].find(p=>p.textContent.includes('Link me'));
              const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);
              await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}""")
            run("insert.hyperlink")
            assert page.locator("#inkdosAskTitle").inner_text() == "Insert hyperlink"
            page.fill("#inkdosAskField0", "https://example.com/")
            page.click("#inkdosAskConfirm")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.evaluate("()=>window.__pending")
            href = page.evaluate("()=>document.querySelector('#pagesHost a[href]')?.getAttribute('href')")
            assert href == "https://example.com/", href

            # Editing an existing link: empty value removes it.
            page.evaluate("""async()=>{const a=document.querySelector('#pagesHost a[href]');const r=document.createRange();r.selectNodeContents(a);const s=getSelection();s.removeAllRanges();s.addRange(r);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}""")
            run("insert.hyperlink")
            assert page.locator("#inkdosAskTitle").inner_text() == "Edit hyperlink"
            page.fill("#inkdosAskField0", "")
            page.keyboard.press("Enter")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.evaluate("()=>window.__pending")
            assert page.locator("#pagesHost a[href]").count() == 0
            assert "Link me" in page.locator("#pagesHost").inner_text()

            native = page.evaluate("()=>window.__native")
            assert native == [], native
            browser.close()
        print(f"Documents app dialogs ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

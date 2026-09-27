#!/usr/bin/env python3
"""Regression: Spreadsheets value input (multiply/divide, hyperlink, comment, chart) uses the
app dialog, never native prompt()."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8841
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
            page.goto(BASE + "/apps/spreadsheets/?suite=1", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1")
            page.evaluate("async()=>{const a=globalThis.__inkdosSpreadsheetsS1;await a.openController.newWorkbook();a.editor.editor.commitValue('5',0,0)}")
            page.locator('#gridStage .cell[data-ref="A1"]').click()
            cell = "()=>String(document.querySelector('#gridStage .cell[data-ref=\"A1\"]')?.innerText||'').trim()"
            page.wait_for_function(cell + "==='5'")

            def open_dialog(action):
                action()
                page.wait_for_selector("#inkdosAskPanel:not([hidden])")

            def pick_operation(kind):
                page.select_option("#operationSelect", kind)

            # Cancel (Escape) leaves the value untouched.
            open_dialog(lambda: pick_operation("multiply"))
            page.keyboard.press("Escape")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.wait_for_timeout(200)
            assert page.evaluate(cell) == "5", page.evaluate(cell)

            # Blank input is a no-op, like the cancelled native prompt was.
            open_dialog(lambda: pick_operation("multiply"))
            page.fill("#inkdosAskField0", "")
            page.keyboard.press("Enter")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.wait_for_timeout(200)
            assert page.evaluate(cell) == "5", page.evaluate(cell)

            # Confirmed factor applies.
            open_dialog(lambda: pick_operation("multiply"))
            assert page.locator("#inkdosAskField0").input_value() == "2"
            page.fill("#inkdosAskField0", "3")
            page.keyboard.press("Enter")
            page.wait_for_function(cell + "==='15'")

            cmd = "(n)=>globalThis.__inkdosSpreadsheetsS1.editor.commands.execute(n)"
            # Hyperlink through the dialog.
            open_dialog(lambda: page.click("#linkBtn"))
            page.fill("#inkdosAskField0", "https://example.com/")
            page.click("#inkdosAskConfirm")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.wait_for_function(f"()=>({cmd})('query.hyperlink')==='https://example.com/'")

            # Comment through the dialog, then removed with a blank value.
            open_dialog(lambda: page.click("#commentBtn"))
            page.fill("#inkdosAskField0", "Check this")
            page.keyboard.press("Enter")
            page.wait_for_function(f"()=>({cmd})('query.comment')==='Check this'")
            open_dialog(lambda: page.click("#commentBtn"))
            assert page.locator("#inkdosAskField0").input_value() == "Check this"
            page.fill("#inkdosAskField0", "")
            page.keyboard.press("Enter")
            page.wait_for_function(f"()=>!({cmd})('query.comment')")

            # Chart type is chosen from a list; cancel inserts nothing, confirm inserts that type.
            page.evaluate("""()=>{const e=globalThis.__inkdosSpreadsheetsS1.editor.editor;e.commitValue('Item',1,0);e.commitValue('Qty',1,1);e.commitValue('A',2,0);e.commitValue('4',2,1);e.commitValue('B',3,0);e.commitValue('6',3,1)}""")
            page.locator('#gridStage .cell[data-ref="A2"]').click()
            page.locator('#gridStage .cell[data-ref="B4"]').click(modifiers=["Shift"])
            charts = "()=>(globalThis.__inkdosSpreadsheetsS1.editor.editor.sheet().drawings||[]).filter(d=>d.kind==='chart').map(d=>d.chartType)"
            open_dialog(lambda: page.click("#chartBtn"))
            assert page.locator("#inkdosAskField0").evaluate("e=>e.tagName") == "SELECT"
            page.click("#inkdosAskCancel")
            page.wait_for_selector("#inkdosAskPanel", state="hidden")
            page.wait_for_timeout(200)
            assert page.evaluate(charts) == [], page.evaluate(charts)
            open_dialog(lambda: page.click("#chartBtn"))
            page.select_option("#inkdosAskField0", "pie")
            page.click("#inkdosAskConfirm")
            page.wait_for_function("()=>("+charts+")().length===1")
            assert page.evaluate(charts) == ["pieChart"], page.evaluate(charts)

            native = page.evaluate("()=>window.__native")
            assert native == [], native
            browser.close()
        print(f"Spreadsheets app dialogs ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

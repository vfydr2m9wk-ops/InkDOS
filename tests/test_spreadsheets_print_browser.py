#!/usr/bin/env python3
"""Regression: printing a spreadsheet prints the whole used range of the active sheet, without the editor UI.

The Print button called window.print() on the editor itself, so the output was the toolbar, the
formula bar and only the cells visible in the scroll viewport. Printing now builds a print-only
table of the sheet's used range (on beforeprint, so the browser shortcut works too) and removes
it afterwards.
"""
from __future__ import annotations
import os, re, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8847
BASE = f"http://127.0.0.1:{PORT}"
ROWS = 120
STUB = ("window.__prints=[];window.print=()=>{window.dispatchEvent(new Event('beforeprint'));"
        "const t=document.querySelector('#ssPrintSheet table');"
        "window.__prints.push(t?{rows:t.rows.length,cols:t.rows[0].cells.length,last:t.rows[t.rows.length-1].cells[1].textContent}:null);"
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
            path = Path(td) / "print.csv"
            path.write_text("Name,Value,Note\n" + "".join(f"Item {r},{r * 3},row {r}\n" for r in range(1, ROWS)), encoding="utf-8")
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                ctx = browser.new_context(viewport={"width": 1280, "height": 860})
                ctx.add_init_script(STUB)
                page = ctx.new_page()
                page.goto(BASE + "/apps/spreadsheets/", wait_until="load")
                page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1")
                page.set_input_files("#fileInput", str(path))
                page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded && document.getElementById('startState')?.hidden === true", timeout=30000)
                page.evaluate("() => document.getElementById('printBtn').click()")
                prints = page.evaluate("() => window.__prints")
                assert prints == [{"rows": ROWS, "cols": 3, "last": str((ROWS - 1) * 3)}], prints
                assert page.evaluate("() => !document.getElementById('ssPrintSheet') && !document.documentElement.classList.contains('ss-printing')")
                # Charts, images and shapes print at their anchored position over the cells.
                drawn = page.evaluate("""() => {
                  const sheet = globalThis.__inkdosSpreadsheetsS1.session.activeSheet();
                  sheet.drawings = [{kind: 'chart', title: 'Print chart', from: {r: 2, c: 1}, to: {r: 12, c: 4}, series: [{values: [1, 3, 2]}]},
                                    {kind: 'shape', text: 'Print note', from: {r: 1, c: 5}, to: {r: 3, c: 7}}];
                  window.dispatchEvent(new Event('beforeprint'));
                  const items = [...document.querySelectorAll('#ssPrintSheet .ss-print-wrap .sheet-drawing')].map(d => ({kind: d.className.replace('sheet-drawing ', ''), text: d.textContent, top: parseFloat(d.style.top), left: parseFloat(d.style.left)}));
                  window.dispatchEvent(new Event('afterprint'));
                  return {items, cleared: !document.getElementById('ssPrintSheet')};
                }""")
                kinds = sorted((i["kind"], i["text"]) for i in drawn["items"])
                assert kinds == [("chart", "Print chart"), ("shape", "Print note")], drawn
                assert drawn["cleared"] and all(i["top"] > 0 and i["left"] > 0 for i in drawn["items"]), drawn
                if browser_name == "chromium":
                    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
                    page.emulate_media(media="print")
                    visible = page.evaluate("() => [...document.body.children].filter(e => getComputedStyle(e).display !== 'none').map(e => e.id)")
                    assert visible == ["ssPrintSheet"], f"only the print sheet may print: {visible}"
                    page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
                    data = page.pdf(prefer_css_page_size=True)
                    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
                    assert pages >= 3, f"{ROWS} rows must continue across pages, got {pages} page(s)"
                    assert page.evaluate("() => !document.getElementById('ssPrintSheet')")
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Spreadsheets print ({browser_name}): OK")


if __name__ == "__main__":
    main()

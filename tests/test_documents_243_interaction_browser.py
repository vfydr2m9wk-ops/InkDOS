#!/usr/bin/env python3
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8783
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
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, os.environ.get("BROWSER", "chromium")).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/documents/?suite=1", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!globalThis.InkDOS2Documents?.DocumentsDebug")
            page.evaluate("async()=>{await globalThis.InkDOS2Documents.DocumentsApp.newDocument();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}")

            # One global transient surface: opening Page/Layout after Document Tools closes Document Tools.
            page.click("#d2P1Btn")
            assert page.locator("#d2Panel").is_visible()
            page.click("#d1LayoutBtn")
            assert page.locator("#d1LayoutPanel").is_visible()
            assert page.locator("#d2Panel").is_hidden(), "Document Tools must close when Page Layout opens"
            page.click("#d1LayoutClose")

            # Cancelled table insertion is a true no-op: no table, no dirty state, no history entry.
            table_cancel = page.evaluate("""async()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              const dbg=globalThis.InkDOS2Documents.DocumentsDebug;
              app.session.markSaved(app.session.revision);
              const before={
                tables:document.querySelectorAll('#pagesHost table').length,
                dirty:app.session.dirty,
              };
              const editor=globalThis.InkDOS2Documents.DocumentsApp;
              const historyBefore=document.getElementById('undoBtn')?.disabled;
              const oldPrompt=globalThis.prompt;
              globalThis.prompt=()=>null;
              try{await dbg.executeCommand('insert.table')}finally{globalThis.prompt=oldPrompt}
              await new Promise(r=>setTimeout(r,350));
              return {
                before,
                afterTables:document.querySelectorAll('#pagesHost table').length,
                dirty:app.session.dirty,
                undoDisabledBefore:historyBefore,
                undoDisabledAfter:document.getElementById('undoBtn')?.disabled,
              };
            }""")
            assert table_cancel["afterTables"] == table_cancel["before"]["tables"], table_cancel
            assert table_cancel["dirty"] is False, table_cancel
            assert table_cancel["undoDisabledAfter"] == table_cancel["undoDisabledBefore"], table_cancel

            bold = page.locator('.fmt-btn[data-cmd="bold"]')
            assert bold.get_attribute("aria-pressed") in ("false", "true"), "Bold must expose aria-pressed"

            def exercise(direction: str):
                return page.evaluate("""async(direction)=>{
                  const app=globalThis.InkDOS2Documents.DocumentsApp;
                  app.session.markSaved(app.session.revision);
                  await app.newDocument();
                  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                  const p=document.querySelector('#pagesHost .page-content p');
                  p.innerHTML='<strong>alpha beta gamma</strong>';
                  const text=p.querySelector('strong').firstChild;
                  const start=6,end=10;
                  const sel=getSelection();sel.removeAllRanges();
                  if(direction==='reverse' && sel.setBaseAndExtent){
                    sel.setBaseAndExtent(text,end,text,start);
                  }else{
                    const r=document.createRange();r.setStart(text,start);r.setEnd(text,end);sel.addRange(r);
                  }
                  document.dispatchEvent(new Event('selectionchange'));
                  await new Promise(r=>requestAnimationFrame(r));
                  return {
                    selected:String(sel),
                    anchor:sel.anchorOffset,
                    focus:sel.focusOffset,
                    pressed:document.querySelector('.fmt-btn[data-cmd="bold"]')?.getAttribute('aria-pressed')
                  };
                }""", direction)

            forward = exercise("forward")
            assert forward["selected"] == "beta", forward
            assert forward["pressed"] == "true", forward
            page.click('.fmt-btn[data-cmd="bold"]')
            forward_html = page.locator("#pagesHost .page-content p").first.inner_html()
            assert "<strong>beta</strong>" not in forward_html.lower(), forward_html

            reverse = exercise("reverse")
            assert reverse["selected"] == "beta", reverse
            assert reverse["anchor"] > reverse["focus"], reverse
            assert reverse["pressed"] == "true", reverse
            page.click('.fmt-btn[data-cmd="bold"]')
            reverse_html = page.locator("#pagesHost .page-content p").first.inner_html()
            assert "<strong>beta</strong>" not in reverse_html.lower(), reverse_html

            browser.close()
        print("Documents 2.4.3 interaction regression test passed.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

if __name__ == "__main__":
    main()

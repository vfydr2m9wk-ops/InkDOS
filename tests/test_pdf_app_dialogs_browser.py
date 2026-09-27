#!/usr/bin/env python3
"""Regression: PDF delete page, print-with-unsaved-annotations and unauthorized replace use the
app confirmation dialog, never native confirm()."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8844
BASE = f"http://127.0.0.1:{PORT}"
NATIVE_GUARD = "window.__native=[];for(const n of ['prompt','confirm','alert'])window[n]=(...a)=>{window.__native.push([n,...a]);return false};"
DBG = "globalThis.InkDOS2PdfP4.PdfStabilityDebug"
FIXTURE = r"""async (n) => {
  const pdf = await PDFLib.PDFDocument.create();
  for (let i = 0; i < n; i++) pdf.addPage([612, 792]).drawText(`Dialog fixture page ${i + 1}`, {x: 48, y: 730, size: 20});
  window.__fixture = new Uint8Array(await pdf.save());
}"""

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
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function(f"() => !!{DBG}")
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument", timeout=15000)
            page.evaluate(FIXTURE, 3)
            assert page.evaluate(f"async()=>await {DBG}.fileOpen.openFile(new File([window.__fixture],'dialogs.pdf',{{type:'application/pdf'}}))") is True
            page.wait_for_function(f"() => {DBG}.layout.pageCount === 3")
            page.click("#editModeBtn")
            page.wait_for_function(f"() => {DBG}.editingReady")
            page.evaluate(f"() => {DBG}.layout.goToPage(2)")
            page.wait_for_function(f"() => {DBG}.layout.currentPage === 2")

            # Delete page: cancel keeps the page, confirm deletes it.
            page.click("#pageToolsBtn"); page.click("#pageDeleteBtn")
            page.wait_for_selector("#pdfConfirmDialog")
            assert page.locator("#pdfConfirmTitle").inner_text() == "Delete page?"
            page.keyboard.press("Escape")
            page.wait_for_selector("#pdfConfirmDialog", state="detached")
            page.wait_for_timeout(300)
            assert page.evaluate(f"() => {DBG}.layout.pageCount") == 3
            if page.locator("#pageDeleteBtn").is_hidden():
                page.click("#pageToolsBtn")
            page.click("#pageDeleteBtn")
            page.click("#pdfConfirmDialog [data-choice=\"confirm\"]")
            page.wait_for_function(f"() => {DBG}.layout.pageCount === 2", timeout=15000)
            assert page.evaluate(f"() => {DBG}.session.dirty") is True

            # Print with unsaved changes asks in-app; cancel prints nothing.
            page.evaluate(f"() => {{ window.__printPending = {DBG}.registry.execute('reader.print') }}")
            page.wait_for_selector("#pdfConfirmDialog")
            assert page.locator("#pdfConfirmTitle").inner_text() == "Print without annotations?"
            frames_before = page.evaluate("() => document.querySelectorAll('iframe').length")
            page.click("#pdfConfirmDialog [data-choice=\"cancel\"]")
            page.evaluate("() => window.__printPending")
            page.wait_for_timeout(300)
            assert page.evaluate("() => document.querySelectorAll('iframe').length") == frames_before

            # An unauthorized replace of a dirty PDF asks in-app; cancel keeps the current PDF.
            page.evaluate(f"() => {{ window.__openPending = {DBG}.fileOpen.openFile(new File([window.__fixture],'other.pdf',{{type:'application/pdf'}})) }}")
            page.wait_for_selector("#pdfConfirmDialog")
            assert page.locator("#pdfConfirmTitle").inner_text() == "Unsaved changes"
            page.click("#pdfConfirmDialog [data-choice=\"cancel\"]")
            assert page.evaluate("async () => await window.__openPending") is False
            assert page.evaluate(f"() => {DBG}.layout.pageCount") == 2
            assert page.evaluate(f"() => {DBG}.session.dirty") is True

            native = page.evaluate("()=>window.__native")
            assert native == [], native
            browser.close()
        print(f"PDF app dialogs ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

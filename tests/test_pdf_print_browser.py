#!/usr/bin/env python3
"""Regression: the PDF Print button prints every page of the open document, without the app UI.

Printing used to load the PDF bytes into a hidden blob: frame, which the page CSP (frame-src 'none')
blocks, so nothing printed. Print now renders each page into a print-only sheet in the page itself.
"""
from __future__ import annotations
import os, re, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8845
BASE = f"http://127.0.0.1:{PORT}"
DBG = "globalThis.InkDOS2PdfP4.PdfStabilityDebug"
PAGES = 4
STUB = ("window.__prints=[];window.__csp=[];window.print=()=>{window.__prints.push(document.querySelectorAll('#pdfPrintSheet img').length)};"
        "document.addEventListener('securitypolicyviolation',e=>window.__csp.push(e.violatedDirective+' '+e.blockedURI));")
FIXTURE = r"""async (n) => {
  const pdf = await PDFLib.PDFDocument.create();
  for (let i = 0; i < n; i++) { const p = pdf.addPage(i === 1 ? [792, 612] : [612, 792]); p.drawText(`Print fixture page ${i + 1}`, {x: 48, y: p.getHeight() - 60, size: 20}); }
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
            ctx.add_init_script(STUB)
            page = ctx.new_page()
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function(f"() => !!{DBG}")
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument", timeout=15000)
            page.evaluate(FIXTURE, PAGES)
            assert page.evaluate(f"async()=>await {DBG}.fileOpen.openFile(new File([window.__fixture],'print.pdf',{{type:'application/pdf'}}))") is True
            page.wait_for_function(f"() => {DBG}.layout.pageCount === {PAGES}")
            page.wait_for_selector("#pdfPrintBtn:not([disabled])", timeout=15000)
            page.click("#pdfPrintBtn")
            page.wait_for_function("() => window.__prints.length === 1", timeout=30000)
            state = page.evaluate("() => ({prints: window.__prints, csp: window.__csp, frames: document.querySelectorAll('iframe').length, classes: [...document.querySelectorAll('#pdfPrintSheet img')].map(i => i.className), loaded: [...document.querySelectorAll('#pdfPrintSheet img')].every(i => i.complete && i.naturalWidth > 0)})")
            assert state["prints"] == [PAGES], state
            assert state["csp"] == [] and state["frames"] == 0, state
            assert state["classes"] == ["portrait", "landscape", "portrait", "portrait"] and state["loaded"], state
            if browser_name == "chromium":
                page.emulate_media(media="print")
                visible = page.evaluate("() => [...document.body.children].filter(e => getComputedStyle(e).display !== 'none').map(e => e.id)")
                assert visible == ["pdfPrintSheet"], f"only the print sheet may print: {visible}"
                data = page.pdf(format="Letter")
                count = len(re.findall(rb"/Type\s*/Page[^s]", data))
                assert count == PAGES, f"printed {count} pages, expected {PAGES}"
                page.emulate_media(media="screen")
            page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
            assert page.evaluate("() => !document.getElementById('pdfPrintSheet') && !document.documentElement.classList.contains('pdf-printing')")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"PDF print ({browser_name}): OK")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Regression: the PDF viewer draws only the pages near the viewport at full resolution.

Every stop drew the eight buffered pages around the current page at full device resolution, which was
the main CPU cost of reading and scrolling on high-density screens. Pages next to the viewport are now
drawn first at full resolution; the rest are drawn later at 1x and redrawn sharp when they come near.
"""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8852
BASE = f"http://127.0.0.1:{PORT}"
DBG = "globalThis.InkDOS2PdfP4.PdfStabilityDebug"
FIXTURE = r"""async (n) => {
  const pdf = await PDFLib.PDFDocument.create();
  for (let i = 0; i < n; i++) pdf.addPage([612, 792]).drawText(`Budget page ${i + 1}`, {x: 48, y: 730, size: 24});
  window.__fixture = new Uint8Array(await pdf.save());
}"""
DENSITY = """(pages) => { const L = globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout, out = {};
  for (const n of pages) { const c = L.getShell(n)?.querySelector('canvas.pdf-page-canvas'); out[n] = c ? Math.round(10 * c.width / parseFloat(c.style.width)) / 10 : 0; }
  return out; }"""


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
            ctx = browser.new_context(viewport={"width": 1100, "height": 800}, device_scale_factor=2)
            page = ctx.new_page()
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function(f"() => !!{DBG}")
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument", timeout=15000)
            page.evaluate(FIXTURE, 24)
            assert page.evaluate(f"async()=>await {DBG}.fileOpen.openFile(new File([window.__fixture],'budget.pdf',{{type:'application/pdf'}}))") is True
            page.wait_for_function(f"() => {DBG}.layout.pageCount === 24")
            page.evaluate(f"() => {DBG}.layout.goToPage(12)")
            # Near pages sharp (2x); the rest of the buffer drawn later at 1x.
            page.wait_for_function(f"() => {{ const d = ({DENSITY})([11,12,13,14,9,10,15,16]); return [11,12,13,14].every(n => d[n] === 2) && [9,10,15,16].every(n => d[n] > 0); }}", timeout=20000)
            density = page.evaluate(DENSITY, [9, 10, 11, 12, 13, 14, 15, 16])
            assert all(density[str(n)] == 2 for n in (11, 12, 13, 14)), density
            assert all(density[str(n)] == 1 for n in (9, 10, 15, 16)), f"buffered pages away from the viewport must be drawn at 1x: {density}"
            # A buffered page is redrawn sharp once the reader reaches it.
            page.evaluate(f"() => {DBG}.layout.goToPage(16)")
            page.wait_for_function(f"() => ({DENSITY})([16])[16] === 2", timeout=20000)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"PDF render budget ({browser_name}): OK")


if __name__ == "__main__":
    main()

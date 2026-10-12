#!/usr/bin/env python3
"""Regression: a highlight added in the PDF workspace keeps the text under it as dark as a PDF reader shows it.

The highlight marks were drawn with mix-blend-mode:multiply inside a layer with its own z-index, which isolates the
blend: the yellow was then painted over the text and black letters turned brown-yellow. The marks now sit in a layer
that multiplies with the page itself."""
from __future__ import annotations

import io
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8834
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument")
            page.evaluate(r"""() => {window.confirm=()=>true;new MutationObserver(()=>document.querySelector('#pdfConfirmDialog [data-choice="confirm"]')?.click()).observe(document.body,{childList:true})}""")
            page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create(),
              f=await pdf.embedFont(PDFLib.StandardFonts.HelveticaBold),p=pdf.addPage([612,792]);
              p.drawText('HHHHHHHHHHHHHHHHHHHHHH',{x:72,y:700,size:30,font:f});
              return d.fileOpen.openFile(new File([await pdf.save()],'highlight-blend.pdf',{type:'application/pdf'}))}""")
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 1")
            page.click("#editModeBtn")
            page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'annotate'")
            page.wait_for_function("() => document.querySelectorAll('.pdf-select-text-layer span').length >= 1")
            # the text layer is rebuilt once after the mode switch: wait until it holds still, then select and mark in one go
            page.wait_for_timeout(800)
            page.wait_for_function("() => document.querySelectorAll('.pdf-select-text-layer span').length >= 1")
            result = page.evaluate("""async () => {const s=document.querySelector('.pdf-select-text-layer span'),b=s.getBoundingClientRect(),r=document.createRange();
              r.selectNodeContents(s);const sel=getSelection();sel.removeAllRanges();sel.addRange(r);
              const added=await globalThis.InkDOS2PdfP4.PdfStabilityDebug.extensions.addMark('highlight');
              return {added,box:{x:b.left,y:b.top,width:b.width,height:b.height}}}""")
            assert result["added"] is not False, "highlight was not added"
            box = result["box"]
            page.click("#selectToolBtn")
            page.evaluate("() => getSelection().removeAllRanges()")
            page.wait_for_function("() => !!document.querySelector('.pdf-extension-mark.highlight')")
            page.wait_for_timeout(300)
            shot = page.screenshot(clip={"x": box["x"], "y": box["y"] + box["height"] * 0.2,
                                         "width": box["width"], "height": box["height"] * 0.6})
            pixels = list(Image.open(io.BytesIO(shot)).convert("RGB").getdata())
            darkest = min(pixels, key=sum)
            # letters stay near black under the highlight (they were about (117, 99, 35) with the isolated blend)
            assert sum(darkest) < 90, ("text under the highlight is washed out", darkest)
            # the band between the letters is still visibly yellow
            yellow = sum(1 for r, g, b in pixels if r > 230 and g > 200 and b < 215) / len(pixels)
            assert yellow > 0.25, ("highlight colour missing", yellow)
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"PDF highlight keeps the text under it dark ({browser_name}): OK")


if __name__ == "__main__":
    main()

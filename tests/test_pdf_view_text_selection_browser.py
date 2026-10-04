#!/usr/bin/env python3
"""PDF workspace: text is selectable and copyable while reading, with editing off.

The text layer must exist without loading the editing tools, stay aligned with the painted text
after zooming, copy to the clipboard, and keep working after editing was switched on and off.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8805
BASE = f"http://127.0.0.1:{PORT}"
LINE = "The quick brown fox jumps over the lazy dog"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


SPAN_RATIO = """() => {const shell=document.querySelector('.pdf-page-shell').getBoundingClientRect(),
  span=[...document.querySelectorAll('.pdf-select-text-layer span')].find(s=>s.textContent.startsWith('The quick'));
  return span ? span.getBoundingClientRect().width/shell.width : 0}"""


def drag_select(page) -> str:
    span = page.locator(".pdf-select-text-layer span", has_text="The quick").first
    box = span.bounding_box()
    page.mouse.move(box["x"] + 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] - 2, box["y"] + box["height"] / 2, steps=8)
    page.mouse.up()
    return page.evaluate("() => getSelection().toString()")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            if browser_name == "chromium":
                context.grant_permissions(["clipboard-read", "clipboard-write"], origin=BASE)
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument")
            page.evaluate("""async(line)=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create(),f=await pdf.embedFont(PDFLib.StandardFonts.Helvetica);
              for(let i=1;i<=2;i++){const p=pdf.addPage([612,792]);p.drawText(line,{x:72,y:700,size:22,font:f});p.drawText('Page '+i+' second line',{x:72,y:650,size:22,font:f})}
              return d.fileOpen.openFile(new File([await pdf.save()],'view-text.pdf',{type:'application/pdf'}))}""", LINE)

            # reading mode, editing tools never opened
            page.wait_for_function("() => document.querySelectorAll('.pdf-select-text-layer[data-view-text] span').length >= 2", timeout=15000)
            state = page.evaluate("() => ({mode:document.documentElement.dataset.pdfMode,editing:globalThis.InkDOS2PdfP4.PdfStabilityDebug.editingActive})")
            assert state["mode"] == "view" and state["editing"] is False, state
            assert 0.6 < page.evaluate(SPAN_RATIO) < 0.8, page.evaluate(SPAN_RATIO)
            assert drag_select(page).strip().startswith("The quick brown fox"), page.evaluate("() => getSelection().toString()")
            if browser_name == "chromium":
                page.keyboard.press("Control+C")
                copied = page.evaluate("() => navigator.clipboard.readText()")
                assert copied.strip().startswith("The quick brown fox"), copied

            # zooming keeps the text aligned with the painted page
            page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.setView({mode:'manual',manualScale:1.5})")
            page.wait_for_timeout(800)
            assert 0.6 < page.evaluate(SPAN_RATIO) < 0.8, page.evaluate(SPAN_RATIO)

            # editing on, then off again: still selectable and aligned after another zoom
            page.click("#editModeBtn")
            page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'annotate'")
            page.wait_for_function("() => !document.querySelector('.pdf-select-text-layer[data-view-text]') && document.querySelectorAll('.pdf-select-text-layer span').length >= 2", timeout=15000)
            page.click("#editModeBtn")
            page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'view'")
            page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.setView({mode:'manual',manualScale:1})")
            page.wait_for_timeout(800)
            assert 0.6 < page.evaluate(SPAN_RATIO) < 0.8, page.evaluate(SPAN_RATIO)
            assert page.evaluate("() => document.querySelectorAll('.pdf-page-shell').length") == page.evaluate(
                "() => [...document.querySelectorAll('.pdf-page-shell')].filter(s=>s.querySelectorAll('.pdf-select-text-layer').length<=1).length")
            page.evaluate("() => getSelection().removeAllRanges()")
            assert drag_select(page).strip().startswith("The quick brown fox")
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"PDF view-mode text selection and copy passed on {browser_name}.")


if __name__ == "__main__":
    main()

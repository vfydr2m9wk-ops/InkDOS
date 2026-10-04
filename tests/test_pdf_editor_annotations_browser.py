#!/usr/bin/env python3
"""PDF workspace: pen, free text, highlight and underline are drawn, aligned and saved.

Guards the PDF.js 6 integration: the editor layer must have the page size (--total-scale-factor),
text-layer spans must match the painted text, ink strokes (draw-layer SVG) must be visible, the
PDF.js floating editor toolbar must not intercept clicks, and saveDocument() must write Ink,
FreeText, Highlight and Underline annotations (the last two through the patched worker).
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8803
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
    errors: list[str] = []
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900}, accept_downloads=True)
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument")
            page.evaluate(r"""() => {for(const[t,k]of[[window,'showSaveFilePicker'],[navigator,'share'],[navigator,'canShare']]){try{Object.defineProperty(t,k,{value:undefined,configurable:true})}catch(_){}}window.confirm=()=>true;new MutationObserver(()=>document.querySelector('#pdfConfirmDialog [data-choice="confirm"]')?.click()).observe(document.body,{childList:true});}""")
            page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create(),f=await pdf.embedFont(PDFLib.StandardFonts.Helvetica),p=pdf.addPage([612,792]);
              p.drawText('The quick brown fox jumps over the lazy dog',{x:72,y:700,size:22,font:f});p.drawText('Second line of selectable text for review',{x:72,y:650,size:22,font:f});
              return d.fileOpen.openFile(new File([await pdf.save()],'editor-annotations.pdf',{type:'application/pdf'}))}""")
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 1")
            page.click("#editModeBtn")
            page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'annotate'")
            page.wait_for_function("() => !!document.querySelector('.annotationEditorLayer')")
            page.wait_for_function("() => document.querySelectorAll('.pdf-select-text-layer span').length >= 2")

            # text spans cover the painted text (Helvetica 22pt line ≈ 0.71 of the width)
            geometry = page.evaluate("""() => {const shell=document.querySelector('.pdf-page-shell').getBoundingClientRect(),span=document.querySelector('.pdf-select-text-layer span').getBoundingClientRect();return {span:span.width/shell.width}}""")
            assert 0.6 < geometry["span"] < 0.8, geometry

            box = page.locator(".pdf-page-shell").first.bounding_box()
            x = lambda f: box["x"] + box["width"] * f
            y = lambda f: box["y"] + box["height"] * f
            page.click("#penToolBtn")
            page.wait_for_function("() => document.querySelector('.annotationEditorLayer').classList.contains('inkEditing')")
            editor = page.evaluate("""() => {const shell=document.querySelector('.pdf-page-shell').getBoundingClientRect(),ed=document.querySelector('.annotationEditorLayer').getBoundingClientRect();return [ed.width/shell.width,ed.height/shell.height]}""")
            assert abs(editor[0] - 1) < 0.01 and abs(editor[1] - 1) < 0.01, editor
            page.mouse.move(x(0.2), y(0.3)); page.mouse.down()
            for i in range(1, 15):
                page.mouse.move(x(0.2 + i * 0.02), y(0.3 + (i % 3) * 0.01))
            page.mouse.up()
            page.click("#textToolBtn")
            page.wait_for_function("() => document.querySelector('.annotationEditorLayer').classList.contains('freetextEditing')")
            page.mouse.click(x(0.3), y(0.4))
            page.wait_for_function("() => document.activeElement?.closest?.('.freeTextEditor')")
            page.keyboard.type("Free text note")
            page.click("#selectToolBtn")
            for index, kind in ((0, "highlight"), (1, "underline")):
                page.evaluate("""([i,kind]) => {const s=document.querySelectorAll('.pdf-select-text-layer span')[i],r=document.createRange();r.selectNodeContents(s);const sel=getSelection();sel.removeAllRanges();sel.addRange(r);
                  return globalThis.InkDOS2PdfP4.PdfStabilityDebug.extensions.addMark(kind)}""", [index, kind])
            page.click("#selectToolBtn")

            visual = page.evaluate("""() => {const svg=document.querySelector('.pdf-page-shell > svg.draw'),r=svg?.getBoundingClientRect();
              return {svg:!!svg&&getComputedStyle(svg).position==='absolute'&&r.width>0,toolbars:[...document.querySelectorAll('.editToolbar')].filter(t=>t.getBoundingClientRect().width>0).length}}""")
            assert visual == {"svg": True, "toolbars": 0}, visual

            saved = Path(td) / "editor-annotations-saved.pdf"
            with page.expect_download(timeout=30000) as info:
                page.click("#saveToolbarBtn")
            info.value.save_as(str(saved))
            page.locator("#fileInput").set_input_files(str(saved))
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.fileName === 'editor-annotations-saved.pdf'", timeout=15000)
            annotations = page.evaluate("""async()=>{const p=await globalThis.InkDOS2PdfP4.PdfStabilityDebug.fileOpen.pdfDocument.getPage(1);
              return (await p.getAnnotations({intent:'display'})).map(a=>[a.subtype,a.contentsObj?.str||''])}""")
            subtypes = sorted(a[0] for a in annotations)
            assert subtypes == ["FreeText", "Highlight", "Ink", "Underline"], annotations
            assert ["FreeText", "Free text note"] in annotations, annotations
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"PDF editor annotations (pen, free text, highlight, underline) round-trip passed on {browser_name}.")


if __name__ == "__main__":
    main()

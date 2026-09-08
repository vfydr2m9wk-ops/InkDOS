#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8778
BASE = f"http://127.0.0.1:{PORT}"

def wait_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")

def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            opened = page.evaluate(r"""async () => {const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug;const pdf=await PDFLib.PDFDocument.create();const p=pdf.addPage([612,792]);p.drawText('Comment command fixture',{x:48,y:730,size:20});const bytes=new Uint8Array(await pdf.save());return await d.fileOpen.openFile(new File([bytes],'comment-fixture.pdf',{type:'application/pdf'}));}""")
            assert opened is True
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 1")
            page.wait_for_function("() => document.querySelector('.pdf-page-shell')")
            page.click('[data-pdf-mode="annotate"]')
            page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'annotate'")
            commands=page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.registry.inspect().commands")
            for command in ("pdf.comment.open","pdf.comment.cancel","pdf.comment.save"): assert command in commands
            opened_dialog=page.evaluate(r"""async () => {const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug;d.extensions.pending={pageNumber:1,rects:[{x:.20,y:.20,w:.002,h:.002}],text:''};return await d.registry.execute('pdf.comment.open');}""")
            assert opened_dialog is True
            assert page.locator("#commentDialog").is_visible()
            assert page.locator("#cancelComment").get_attribute("data-command") == "pdf.comment.cancel"
            submit=page.locator('#commentDialog button[type="submit"]')
            assert submit.get_attribute("data-command") == "pdf.comment.save"
            assert page.locator("#commentBackdrop").get_attribute("data-command") == "pdf.comment.cancel"
            page.locator("#commentText").fill("Registry-backed comment")
            submit.click()
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.extensions.inspect().count === 1")
            assert page.locator("#commentDialog").is_hidden()
            page.wait_for_function("() => document.querySelectorAll('.pdf-extension-comment').length === 1")
            pin=page.locator(".pdf-extension-comment").first
            assert pin.get_attribute("data-command") == "pdf.comment.open"
            annotation_id=pin.get_attribute("data-annotation-id")
            assert annotation_id
            pin.click()
            assert page.locator("#commentDialog").is_visible()
            assert page.locator("#commentDialogTitle").inner_text() == "Edit comment"
            assert page.locator("#commentText").input_value() == "Registry-backed comment"
            page.locator("#cancelComment").click()
            assert page.locator("#commentDialog").is_hidden()
            page.evaluate("() => document.querySelector('.pdf-extension-comment').remove()")
            reopened=page.evaluate("async (id) => {const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug;return await d.registry.execute('pdf.comment.open',{currentTarget:{dataset:{annotationId:id}},stopPropagation(){}});}",annotation_id)
            assert reopened is True
            assert page.locator("#commentDialog").is_visible()
            page.locator("#commentBackdrop").click(position={"x":2,"y":2})
            assert page.locator("#commentDialog").is_hidden()
            if errors: raise AssertionError({"browser":browser_name,"errors":errors})
            browser.close()
        print(f"PDF comment command regression passed on {browser_name}.")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__": main()

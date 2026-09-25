#!/usr/bin/env python3
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8792
BASE = f"http://127.0.0.1:{PORT}"


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("PDF test server did not start")


def main():
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 810})
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug?.fileOpen")
            # pdf-lib is not a product startup dependency. Load the checked-in bundle
            # explicitly for this synthetic regression fixture.
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument", timeout=15000)

            opened = page.evaluate("""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug; const pdf=await PDFLib.PDFDocument.create(); const p=pdf.addPage([612,792]); p.drawText('InkDOS PDF hitbox audit',{x:48,y:730,size:20}); const bytes=new Uint8Array(await pdf.save()); return await d.fileOpen.openFile(new File([bytes],'hitbox.pdf',{type:'application/pdf'}));}""")
            assert opened is True
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 1")

            nav = page.locator("#navPanelBtn")
            edit = page.locator("#editModeBtn")
            organize = page.locator("#pageToolsBtn")
            assert nav.is_visible() and nav.is_enabled()
            assert edit.is_visible() and edit.is_enabled()
            assert not organize.is_visible()
            edit.click(timeout=2500)
            page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'annotate'")
            assert organize.is_visible() and organize.is_enabled()
            assert organize.locator(".tool-label").count() == 0

            nav.click(timeout=2500)
            page.wait_for_selector("#navigationPanel:not([hidden])")
            page.locator("#closeNavigation").click(timeout=2500)

            organize.click(timeout=2500)
            page.wait_for_selector("#pageToolsPanel:not([hidden])")
            page.locator("#closePageTools").click(timeout=2500)

            assert not errors, errors
            browser.close()
        print("PDF navigation/page-tools hitbox regression passed.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

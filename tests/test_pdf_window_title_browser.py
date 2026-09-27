#!/usr/bin/env python3
"""Regression: the PDF window title follows the open file and dirty state (file • — PDF),
like the other workspaces, and returns to the empty title when nothing is open."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8847
BASE = f"http://127.0.0.1:{PORT}"
DBG = "globalThis.InkDOS2PdfP4.PdfStabilityDebug"

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
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function(f"() => !!{DBG}")
            empty = page.title()
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument", timeout=15000)
            opened = page.evaluate(f"""async()=>{{const pdf=await PDFLib.PDFDocument.create();pdf.addPage([612,792]);
              const bytes=new Uint8Array(await pdf.save());return await {DBG}.fileOpen.openFile(new File([bytes],'report.pdf',{{type:'application/pdf'}}))}}""")
            assert opened is True
            page.wait_for_function("() => document.title === 'report.pdf — PDF'", timeout=10000)
            # Same sequence the annotation commands use: mark the session dirty, then sync the chrome.
            page.evaluate(f"() => {{ {DBG}.session.markDirty(); {DBG}.extensions.chrome.dirty(); }}")
            assert page.title() == "report.pdf • — PDF", page.title()
            assert empty and "—" in empty, empty
            browser.close()
        print(f"PDF window title ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

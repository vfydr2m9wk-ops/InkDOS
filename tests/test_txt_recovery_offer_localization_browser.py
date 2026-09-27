#!/usr/bin/env python3
"""Regression: the Plain Text recovery offer follows the workspace language; the file name,
date and count stay as user content."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8853
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

def ready(page):
    page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")

def main():
    browser_name = os.environ.get("BROWSER", "chromium")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            ctx = browser.new_context()
            ctx.add_init_script("try{localStorage.setItem('inkdos2:txt:language','pt-BR')}catch(_){}")
            page = ctx.new_page()
            page.goto(BASE + "/apps/txt/", wait_until="load"); ready(page)
            page.click("#startNew"); page.wait_for_function("() => InkDOS2.TxtAppDebug.state.loaded")
            page.click("#editor"); page.keyboard.type("LOCALIZED-DRAFT")
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.session.checkpointRevision===InkDOS2.TxtAppDebug.state.session.revision", timeout=5000)
            page.reload(wait_until="load"); ready(page)
            page.wait_for_selector(".txt-recovery-offer", state="visible", timeout=5000)
            page.wait_for_function("() => document.documentElement.lang === 'pt-BR'")
            page.wait_for_function("() => document.getElementById('recoveryAccept').textContent === 'Recuperar'", timeout=5000)
            offer = page.evaluate("""() => { const o = document.querySelector('.txt-recovery-offer');
              return {lead: o.querySelector('strong').textContent, detail: o.querySelector('.txt-recovery-detail').textContent,
                      accept: document.getElementById('recoveryAccept').textContent, discard: document.getElementById('recoveryDiscard').textContent} }""")
            assert offer["lead"] == "Há texto não salvo que pode ser recuperado.", offer
            assert offer["discard"] == "Descartar", offer
            assert offer["detail"].startswith("Untitled.txt · ") and offer["detail"].endswith("caracteres"), offer
            page.click("#recoveryAccept")
            page.wait_for_function("() => document.getElementById('editor').value.includes('LOCALIZED-DRAFT')")
            browser.close()
        print(f"TXT recovery offer localization ({browser_name}): OK")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

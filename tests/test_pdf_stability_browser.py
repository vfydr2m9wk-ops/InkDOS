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
PORT = 8776
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
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            browser_type = getattr(pw, browser_name)
            browser = browser_type.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")

            opened = page.evaluate(r"""async () => {
              const d = globalThis.InkDOS2PdfP4.PdfStabilityDebug;
              const pdf = await PDFLib.PDFDocument.create();
              for (let i = 0; i < 5; i++) {
                const p = pdf.addPage([612, 792]);
                p.drawText(`Stability fixture page ${i + 1}`, {x: 48, y: 730, size: 20});
              }
              const bytes = new Uint8Array(await pdf.save());
              const file = new File([bytes], 'stability-fixture.pdf', {type:'application/pdf'});
              return await d.fileOpen.openFile(file);
            }""")
            assert opened is True
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 5")
            page.wait_for_function("() => document.querySelectorAll('.pdf-page-shell').length >= 1")

            page.click("#navPanelBtn")
            assert "active" in (page.locator("#outlineTab").get_attribute("class") or "").split()
            assert "active" not in (page.locator("#pagesPane").get_attribute("class") or "").split()
            page.click("#pagesTab")
            assert "active" in (page.locator("#pagesTab").get_attribute("class") or "").split()
            page.click("#closeNavigation")
            page.click("#navPanelBtn")
            assert "active" in (page.locator("#outlineTab").get_attribute("class") or "").split()
            page.click("#closeNavigation")
            page.click('[data-pdf-mode="annotate"]')
            page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'annotate'")

            page.evaluate(r"""() => {
              const d = globalThis.InkDOS2PdfP4.PdfStabilityDebug;
              window.__inkdosHistoryFlag = 0;
              d.editor.addCommand({
                cmd: () => { window.__inkdosHistoryFlag = 1; },
                undo: () => { window.__inkdosHistoryFlag = 0; },
                mustExec: true,
              });
            }""")
            page.wait_for_function("() => !document.getElementById('undoBtn').disabled")
            assert page.evaluate("() => window.__inkdosHistoryFlag") == 1

            page.evaluate("() => document.getElementById('editbar').append(document.getElementById('undoBtn'))")
            page.locator("#undoBtn").scroll_into_view_if_needed()
            page.click("#undoBtn")
            page.wait_for_function("() => window.__inkdosHistoryFlag === 0")
            page.wait_for_function("() => !document.getElementById('redoBtn').disabled")
            page.locator("#redoBtn").scroll_into_view_if_needed()
            page.click("#redoBtn")
            page.wait_for_function("() => window.__inkdosHistoryFlag === 1")

            page.locator("#undoBtn").scroll_into_view_if_needed()
            page.click("#undoBtn")
            page.wait_for_function("() => window.__inkdosHistoryFlag === 0")
            page.evaluate("() => document.getElementById('redoBtn').remove()")
            redone = page.evaluate("async () => await globalThis.InkDOS2PdfP4.PdfStabilityDebug.registry.execute('history.redo')")
            assert redone is not False
            page.wait_for_function("() => window.__inkdosHistoryFlag === 1")

            delete_probe = page.evaluate(r"""() => {
              const d = globalThis.InkDOS2PdfP4.PdfStabilityDebug;
              window.__inkdosDeleteCalled = 0;
              d.editor.deleteSelected = () => { window.__inkdosDeleteCalled += 1; };
              d.editor.eventBus.dispatch('editingstateschanged', {
                source: d.editor,
                details: {hasSelectedEditor:true}
              });
              return !document.getElementById('deleteAnnotationBtn').disabled;
            }""")
            assert delete_probe is True
            page.locator("#deleteAnnotationBtn").scroll_into_view_if_needed()
            page.click("#deleteAnnotationBtn")
            assert page.evaluate("() => window.__inkdosDeleteCalled") == 1

            viewport = page.locator("#contentViewport")
            viewport.hover()
            page.evaluate("() => { const v=document.getElementById('contentViewport'); v.scrollTop=0; }")
            before = page.evaluate("() => document.getElementById('contentViewport').scrollTop")
            page.mouse.wheel(0, 650)
            page.wait_for_timeout(250)
            after = page.evaluate("() => document.getElementById('contentViewport').scrollTop")
            assert after > before, (browser_name, before, after)

            page.select_option("#zoomSelect", "125")
            page.wait_for_timeout(40)
            zoom_before = page.evaluate("() => document.getElementById('contentViewport').scrollTop")
            page.mouse.wheel(0, 550)
            page.wait_for_timeout(600)
            zoom_after = page.evaluate("() => document.getElementById('contentViewport').scrollTop")
            assert zoom_after > zoom_before, (browser_name, zoom_before, zoom_after)

            page.click("#navPanelBtn")
            page.click("#closeNavigation")
            page.click("#pageToolsBtn")
            page.click("#closePageTools")
            panel_before = page.evaluate("() => document.getElementById('contentViewport').scrollTop")
            page.mouse.wheel(0, 450)
            page.wait_for_timeout(250)
            panel_after = page.evaluate("() => document.getElementById('contentViewport').scrollTop")
            assert panel_after > panel_before, (browser_name, panel_before, panel_after)

            page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.goToPage(2)")
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.currentPage === 2")
            page.click("#pageToolsBtn")
            page.once("dialog", lambda dialog: dialog.accept())
            page.click("#pageDeleteBtn")
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 4", timeout=15000)
            page.click("#closePageTools")

            final = page.evaluate(r"""() => {
              const d = globalThis.InkDOS2PdfP4.PdfStabilityDebug;
              return {
                pageCount: d.layout.pageCount,
                nav: d.navigation.inspect(),
                commands: d.registry.inspect(),
                scroll: d.layout.inspect(),
              };
            }""")
            assert final["pageCount"] == 4
            assert final["nav"]["tab"] == "outline"
            assert "history.undo" in final["commands"]["commands"]
            assert "annotation.delete" in final["commands"]["commands"]
            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PDF stability browser regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

if __name__ == "__main__":
    main()

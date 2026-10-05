#!/usr/bin/env python3
"""PDF workspace (web edition): Page tools → Make searchable (OCR).

Scanned pages get an invisible, searchable text layer through the page-tools mutation path (the
document becomes dirty, a copy must be saved). A noisy scan is recognized through the cleaned
reading. Pages that already have text are left alone, a signed PDF is refused (a text layer would
invalidate the signature), the OCR engine is fetched only on first use, and the action is hidden in
the desktop app.
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
PORT = 8806
BASE = f"http://127.0.0.1:{PORT}"

MAKE_PDF = r"""async ({noise, withText, signed}) => {
  const draw = (W, H, rot) => { const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, W, H); g.save(); if (rot) { g.translate(W / 2, H / 2); g.rotate(rot * Math.PI / 180); g.translate(-W / 2, -H / 2); }
    g.fillStyle = '#000'; g.font = `${W * 0.045}px serif`; g.fillText('Contrato de prestação de serviços', W * 0.1, H * 0.17); g.fillText('Cláusula terceira sobre a rescisão', W * 0.1, H * 0.24); g.restore(); return c; };
  let c = draw(1240, 1754, 0);
  if (noise) { // a poor scan: half resolution, blurred, slightly skewed, grainy
    const big = draw(1240, 1754, 1.2), small = document.createElement('canvas'); small.width = 620; small.height = 877;
    const g = small.getContext('2d'); g.filter = 'blur(1.1px)'; g.drawImage(big, 0, 0, 620, 877); g.filter = 'none';
    const d = g.getImageData(0, 0, 620, 877); let seed = 11; const r = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < d.data.length; i += 4) { const n = (r() - .5) * noise; for (let k = 0; k < 3; k++) d.data[i + k] = Math.max(0, Math.min(255, d.data[i + k] + n)); }
    g.putImageData(d, 0, 0); c = small; }
  const png = Uint8Array.from(atob(c.toDataURL('image/png').split(',')[1]), ch => ch.charCodeAt(0));
  const pdf = await PDFLib.PDFDocument.create(), img = await pdf.embedPng(png), p = pdf.addPage([595, 842]);
  p.drawImage(img, { x: 0, y: 0, width: 595, height: 842 });
  if (withText) p.drawText('This page already carries a real text layer for search.', { x: 40, y: 40, size: 12 });
  let bytes = await pdf.save();
  if (signed) bytes = new Uint8Array([...bytes, ...new TextEncoder().encode('\n99 0 obj\n<< /Type /Sig /ByteRange [0 10 20 30] /Contents <00> >>\nendobj\n')]);
  return Array.from(bytes);
}"""

OPEN = r"""async (bytes) => globalThis.InkDOS2PdfP4.PdfStabilityDebug.fileOpen.openFile(new File([new Uint8Array(bytes)], 'scan.pdf', {type: 'application/pdf'}))"""
TEXT = r"""async () => { const doc = globalThis.InkDOS2PdfP4.PdfStabilityDebug.fileOpen.pdfDocument, p = await doc.getPage(1);
  return (await p.getTextContent()).items.map(i => i.str).join(' '); }"""


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def boot(context, errors):
    page = context.new_page()
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
    page.goto(BASE + "/apps/pdf/", wait_until="load")
    page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
    page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
    page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument")
    page.evaluate("""() => { window.confirm = () => true; new MutationObserver(() => document.querySelector('#pdfConfirmDialog [data-choice="confirm"]')?.click()).observe(document.body, {childList: true}); }""")
    return page


def open_pdf(page, **kind):
    assert page.evaluate(OPEN, page.evaluate(MAKE_PDF, {"noise": 0, "withText": False, "signed": False, **kind})) is True
    page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 1")


def run_ocr(page) -> str:
    if page.evaluate("() => document.documentElement.dataset.pdfMode") != "annotate":
        page.click("#editModeBtn")
        page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.editingReady")
    if page.locator("#pageToolsPanel").is_hidden():
        page.click("#pageToolsBtn")
    page.evaluate("() => { document.getElementById('pageToolsStatus').textContent = ''; }")
    page.click("#pageOcrBtn")
    page.wait_for_function("""() => /Text recognized|nothing to recognize|digitally signed|failed/i.test(document.getElementById('pageToolsStatus')?.textContent || '')""", timeout=180_000)
    return page.inner_text("#pageToolsStatus")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 900}, service_workers="block")
            page = boot(context, errors)
            requests: list[str] = []
            page.on("request", lambda r: requests.append(r.url))

            # clean scan: recognized, document dirty, OCR engine fetched only now
            open_pdf(page)
            assert not any("/vendor/tesseract/" in u for u in requests), "OCR engine loaded before use"
            status = run_ocr(page)
            assert "Text recognized on 1 page" in status, status
            text = page.evaluate(TEXT).lower()
            assert "contrato" in text and "rescis" in text, text
            assert page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.dirty") is True
            assert any("/vendor/tesseract/lang/por.traineddata.gz" in u for u in requests)

            # running again: the page now has text
            assert "nothing to recognize" in run_ocr(page)

            # noisy scan: only the cleaned reading recognizes it
            open_pdf(page, noise=90)
            status = run_ocr(page)
            assert "Text recognized on 1 page" in status, status
            text = page.evaluate(TEXT).lower()
            assert "contrato" in text and "rescis" in text, text

            # page that already has a text layer
            open_pdf(page, withText=True)
            assert "nothing to recognize" in run_ocr(page)

            # signed PDF: refused, unchanged
            open_pdf(page, signed=True)
            assert "digitally signed" in run_ocr(page)
            assert page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.dirty") is False
            assert not errors, errors
            page.close()

            # desktop app: the action is not offered
            desktop = browser.new_context(viewport={"width": 1280, "height": 900}, service_workers="block")
            desktop.add_init_script("window.InkDOSDesktop = Object.freeze({});")
            page = boot(desktop, [])
            open_pdf(page)
            page.click("#editModeBtn")
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.editingReady")
            page.click("#pageToolsBtn")
            assert page.locator("#pageOcrRow").is_hidden()
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"PDF OCR (web edition) passed on {browser_name}.")


if __name__ == "__main__":
    main()

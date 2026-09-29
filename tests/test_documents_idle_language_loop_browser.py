#!/usr/bin/env python3
"""Regression: an open document must stay idle, and a language change must still relabel the UI.

The shared localization runtime announces 'inkdos:language' after every DOM insertion. Documents
rebuilt its navigation and status bar on every announcement, which inserted nodes, which triggered
another announcement: a requestAnimationFrame loop at 60 fps (about a third of a CPU core) for as
long as a document was open. Documents now rebuilds only when the language actually changes.
"""
from __future__ import annotations
import io, os, socket, subprocess, sys, tempfile, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8849
BASE = f"http://127.0.0.1:{PORT}"
RAF_COUNTER = "(()=>{const ra=requestAnimationFrame;window.__raf=0;window.requestAnimationFrame=function(f){window.__raf++;return ra.call(this,f)}})()"


def docx_bytes() -> bytes:
    paragraphs = "".join(f'<w:p><w:r><w:t>Idle regression paragraph {i} with a few words.</w:t></w:r></w:p>' for i in range(60))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{paragraphs}</w:body></w:document>')
    return out.getvalue()


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
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "idle.docx"
            path.write_bytes(docx_bytes())
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                ctx = browser.new_context(viewport={"width": 1180, "height": 820}, service_workers="block")
                ctx.add_init_script(RAF_COUNTER)
                page = ctx.new_page()
                page.goto(BASE + "/apps/documents/", wait_until="load")
                page.set_input_files("#fileInput", str(path))
                page.wait_for_function("() => globalThis.InkDOS2Documents?.DocumentsApp?.session?.kind === 'docx' && !!document.querySelector('.page-content')", timeout=30000)
                page.wait_for_timeout(1500)
                page.evaluate("() => { window.__raf = 0; }")
                page.wait_for_timeout(2000)
                frames = page.evaluate("() => window.__raf")
                assert frames < 10, f"open document is not idle: {frames} animation frames in 2 s"
                # A real language change still relabels the status bar.
                before = page.evaluate("() => document.getElementById('pageStatus').textContent")
                assert before.startswith("Page 1 of"), before
                page.evaluate("async () => { await InkDOSLocalization.setLanguage('pt-BR'); }")
                page.wait_for_function("() => document.getElementById('pageStatus').textContent.startsWith('Página 1 de')", timeout=10000)
                page.wait_for_timeout(500)
                page.evaluate("() => { window.__raf = 0; }")
                page.wait_for_timeout(2000)
                frames = page.evaluate("() => window.__raf")
                assert frames < 10, f"document is not idle after a language change: {frames} animation frames in 2 s"
                page.evaluate("async () => { await InkDOSLocalization.setLanguage('en'); }")
                page.wait_for_function("() => document.getElementById('pageStatus').textContent.startsWith('Page 1 of')", timeout=10000)
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Documents idle/language loop ({browser_name}): OK")


if __name__ == "__main__":
    main()

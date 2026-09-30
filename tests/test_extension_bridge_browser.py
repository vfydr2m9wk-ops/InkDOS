#!/usr/bin/env python3
"""The InkDOS browser extension (extension/, loaded unpacked, no build step) opens linked files in the right workspace.

Loads the extension into Chromium, serves the InkDOS web apps under their public URL and a local "cloud" server,
then checks that:
- the extension routes every format exactly like Home;
- Google Drive file pages and Google Docs/Sheets/Slides map to their direct downloads;
- a link without an extension (name from Content-Disposition, like Drive downloads) opens in its workspace with its content;
- a PDF opened in a tab goes to the PDF workspace instead of the browser's viewer, and can still be opened in the browser;
- a document download opens in its workspace instead of being saved; text files and a disabled option download as usual;
- the toolbar button opens InkDOS.
"""
from __future__ import annotations
import http.server, io, os, socketserver, ssl, subprocess, tempfile, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "extension"
SITE = "https://vfydr2m9wk-ops.github.io/InkDOS/"
CSV = b"Name,Value\nExtension launch,42\n"


def pdf_bytes() -> bytes:
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    stream = b"BT /F1 24 Tf 72 700 Td (Extension PDF) Tj ET"
    out = io.BytesIO(); out.write(b"%PDF-1.4\n"); offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(out.tell())
        if body is None:
            out.write(f"{i} 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream\nendobj\n")
        else:
            out.write(f"{i} 0 obj\n{body}\nendobj\n".encode())
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


PDF = pdf_bytes()
PDF_READY = "() => globalThis.InkDOS2PdfP4?.PdfStabilityDebug?.layout?.pageCount === 1 && !!document.querySelector('canvas')"
SHEET_READY = "() => !!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded && document.getElementById('startState')?.hidden === true"


class Cloud(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/download"):
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", "attachment; filename*=UTF-8''Relat%C3%B3rio%20extens%C3%A3o.csv")
            self.end_headers()
            self.wfile.write(CSV)
        elif self.path.startswith("/papers/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.end_headers()
            try:
                self.wfile.write(PDF)
            except (BrokenPipeError, ConnectionResetError):
                pass  # the extension redirects the tab as soon as it sees the PDF headers
        elif self.path.startswith("/notes.txt"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Disposition", "attachment; filename=notes.txt")
            self.end_headers()
            self.wfile.write(b"plain notes\n")
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<!doctype html><title>cloud</title>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


class Site(http.server.SimpleHTTPRequestHandler):
    """The repository served under /InkDOS/, as on GitHub Pages."""
    def translate_path(self, path):
        path = path.split("?")[0].split("#")[0]
        rel = path[len("/InkDOS/"):] if path.startswith("/InkDOS/") else ""
        return str(ROOT / rel)

    def log_message(self, *args):
        pass


def https_server(workdir):
    cert, key = Path(workdir) / "cert.pem", Path(workdir) / "key.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-subj", "/CN=vfydr2m9wk-ops.github.io",
                    "-keyout", str(key), "-out", str(cert)], check=True, capture_output=True)
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Site)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(cert), str(key))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main():
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Cloud)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    cloud = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with tempfile.TemporaryDirectory() as profile, tempfile.TemporaryDirectory() as certs, sync_playwright() as pw:
            site = https_server(certs)
            # The public InkDOS host resolves to the local copy of the repository (the extension only acts on that host).
            ctx = pw.chromium.launch_persistent_context(profile, channel="chromium", headless=True, service_workers="block", ignore_https_errors=True,
                                                        args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}", "--no-proxy-server", "--ignore-certificate-errors",
                                                              f"--host-resolver-rules=MAP vfydr2m9wk-ops.github.io 127.0.0.1:{site.server_address[1]}"])
            worker = ctx.service_workers[0] if ctx.service_workers else ctx.wait_for_event("serviceworker", timeout=15000)

            # Same routing as Home for every declared format.
            home = ctx.new_page()
            home.goto(SITE + "index.html")
            home_routes = home.evaluate("() => globalThis.InkDOSHomeLaunch.routes.map(r => [r.app, r.ext])")
            ext_routes = worker.evaluate("() => ROUTES.map(r => [r.app, r.ext])")
            assert ext_routes == home_routes, (ext_routes, home_routes)
            home.close()

            # Drive / Docs pages become direct downloads.
            mapped = worker.evaluate("""() => [
              downloadUrl('https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view?usp=sharing'),
              downloadUrl('https://drive.google.com/open?id=1AbCdEfGhIjKlMnOp'),
              downloadUrl('https://docs.google.com/document/d/1AbCdEfGhIjKlMnOp/edit'),
              downloadUrl('https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOp/edit#gid=0'),
              downloadUrl('https://docs.google.com/presentation/d/1AbCdEfGhIjKlMnOp/edit'),
              downloadUrl('https://example.com/report.pdf')]""")
            assert mapped == [
                "https://drive.usercontent.google.com/download?id=1AbCdEfGhIjKlMnOp&export=download&confirm=t",
                "https://drive.usercontent.google.com/download?id=1AbCdEfGhIjKlMnOp&export=download&confirm=t",
                "https://docs.google.com/document/d/1AbCdEfGhIjKlMnOp/export?format=docx",
                "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOp/export?format=xlsx",
                "https://docs.google.com/presentation/d/1AbCdEfGhIjKlMnOp/export/pptx",
                "https://example.com/report.pdf",
            ], mapped

            # A cloud download (name only in Content-Disposition) opens in Spreadsheets with its content.
            with ctx.expect_page(timeout=15000) as opened:
                worker.evaluate("url => openLink(url)", cloud + "/download?id=42")
            page = opened.value
            page.wait_for_load_state()
            assert page.url.startswith(SITE + "apps/spreadsheets/index.html"), page.url
            page.wait_for_function(SHEET_READY, timeout=30000)
            state = page.evaluate("() => ({name: globalThis.__inkdosSpreadsheetsS1.session.book.fileName, a2: globalThis.__inkdosSpreadsheetsS1.session.activeSheet().cells.get('A2')?.v, hash: location.hash})")
            assert state == {"name": "Relatório extensão.csv", "a2": "Extension launch", "hash": ""}, state
            page.close()

            # A PDF opened in a tab goes to the InkDOS PDF workspace (same tab) instead of the browser's viewer.
            page = ctx.new_page()
            page.goto(cloud + "/")
            page.goto(cloud + "/papers/review.pdf")
            page.wait_for_url(SITE + "apps/pdf/index.html*", timeout=15000)
            page.wait_for_function(PDF_READY, timeout=30000)
            assert page.evaluate("() => location.hash") == ""
            page.go_back()
            page.wait_for_url(cloud + "/", timeout=15000)
            # A PDF that cannot be fetched explains why and offers the browser's viewer; that choice skips the redirect once.
            page.goto(worker.evaluate("() => chrome.runtime.getURL('open.html')") + "#" + cloud + "/missing.pdf")
            page.wait_for_function("() => document.getElementById('title').textContent.includes('could not open')", timeout=15000)
            assert "404" in page.inner_text("#detail") and page.is_visible("#browser")
            worker.evaluate("url => allowOnce(url)", cloud + "/papers/review.pdf")
            page.goto(cloud + "/papers/review.pdf")
            page.wait_for_timeout(1000)
            assert page.url == cloud + "/papers/review.pdf", page.url
            page.close()

            # A document download opens in its workspace instead of being saved.
            page = ctx.new_page()
            page.goto(cloud + "/")
            with ctx.expect_page(timeout=15000) as opened:
                page.evaluate("url => { const a = document.createElement('a'); a.href = url; document.body.append(a); a.click(); }", cloud + "/download?id=7")
            sheet = opened.value
            sheet.wait_for_url(SITE + "apps/spreadsheets/index.html*", timeout=15000)
            sheet.wait_for_function(SHEET_READY, timeout=30000)
            sheet.close()
            downloads = worker.evaluate("async () => (await chrome.downloads.search({})).map(d => d.filename.split(/[\\\\/]/).pop())")
            assert downloads == [], downloads
            # Text files, and documents with the option turned off, download as usual.
            with page.expect_download(timeout=15000) as dl:
                page.evaluate("url => { const a = document.createElement('a'); a.href = url; document.body.append(a); a.click(); }", cloud + "/notes.txt")
            assert dl.value.suggested_filename == "notes.txt", dl.value.suggested_filename
            worker.evaluate("() => chrome.storage.local.set({downloads: false, pdfViewer: false})")
            with page.expect_download(timeout=15000) as dl:
                page.evaluate("url => { const a = document.createElement('a'); a.href = url; document.body.append(a); a.click(); }", cloud + "/download?id=8")
            assert dl.value.suggested_filename.endswith(".csv"), dl.value.suggested_filename
            page.wait_for_timeout(500)
            rules = worker.evaluate("async () => (await chrome.declarativeNetRequest.getDynamicRules()).length")
            assert rules == 0, rules
            page.close()
            assert len([p for p in ctx.pages if p.url.startswith(SITE)]) == 0, [p.url for p in ctx.pages]

            # The toolbar button opens InkDOS.
            with ctx.expect_page(timeout=15000) as opened:
                worker.evaluate("() => chrome.tabs.create({url: INKDOS})")
            opened.value.wait_for_url(SITE, timeout=15000)
            ctx.close()
            site.shutdown()
    finally:
        server.shutdown()
    print("InkDOS extension bridge (chromium): OK")


if __name__ == "__main__":
    main()

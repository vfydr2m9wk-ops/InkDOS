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
PORT = 8831
BASE = f"http://127.0.0.1:{PORT}"


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            launch_args = {"headless": True}
            chromium_path = os.environ.get("CHROMIUM_PATH")
            if chromium_path:
                launch_args["executable_path"] = chromium_path
            browser = pw.chromium.launch(**launch_args)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/documents/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DrawingLayout")
            result = page.evaluate(r"""() => {
              const D = globalThis.InkDOS2Documents.DrawingLayout;
              const enc = new TextEncoder();
              const files = new Map();
              const png = Uint8Array.from(atob(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
              ), c => c.charCodeAt(0));

              const header = `<?xml version="1.0"?>
                <w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
                  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                  xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                  <w:p><w:r><w:drawing><wp:anchor behindDoc="0">
                    <wp:positionH relativeFrom="page"><wp:align>center</wp:align></wp:positionH>
                    <wp:positionV relativeFrom="page"><wp:posOffset>95250</wp:posOffset></wp:positionV>
                    <wp:extent cx="952500" cy="476250"/>
                    <a:graphic><a:graphicData><pic:pic><pic:blipFill><a:blip r:embed="rIdImage"/></pic:blipFill></pic:pic></a:graphicData></a:graphic>
                  </wp:anchor></w:drawing></w:r></w:p>
                </w:hdr>`;
              const footer = `<?xml version="1.0"?>
                <w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
                  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                  xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                  <w:p><w:r><w:drawing><wp:anchor behindDoc="0">
                    <wp:positionH relativeFrom="margin"><wp:align>center</wp:align></wp:positionH>
                    <wp:positionV relativeFrom="margin"><wp:posOffset>0</wp:posOffset></wp:positionV>
                    <wp:extent cx="762000" cy="381000"/>
                    <a:graphic><a:graphicData><pic:pic><pic:blipFill><a:blip r:embed="rIdImage"/></pic:blipFill></pic:pic></a:graphicData></a:graphic>
                  </wp:anchor></w:drawing></w:r></w:p>
                </w:ftr>`;
              const rels = `<?xml version="1.0"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                  <Relationship Id="rIdImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.png"/>
                </Relationships>`;

              files.set('word/header1.xml', enc.encode(header));
              files.set('word/footer1.xml', enc.encode(footer));
              files.set('word/_rels/header1.xml.rels', enc.encode(rels));
              files.set('word/_rels/footer1.xml.rels', enc.encode(rels));
              files.set('word/media/logo.png', png);

              const sect = new DOMParser().parseFromString(`
                <w:sectPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
                  <w:headerReference w:type="default" r:id="rIdHeader"/>
                  <w:footerReference w:type="default" r:id="rIdFooter"/>
                </w:sectPr>`, 'application/xml').documentElement;

              const relMap = {rIdHeader:'header1.xml', rIdFooter:'footer1.xml'};
              const urls = {};
              const h = D.partSpec(sect, 'header', relMap, 'word', files, urls);
              const f = D.partSpec(sect, 'footer', relMap, 'word', files, urls);
              const spec = {
                widthPx: 816, heightPx: 1056,
                marginLeftPx: 96, marginRightPx: 96,
                marginTopPx: 96, marginBottomPx: 96,
                headerArtwork: h.artwork, footerArtwork: f.artwork
              };
              const host = document.createElement('div');
              host.className = 'page';
              document.body.appendChild(host);
              D.appendPageArtwork(host, spec);
              const rendered = [...host.querySelectorAll('.page-watermark')].map(img => ({
                left: parseFloat(img.style.left),
                top: parseFloat(img.style.top),
                width: parseFloat(img.style.width),
                height: parseFloat(img.style.height)
              }));
              return {
                headerCount:h.artwork.length,
                footerCount:f.artwork.length,
                header:h.artwork[0] || null,
                footer:f.artwork[0] || null,
                rendered
              };
            }""")
            browser.close()

        assert result["headerCount"] == 1, result
        assert result["footerCount"] == 1, result
        assert result["header"]["partKind"] == "header", result
        assert result["footer"]["partKind"] == "footer", result
        assert result["header"]["horizontalAlign"] == "center", result
        assert result["footer"]["horizontalAlign"] == "center", result
        assert result["header"]["widthPx"] > 0 and result["header"]["heightPx"] > 0, result
        assert result["footer"]["widthPx"] > 0 and result["footer"]["heightPx"] > 0, result
        assert len(result["rendered"]) == 2, result
        assert 300 < result["rendered"][0]["left"] < 500, result
        assert result["rendered"][1]["top"] > 800, result
        print("Documents DrawingML header/footer artwork browser regression: OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

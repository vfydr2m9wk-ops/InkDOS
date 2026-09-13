#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8795
BASE = f'http://127.0.0.1:{PORT}'


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local EPUB embedded-SVG test server did not start')


def build_svg_epub(path: Path) -> None:
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
    opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:inkdos:embedded-svg</dc:identifier>
    <dc:title>Embedded SVG Book</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml" properties="svg"/>
  </manifest>
  <spine><itemref idref="chapter"/></spine>
</package>'''
    xhtml = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:svg="http://www.w3.org/2000/svg">
<head><title>SVG Chapter</title></head>
<body>
  <svg:svg viewBox="0 0 600 200" role="img" aria-labelledby="chart-title">
    <svg:title id="chart-title">Quarterly trend</svg:title>
    <svg:desc>Accessible chart description</svg:desc>
    <svg:text x="20" y="80">Embedded SVG chapter text</svg:text>
  </svg:svg>
</body>
</html>'''
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        zf.writestr('META-INF/container.xml', container, compress_type=zipfile.ZIP_STORED)
        zf.writestr('EPUB/package.opf', opf, compress_type=zipfile.ZIP_STORED)
        zf.writestr('EPUB/chapter.xhtml', xhtml, compress_type=zipfile.ZIP_STORED)


def main() -> None:
    browser_name = os.environ.get('BROWSER', 'chromium').strip().lower()
    if browser_name not in {'chromium', 'firefox', 'webkit'}:
        raise RuntimeError(f'Unsupported BROWSER={browser_name}')

    server = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td:
            epub_path = Path(td) / 'embedded-svg.epub'
            build_svg_epub(epub_path)
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                page = browser.new_page(viewport={'width': 1200, 'height': 800})
                page.goto(BASE + '/apps/epub/', wait_until='load')
                page.wait_for_function('() => !!globalThis.__InkEpubR4')
                page.set_input_files('#fileInput', str(epub_path))
                page.wait_for_function("""() => {
                    const s=globalThis.__InkEpubR4.state();
                    return !!s.book || /readable projected content|content/i.test(document.body.innerText);
                }""")
                state = page.evaluate("""() => {
                    const s=globalThis.__InkEpubR4.state();
                    const blocks=s.book?.chapters?.[0]?.blocks || [];
                    return {
                        title:s.book?.title || null,
                        chapters:s.book?.chapters?.length || 0,
                        texts:blocks.flatMap(block => (block.runs || []))
                            .filter(run => run.kind === 'text')
                            .map(run => run.text.replace(/\\s+/g,' ').trim())
                            .filter(Boolean),
                    };
                }""")
                assert state['title'] == 'Embedded SVG Book', (browser_name, state)
                assert state['chapters'] == 1, (browser_name, state)
                joined = ' | '.join(state['texts'])
                assert 'Embedded SVG chapter text' in joined, (browser_name, state)
                assert 'Quarterly trend' in joined or 'Accessible chart description' in joined, (browser_name, state)
                browser.close()
        print(f'EPUB embedded-SVG stability ({browser_name}): OK')
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=3)


if __name__ == '__main__':
    main()

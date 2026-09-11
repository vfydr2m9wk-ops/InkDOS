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
PORT = 8793
BASE = f'http://127.0.0.1:{PORT}'


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local EPUB SVG test server did not start')


def build_svg_epub(path: Path) -> None:
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
    opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:inkdos:svg-spine</dc:identifier>
    <dc:title>SVG Spine Book</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="page" href="page.svg" media-type="image/svg+xml"/>
  </manifest>
  <spine><itemref idref="page"/></spine>
</package>'''
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800">
  <text id="title" x="40" y="80">SVG Chapter</text>
  <text id="body" x="40" y="140">Readable fixed-layout text.</text>
</svg>'''
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        zf.writestr('META-INF/container.xml', container, compress_type=zipfile.ZIP_STORED)
        zf.writestr('EPUB/package.opf', opf, compress_type=zipfile.ZIP_STORED)
        zf.writestr('EPUB/page.svg', svg, compress_type=zipfile.ZIP_STORED)


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
            epub_path = Path(td) / 'svg-spine.epub'
            build_svg_epub(epub_path)
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                page = browser.new_page(viewport={'width': 1200, 'height': 800})
                page.goto(BASE + '/apps/epub/', wait_until='load')
                page.wait_for_function('() => !!globalThis.__InkEpubR4')
                page.set_input_files('#fileInput', str(epub_path))
                page.wait_for_function("""() => {
                    const s=globalThis.__InkEpubR4.state();
                    return !!s.book || /SVG|spine|content/i.test(document.body.innerText);
                }""")
                state = page.evaluate("""() => {
                    const s=globalThis.__InkEpubR4.state();
                    const chapter=s.book?.chapters?.[0];
                    return {
                        title:s.book && s.book.title,
                        chapters:s.book && s.book.chapters.length,
                        spineMediaType:s.book?.spine?.[0]?.mediaType || null,
                        blockSources:(chapter?.blocks || []).map(block=>block.sourceId),
                        text:document.querySelector('#readerSurface')?.innerText || '',
                    };
                }""")
                assert state['title'] == 'SVG Spine Book', (browser_name, state)
                assert state['chapters'] == 1, (browser_name, state)
                assert state['spineMediaType'] == 'image/svg+xml', (browser_name, state)
                assert state['blockSources'] == ['title', 'body'], (browser_name, state)
                assert 'SVG Chapter' in state['text'], (browser_name, state)
                assert 'Readable fixed-layout text.' in state['text'], (browser_name, state)
                browser.close()
        print(f'EPUB SVG spine stability ({browser_name}): OK')
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

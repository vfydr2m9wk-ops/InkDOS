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
PORT = 8783
BASE = f'http://127.0.0.1:{PORT}'


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local EPUB test server did not start')


def build_epub(path: Path) -> None:
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
    opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:inkdos:epub-regression</dc:identifier>
    <dc:title>Regression Book</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="c1"/><itemref idref="c2"/></spine>
</package>'''
    nav = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head><body>
<nav epub:type="toc"><ol>
<li><a href="ch1.xhtml#one">Chapter One</a></li>
<li><a href="ch2.xhtml#two">Chapter Two</a></li>
</ol></nav>
</body></html>'''
    ch1 = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>One</title></head><body>
<h1 id="one">Chapter One</h1><p id="p1">Alpha beta gamma. First chapter regression text.</p>
</body></html>'''
    ch2 = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Two</title></head><body>
<h1 id="two">Chapter Two</h1><p id="p2">Delta epsilon zeta. Second chapter regression text.</p>
</body></html>'''

    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        for name, data in (
            ('META-INF/container.xml', container),
            ('OEBPS/content.opf', opf),
            ('OEBPS/nav.xhtml', nav),
            ('OEBPS/ch1.xhtml', ch1),
            ('OEBPS/ch2.xhtml', ch2),
        ):
            zf.writestr(name, data, compress_type=zipfile.ZIP_STORED)


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
    errors: list[str] = []
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td:
            epub_path = Path(td) / 'regression.epub'
            build_epub(epub_path)
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                page = browser.new_page(viewport={'width': 1360, 'height': 900})
                page.on('pageerror', lambda exc: errors.append(f'pageerror: {exc}'))
                page.on('console', lambda msg: errors.append(f'console.error: {msg.text}') if msg.type == 'error' else None)
                page.goto(BASE + '/apps/epub/', wait_until='load')
                page.wait_for_function('() => !!globalThis.__InkEpubR4')
                page.wait_for_selector('.inkdos-toolbar-rail')

                assert page.locator('#emptyState').is_visible()
                assert page.locator('#saveBtn').is_disabled()
                assert page.locator('#shareBtn').is_disabled()
                rail = page.evaluate("""() => ({
                    rail:document.querySelectorAll('.inkdos-toolbar-rail').length,
                    toolbarInside:!!document.querySelector('.inkdos-toolbar-rail > #toolbar'),
                    arrows:document.querySelectorAll('.inkdos-toolbar-arrow').length,
                })""")
                assert rail == {'rail': 1, 'toolbarInside': True, 'arrows': 2}, rail

                page.set_input_files('#fileInput', str(epub_path))
                page.wait_for_function("""() => {
                    const s=globalThis.__InkEpubR4.state();
                    return s.book && s.book.chapters.length===2 && document.querySelectorAll('#readerSurface .reader-chapter').length===2;
                }""")
                opened = page.evaluate("""() => {
                    const s=globalThis.__InkEpubR4.state();
                    return {
                        fileName:s.fileName,
                        title:s.book && s.book.title,
                        chapters:s.book && s.book.chapters.length,
                        toc:s.book && s.book.toc.length,
                        exportReady:s.exportReady,
                        empty:document.getElementById('emptyState').hidden,
                    };
                }""")
                assert opened == {
                    'fileName': 'regression.epub',
                    'title': 'Regression Book',
                    'chapters': 2,
                    'toc': 2,
                    'exportReady': True,
                    'empty': True,
                }, opened
                assert not page.locator('#saveBtn').is_disabled()
                assert not page.locator('#shareBtn').is_disabled()
                text = page.locator('#readerSurface').inner_text()
                assert 'Chapter One' in text and 'Chapter Two' in text and 'Alpha beta gamma' in text, text

                # Semantic reading flow survives removal of its toolbar controls.
                page.click('#scrollBtn')
                page.wait_for_function("() => globalThis.__InkEpubR4.state().flow === 'scroll'")
                page.evaluate("() => { document.getElementById('pagesBtn').remove(); document.getElementById('scrollBtn').remove(); globalThis.__InkEpubR4.setFlow('pages'); }")
                page.wait_for_function("() => globalThis.__InkEpubR4.state().flow === 'pages'")

                # Typography is a reader operation, not a dependency on the appearance button.
                page.evaluate("() => { document.getElementById('appearanceBtn').remove(); globalThis.__InkEpubR4.setFont(20); globalThis.__InkEpubR4.setFontStyle('sans'); }")
                page.wait_for_function("() => { const s=globalThis.__InkEpubR4.state(); return s.fontPx===20 && s.fontStyle==='sans'; }")

                # Navigation remains available after removing the corresponding toolbar control.
                navigation_probe = page.evaluate("""() => {
                    document.getElementById('tocBtn').remove();
                    return globalThis.__InkEpubR4.goPath('OEBPS/ch2.xhtml','two');
                }""")
                assert navigation_probe is True
                page.wait_for_function("() => globalThis.__InkEpubR4.state().locator && globalThis.__InkEpubR4.state().locator.chapter === 2")
                locator = page.evaluate("() => globalThis.__InkEpubR4.state().locator")
                assert locator['path'] == 'OEBPS/ch2.xhtml', locator

                browser.close()

        if errors:
            raise AssertionError('\n'.join(errors))
        print(f'EPUB stability browser ({browser_name}): OK')
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == '__main__':
    main()

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
EPUB_OFFLINE_URLS = (
    '/apps/epub/engine/navigation-index.js',
    '/apps/epub/ui/navigation-tools.js',
)


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local EPUB test server did not start')


def stop_server(server: subprocess.Popen | None) -> None:
    if server is None or server.poll() is not None:
        return
    server.terminate()
    try:
        server.wait(timeout=3)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=3)


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


def write_single_chapter_epub(path: Path, chapter: str, *, extra_entries: tuple[tuple[str, str], ...] = ()) -> None:
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
    opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:inkdos:epub-security</dc:identifier>
    <dc:title>Security Fixture</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest><item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="c1"/></spine>
</package>'''
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        zf.writestr('META-INF/container.xml', container, compress_type=zipfile.ZIP_STORED)
        zf.writestr('OEBPS/content.opf', opf, compress_type=zipfile.ZIP_STORED)
        zf.writestr('OEBPS/ch1.xhtml', chapter, compress_type=zipfile.ZIP_STORED)
        for name, data in extra_entries:
            zf.writestr(name, data, compress_type=zipfile.ZIP_STORED)


def build_malicious_epub(path: Path) -> None:
    chapter = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Security</title></head><body>
<h1 id="security">Security Chapter</h1>
<script>globalThis.__INKDOS_EPUB_XSS=1</script>
<style>body{display:none}</style>
<iframe src="https://attacker.invalid/frame"></iframe>
<object data="https://attacker.invalid/object"></object>
<svg xmlns="http://www.w3.org/2000/svg" onload="globalThis.__INKDOS_EPUB_XSS=1"><script>globalThis.__INKDOS_EPUB_XSS=1</script></svg>
<form action="https://attacker.invalid/form"><input autofocus="autofocus" onfocus="globalThis.__INKDOS_EPUB_XSS=1"/></form>
<p onclick="globalThis.__INKDOS_EPUB_XSS=1">Visible safe text. <a href="javascript:globalThis.__INKDOS_EPUB_XSS=1">Blocked JS link</a> <a href="https://attacker.invalid/link">Blocked external link</a></p>
<p><img src="https://attacker.invalid/pixel.png" alt="Remote image blocked"/></p>
</body></html>'''
    write_single_chapter_epub(path, chapter)


def build_entity_epub(path: Path) -> None:
    chapter = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html [<!ENTITY xxe "ENTITY SHOULD NOT LOAD">]>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Entity</title></head><body>
<h1>Entity Fixture</h1><p>&xxe;</p>
</body></html>'''
    write_single_chapter_epub(path, chapter)


def build_traversal_epub(path: Path) -> None:
    chapter = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Traversal</title></head><body>
<h1>Traversal Fixture</h1><p>This content must never commit.</p>
</body></html>'''
    write_single_chapter_epub(path, chapter, extra_entries=(('../escape.txt', 'must-not-escape'),))


def main() -> None:
    browser_name = os.environ.get('BROWSER', 'chromium').strip().lower()
    if browser_name not in {'chromium', 'firefox', 'webkit'}:
        raise RuntimeError(f'Unsupported BROWSER={browser_name}')

    server: subprocess.Popen | None = subprocess.Popen(
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
            malicious_path = Path(td) / 'malicious.epub'
            entity_path = Path(td) / 'entity.epub'
            traversal_path = Path(td) / 'traversal.epub'
            build_epub(epub_path)
            build_malicious_epub(malicious_path)
            build_entity_epub(entity_path)
            build_traversal_epub(traversal_path)
            with sync_playwright() as pw:
                browser = getattr(pw, browser_name).launch(headless=True)
                context = browser.new_context(viewport={'width': 1360, 'height': 900})
                page = context.new_page()
                page.on('pageerror', lambda exc: errors.append(f'pageerror: {exc}'))
                page.on('console', lambda msg: errors.append(f'console.error: {msg.text}') if msg.type == 'error' else None)

                # Install and activate the root service worker before exercising the app.
                page.goto(BASE + '/index.html', wait_until='load')
                assert page.evaluate("() => 'serviceWorker' in navigator") is True, browser_name
                page.evaluate('async () => { await navigator.serviceWorker.ready; return true; }')
                page.reload(wait_until='load')
                page.wait_for_function('() => !!navigator.serviceWorker.controller')

                # Optional toolbar controls must not be bootstrap dependencies. Simulate a
                # shell variant where Search and Bookmark cannot be resolved by getElementById.
                optional_errors: list[str] = []
                optional_page = context.new_page()
                optional_page.on('pageerror', lambda exc: optional_errors.append(f'pageerror: {exc}'))
                optional_page.on('console', lambda msg: optional_errors.append(f'console.error: {msg.text}') if msg.type == 'error' else None)
                optional_page.add_init_script("""(() => {
                    const original=Document.prototype.getElementById;
                    Document.prototype.getElementById=function(id){
                        if(location.pathname.startsWith('/apps/epub/') && (id==='searchBtn'||id==='bookmarkBtn'))return null;
                        return original.call(this,id);
                    };
                })()""")
                optional_page.goto(BASE + '/apps/epub/', wait_until='load')
                optional_page.wait_for_function('() => !!globalThis.__InkEpubR4')
                optional_probe = optional_page.evaluate("""() => {
                    globalThis.__InkEpubR4.navigation.openNavigation('search');
                    globalThis.__InkEpubR4.navigation.toggleBookmark();
                    return {
                        navigationOpen:!document.querySelector('#tocSheet').hidden,
                        searchOpen:!document.querySelector('[data-nav-panel="search"]').hidden,
                        searchLookup:document.getElementById('searchBtn')===null,
                        bookmarkLookup:document.getElementById('bookmarkBtn')===null,
                    };
                }""")
                assert all(optional_probe.values()), (browser_name, optional_probe)
                if optional_errors:
                    raise AssertionError('\n'.join(optional_errors))
                optional_page.close()

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

                missing = page.evaluate(
                    r"""async (paths) => {
                        const names=(await caches.keys()).filter(name=>name.startsWith('inkdos-'));
                        const inkCaches=await Promise.all(names.map(name=>caches.open(name)));
                        const missing=[];
                        for(const path of paths){
                            const url=new URL(path,location.origin).href;
                            let hit=false;
                            for(const cache of inkCaches){if(await cache.match(url)){hit=true;break;}}
                            if(!hit)missing.push(path);
                        }
                        return missing;
                    }""",
                    list(EPUB_OFFLINE_URLS),
                )
                assert missing == [], (browser_name, missing)

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

                # Hostile EPUB regression: active content and external resources must be projected
                # into inert local reader nodes without executing script or making remote requests.
                security_errors: list[str] = []
                external_requests: list[str] = []
                security_page = context.new_page()
                security_page.on('pageerror', lambda exc: security_errors.append(f'pageerror: {exc}'))
                security_page.on('console', lambda msg: security_errors.append(f'console.error: {msg.text}') if msg.type == 'error' else None)
                security_page.on('request', lambda request: external_requests.append(request.url) if request.url.startswith('https://attacker.invalid') else None)
                security_page.goto(BASE + '/apps/epub/', wait_until='load')
                security_page.wait_for_function('() => !!globalThis.__InkEpubR4')
                security_page.evaluate('() => { globalThis.__INKDOS_EPUB_XSS = 0; }')
                security_page.set_input_files('#fileInput', str(malicious_path))
                security_page.wait_for_function("""() => {
                    const s=globalThis.__InkEpubR4.state();
                    return s.fileName==='malicious.epub' && s.book && s.book.chapters.length===1;
                }""")
                hostile = security_page.evaluate("""() => {
                    const surface=document.getElementById('readerSurface');
                    return {
                        xss:globalThis.__INKDOS_EPUB_XSS,
                        blockedNodes:surface.querySelectorAll('script,style,iframe,object,embed,form,input,button,video,audio,canvas,svg,math,link').length,
                        anchors:surface.querySelectorAll('a').length,
                        remoteImages:surface.querySelectorAll('img[src^="http://"],img[src^="https://"],img[src^="//"]').length,
                        text:surface.innerText,
                        readerLinks:[...surface.querySelectorAll('.reader-link')].map(x=>({text:x.textContent,kind:x.dataset.linkKind,href:x.dataset.linkHref||''})),
                    };
                }""")
                assert hostile['xss'] == 0, (browser_name, hostile)
                assert hostile['blockedNodes'] == 0 and hostile['anchors'] == 0 and hostile['remoteImages'] == 0, (browser_name, hostile)
                assert 'Visible safe text.' in hostile['text'] and 'Remote image blocked' in hostile['text'], (browser_name, hostile)
                assert any(x['text'] == 'Blocked JS link' and x['kind'] == 'external' and x['href'].startswith('javascript:') for x in hostile['readerLinks']), hostile
                assert any(x['text'] == 'Blocked external link' and x['kind'] == 'external' and x['href'].startswith('https://attacker.invalid/') for x in hostile['readerLinks']), hostile
                assert external_requests == [], (browser_name, external_requests)

                before_url = security_page.url
                security_page.locator('#readerSurface .reader-link', has_text='Blocked JS link').click()
                security_page.wait_for_function("() => document.getElementById('chapterState').textContent.includes('External links are disabled')")
                assert security_page.url == before_url, (browser_name, security_page.url)
                assert security_page.evaluate('() => globalThis.__INKDOS_EPUB_XSS') == 0, browser_name
                assert external_requests == [], (browser_name, external_requests)

                security_page.locator('#readerSurface .reader-link', has_text='Blocked external link').click()
                assert security_page.url == before_url, (browser_name, security_page.url)
                assert external_requests == [], (browser_name, external_requests)

                # Entity/DOCTYPE and ZIP traversal failures must be transactional: a rejected
                # candidate cannot replace the already committed safe projection.
                security_page.set_input_files('#fileInput', str(entity_path))
                security_page.wait_for_function("() => /xml-(entity|doctype)/.test(document.getElementById('chapterState').textContent)")
                entity_probe = security_page.evaluate("""() => ({
                    fileName:globalThis.__InkEpubR4.state().fileName,
                    title:globalThis.__InkEpubR4.state().book && globalThis.__InkEpubR4.state().book.title,
                    text:document.getElementById('readerSurface').innerText,
                })""")
                assert entity_probe['fileName'] == 'malicious.epub' and entity_probe['title'] == 'Security Fixture', entity_probe
                assert 'Visible safe text.' in entity_probe['text'], entity_probe

                security_page.set_input_files('#fileInput', str(traversal_path))
                security_page.wait_for_function("() => document.getElementById('chapterState').textContent.includes('unsafe-path')")
                traversal_probe = security_page.evaluate("""() => ({
                    fileName:globalThis.__InkEpubR4.state().fileName,
                    title:globalThis.__InkEpubR4.state().book && globalThis.__InkEpubR4.state().book.title,
                    text:document.getElementById('readerSurface').innerText,
                })""")
                assert traversal_probe['fileName'] == 'malicious.epub' and traversal_probe['title'] == 'Security Fixture', traversal_probe
                assert 'Visible safe text.' in traversal_probe['text'], traversal_probe
                assert external_requests == [], (browser_name, external_requests)
                if security_errors:
                    raise AssertionError('\n'.join(security_errors))
                security_page.close()

                # Semantic reading flow survives removal of its toolbar controls.
                page.click('#scrollBtn')
                page.wait_for_function("() => globalThis.__InkEpubR4.state().flow === 'scroll'")
                page.evaluate("() => { document.getElementById('pagesBtn').remove(); document.getElementById('scrollBtn').remove(); globalThis.__InkEpubR4.setFlow('pages'); }")
                page.wait_for_function("() => globalThis.__InkEpubR4.state().flow === 'pages'")

                # Typography is a reader operation, not a dependency on the appearance button.
                page.evaluate("() => { document.getElementById('appearanceBtn').remove(); globalThis.__InkEpubR4.setFont(20); globalThis.__InkEpubR4.setFontStyle('sans'); }")
                page.wait_for_function("() => { const s=globalThis.__InkEpubR4.state(); return s.fontPx===20 && s.fontStyle==='sans'; }")

                # Navigation must survive removal and invalidation of the toolbar control itself.
                # This catches hidden programmatic dependencies on tocBtn.click().
                navigation_probe = page.evaluate("""() => {
                    const tocButton=document.getElementById('tocBtn');
                    Object.defineProperty(tocButton,'click',{value:()=>{throw new Error('tocBtn.click dependency');},configurable:true});
                    tocButton.remove();
                    globalThis.__InkEpubR4.navigation.openNavigation('search');
                    const navigationOpen=!document.getElementById('tocSheet').hidden;
                    const searchOpen=!document.querySelector('[data-nav-panel="search"]').hidden;
                    const ok=globalThis.__InkEpubR4.goPath('OEBPS/ch2.xhtml','two');
                    const locator=globalThis.__InkEpubR4.state().locator;
                    return {navigationOpen,searchOpen,ok,locator};
                }""")
                assert navigation_probe['navigationOpen'] is True, navigation_probe
                assert navigation_probe['searchOpen'] is True, navigation_probe
                assert navigation_probe['ok'] is True, navigation_probe
                locator = navigation_probe['locator']
                assert locator['chapter'] == 2, locator
                assert locator['path'] == 'OEBPS/ch2.xhtml', locator

                # A fresh reader boot must still resolve its navigation modules with the origin unavailable.
                # Stopping the HTTP server exercises the actual service-worker fallback and avoids
                # Playwright/WebKit's internal failure when combining set_offline() with reload().
                errors.clear()
                stop_server(server)
                server = None
                page.reload(wait_until='load', timeout=20_000)
                page.wait_for_function('() => !!globalThis.__InkEpubR4', timeout=15_000)
                offline = page.evaluate("""() => ({
                    navigationIndex:!!globalThis.InkDOS2Epub?.EpubNavigationIndex,
                    navigationTools:!!globalThis.InkDOS2Epub?.ReaderNavigationTools,
                    toolbarRail:document.querySelectorAll('.inkdos-toolbar-rail').length===1,
                    emptyState:!document.getElementById('emptyState').hidden,
                })""")
                assert all(offline.values()), (browser_name, offline)

                if errors:
                    raise AssertionError('\n'.join(errors))
                browser.close()

        print(f'EPUB stability browser ({browser_name}): OK')
    finally:
        stop_server(server)


if __name__ == '__main__':
    main()

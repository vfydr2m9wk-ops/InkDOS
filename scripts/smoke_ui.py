#!/usr/bin/env python3
"""Quick UI smoke check, run before every push and again on the published site after each deploy.

It opens what the owner uses (Home, the download panel, the Settings menu, each workspace with a small file) once,
in Chromium set up like an iPad (Safari user agent, touch, iPad screen size), and saves a screenshot of each step. It does not replace the regression tests; it catches the obvious "this stopped working"
before the owner sees it.

    python3 scripts/smoke_ui.py                       # local checkout, served on a free port
    python3 scripts/smoke_ui.py --base https://vfydr2m9wk-ops.github.io/InkDOS/
    python3 scripts/smoke_ui.py --out /tmp/smoke      # where the screenshots go (default: ./smoke-out)

Limits: Chromium only (no WebKit engine here), so Safari-only behaviour is not covered; the suite frame
(https://inkdos-tools.github.io) is always the published one.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import io
import socket
import sys
import threading
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TOOLS = 'https://inkdos-tools.github.io'

PDF = (b"%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
       b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 300]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")


def docx() -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml', '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>InkDOS smoke</w:t></w:r></w:p></w:body></w:document>')
    return out.getvalue()


IPAD = (1180, 820)  # iPad Air/Pro 11 in landscape
IPAD_UA = ('Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) '
           'Version/18.0 Mobile/15E148 Safari/604.1')
NO_SW = "try{delete Navigator.prototype.serviceWorker}catch(_){}"


class Run:
    def __init__(self, out: Path):
        self.out, self.results = out, []

    def check(self, name, ok, detail=''):
        self.results.append((name, bool(ok), detail))
        print(f"{'PASS' if ok else 'FAIL'}  {name}{('  · ' + detail) if detail else ''}")

    def shot(self, page, name):
        page.screenshot(path=str(self.out / f'{name}.png'))


def serve() -> tuple[str, http.server.ThreadingHTTPServer]:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    handler.log_message = lambda *a: None
    server = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{port}/', server


def home(run, browser, base, scheme, size, no_sw=False):
    tag = f"home-{scheme}-{size[0]}{'-nosw' if no_sw else ''}"
    ctx = browser.new_context(viewport={'width': size[0], 'height': size[1]}, color_scheme=scheme, has_touch=True, user_agent=IPAD_UA,
                              service_workers='block' if no_sw else 'allow')
    if no_sw:
        ctx.add_init_script(NO_SW)
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)[:160]))
    page.goto(base + 'index.html?smoke=' + str(time.time()), wait_until='load')
    page.wait_for_timeout(800)
    run.check(f'{tag}: six workspace cards', page.locator('.workspace-card').count() == 6)
    run.check(f'{tag}: download button left of Settings', page.evaluate(
        "()=>{const d=document.getElementById('toolsDownload'),s=document.getElementById('appearanceButton');"
        "return !!d&&!!s&&d.getBoundingClientRect().right<=s.getBoundingClientRect().left}"))
    run.shot(page, tag)
    page.click('#toolsDownload')
    panel = page.frame_locator('.tools-download-layer iframe')
    try:
        panel.locator('#offlineTools:not([hidden])').wait_for(state='visible', timeout=20000)
        visible = True
    except Exception:
        visible = False
    run.check(f'{tag}: download opens the Offline tools panel', visible)
    if visible:
        page.wait_for_timeout(1500)
        rows = panel.locator('.offline-row:visible').count()
        all_btn = panel.locator('[data-offline-all]:visible').count() == 1
        if no_sw:
            warn = panel.locator('[data-offline-warn]:visible').count() == 1
            run.check(f'{tag}: no service worker: notice and Download all', warn and all_btn)
        else:
            run.check(f'{tag}: tool list ({rows} rows) and Download all', rows >= 5 and all_btn, f'{rows} rows')
    run.shot(page, tag + '-download')
    # Close is posted only to the published InkDOS origin, so it can be checked only on the published site
    if visible and base.startswith('https://vfydr2m9wk-ops.github.io/'):
        panel.locator('[data-offline-close]').click()
        page.wait_for_timeout(500)
        run.check(f'{tag}: Close removes the panel', not page.evaluate("()=>!!document.querySelector('.tools-download-layer')"))
    page.keyboard.press('Escape')
    page.evaluate("()=>document.querySelector('.tools-download-layer')?.remove()")
    page.click('#appearanceButton')
    page.wait_for_timeout(300)
    run.check(f'{tag}: Settings menu opens', page.evaluate("()=>!document.getElementById('appearanceMenu').hidden"))
    run.check(f'{tag}: no page errors', not errors, '; '.join(errors[:2]))
    ctx.close()


def workspace(run, browser, base, app, name, data, accept, scheme='light', size=IPAD):
    ctx = browser.new_context(viewport={'width': size[0], 'height': size[1]}, color_scheme=scheme, has_touch=True, user_agent=IPAD_UA)
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)[:160]))
    page.goto(base + f'apps/{app}/index.html?suite=1&smoke={time.time()}', wait_until='load')
    page.wait_for_timeout(1000)
    page.set_input_files(f'input[type=file][accept*="{accept}"]', files=[{'name': name, 'mimeType': 'application/octet-stream', 'buffer': data}])
    page.wait_for_timeout(3500)
    run.check(f'{app}: opens {name}', name.split('.')[0] in (page.title() or '') or page.evaluate(
        "n=>document.body.innerText.includes(n)", name), page.title())
    titles = ("()=>Array.from(document.querySelectorAll('.inkdos-settings-popover-title'))"
              ".filter(x=>x.offsetParent).map(x=>x.textContent.trim())")
    page.click('[data-frame-action="sun"]')
    page.wait_for_timeout(300)
    sun = page.evaluate(titles)
    run.check(f'{app}: Settings (sun) only Appearance, Interface, Language', sun == ['Appearance', 'Interface', 'Language'], str(sun))
    run.shot(page, f'{app}-sun')
    page.click('[data-frame-action="sun"]')
    lock = page.locator('[data-frame-action="lock"]')
    ok = lock.count() == 1 and page.evaluate(
        "()=>document.querySelector('[data-frame-action=\"sun\"]').nextElementSibling===document.querySelector('[data-frame-action=\"lock\"]')")
    run.check(f'{app}: lock right of the sun', ok)
    if lock.count():
        lock.click()
        page.wait_for_timeout(300)
        run.check(f'{app}: lock shows Security / Recovery', page.evaluate(titles) == ['Security', 'Recovery'], str(page.evaluate(titles)))
        run.shot(page, f'{app}-lock')
        lock.click()
    if app in ('documents', 'spreadsheets', 'presentations'):
        run.check(f'{app}: Edit with ONLYOFFICE enabled, left of Settings', page.evaluate(
            "()=>{const b=document.getElementById('inkdosOfficeBtn'),s=document.querySelector('[data-frame-action=\"sun\"]');"
            "return !!b&&!b.disabled&&b.nextElementSibling===s}"))
    if app == 'pdf':
        run.check('pdf: task bar View · Annotate', page.evaluate(
            "()=>[...document.querySelectorAll('#pdfTaskBar [data-task]')].map(b=>b.dataset.task).join(',')") == 'view,annotate')
        run.check('pdf: Edit with BentoPDF left of Settings', page.evaluate(
            "()=>{const b=document.getElementById('pdfBentoBtn'),s=document.querySelector('[data-frame-action=\"sun\"]');return !!b&&b.nextElementSibling===s}"))
        page.click('#editModeBtn')
        page.wait_for_timeout(600)
        run.check('pdf: tool bar not cut off', page.evaluate(
            "()=>{const e=document.getElementById('editbar');return e.scrollWidth<=e.clientWidth+1}"))
    run.shot(page, f'{app}-{scheme}-{size[0]}')
    run.check(f'{app}: no page errors', not errors, '; '.join(errors[:2]))
    ctx.close()


def menus(run, browser, base, app):
    ctx = browser.new_context(viewport={'width': IPAD[0], 'height': IPAD[1]}, has_touch=True, user_agent=IPAD_UA)
    page = ctx.new_page()
    page.goto(base + f'apps/{app}/index.html?suite=1&smoke={time.time()}', wait_until='load')
    page.wait_for_selector('[data-frame-action="sun"]', timeout=15000)
    titles = ("()=>Array.from(document.querySelectorAll('.inkdos-settings-popover-title'))"
              ".filter(x=>x.offsetParent).map(x=>x.textContent.trim())")
    page.click('[data-frame-action="sun"]')
    page.wait_for_timeout(300)
    run.check(f'{app}: Settings (sun) only Appearance, Interface, Language', page.evaluate(titles) == ['Appearance', 'Interface', 'Language'], str(page.evaluate(titles)))
    page.click('[data-frame-action="sun"]')
    run.check(f'{app}: lock right of the sun', page.evaluate(
        "()=>document.querySelector('[data-frame-action=\"sun\"]').nextElementSibling===document.querySelector('[data-frame-action=\"lock\"]')"))
    ctx.close()


def phone_header(run, browser, base):
    # a phone-width header must keep every button on screen (the sun, the lock and share included)
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True)
    for app in ('documents', 'spreadsheets', 'presentations', 'pdf', 'txt', 'epub'):
        page = ctx.new_page()
        page.goto(base + f'apps/{app}/index.html?suite=1&smoke={time.time()}', wait_until='load')
        page.wait_for_selector('[data-frame-action="sun"]', timeout=15000)
        page.wait_for_timeout(500)
        right = page.evaluate("()=>Math.max(...[...document.querySelectorAll('header button')].filter(b=>b.offsetParent).map(b=>b.getBoundingClientRect().right))")
        run.check(f'{app}: phone header fits (390 px)', right <= 391, f'right edge {right:.0f}')
        page.close()
    ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', help='site to check (default: this checkout, served locally)')
    ap.add_argument('--out', default='smoke-out')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    server = None
    base = args.base
    if not base:
        base, server = serve()
    if not base.endswith('/'):
        base += '/'
    run = Run(out)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        home(run, browser, base, 'light', IPAD)
        workspace(run, browser, base, 'documents', 'smoke.docx', docx(), '.docx')
        workspace(run, browser, base, 'pdf', 'smoke.pdf', PDF, '.pdf')
        workspace(run, browser, base, 'txt', 'smoke.txt', b'InkDOS smoke\n', '.txt')
        for app in ('spreadsheets', 'presentations', 'epub'):
            menus(run, browser, base, app)
        phone_header(run, browser, base)
        browser.close()
    if server:
        server.shutdown()
    failed = [r for r in run.results if not r[1]]
    print(f'\n{len(run.results) - len(failed)}/{len(run.results)} passed · screenshots in {out}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()

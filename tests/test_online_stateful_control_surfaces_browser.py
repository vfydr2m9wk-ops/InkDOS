#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = os.environ.get("INKDOS_ONLINE_BASE", "https://vfydr2m9wk-ops.github.io/InkDOS/").rstrip("/") + "/"
OUT = Path(os.environ.get("INKDOS_STATEFUL_OUT", "audit-stateful-controls"))
OUT.mkdir(parents=True, exist_ok=True)

PAGES = {
    "home": "",
    "documents": "apps/documents/index.html",
    "spreadsheets": "apps/spreadsheets/index.html",
    "presentations": "apps/presentations/index.html",
    "pdf": "apps/pdf/index.html",
    "txt": "apps/txt/index.html",
    "epub": "apps/epub/index.html",
}


def minimal_pdf(path: Path) -> None:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length 44 >>\nstream\nBT /F1 18 Tf 72 720 Td (InkDOS audit) Tj ET\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{i} 0 obj\n".encode())
        data.extend(obj + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects)+1}\n".encode())
    data.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        data.extend(f"{off:010d} 00000 n \n".encode())
    data.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.write_bytes(data)


def minimal_epub(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""")
        z.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">audit</dc:identifier><dc:title>InkDOS Audit</dc:title><dc:language>en</dc:language></metadata>
  <manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="c1" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="c1"/></spine>
</package>""")
        z.writestr("OEBPS/nav.xhtml", """<!doctype html><html xmlns="http://www.w3.org/1999/xhtml"><body><nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops"><ol><li><a href="chapter.xhtml">Chapter</a></li></ol></nav></body></html>""")
        z.writestr("OEBPS/chapter.xhtml", """<!doctype html><html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Audit chapter</h1><p>InkDOS synthetic EPUB fixture for stateful controls.</p></body></html>""")


def key_for(el):
    return el.get("id") or el.get("aria") or el.get("text") or f"button-{el.get('index')}"


def inspect_buttons(page):
    return page.evaluate(
        """() => {
          const visible = el => {
            const s = getComputedStyle(el), r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' &&
              Number(s.opacity || 1) !== 0 && r.width > 0 && r.height > 0;
          };
          return [...document.querySelectorAll('button,[role="button"]')].map((el,index)=>({
            index,
            id: el.id || null,
            aria: el.getAttribute('aria-label'),
            text: (el.innerText || '').trim().replace(/\s+/g,' ').slice(0,100),
            visible: visible(el),
            disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
          }));
        }"""
    )


def click_if(page, selector, timeout=2500):
    loc = page.locator(selector)
    if loc.count() == 0 or not loc.first.is_visible() or not loc.first.is_enabled():
        return False
    loc.first.click(timeout=timeout, no_wait_after=True)
    page.wait_for_timeout(120)
    return True


def record(report, app, stage, page):
    buttons = inspect_buttons(page)
    report[app]["stages"].append({"stage": stage, "buttons": buttons})
    for b in buttons:
        k = key_for(b)
        report[app]["discovered"][k] = b
        if b["visible"]:
            report[app]["visibleUnion"][k] = b


def reset_transients(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(80)


def prepare_active(app, page, fixtures):
    if app == "documents":
        page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DocumentsApp")
        page.evaluate("""async()=>{await globalThis.InkDOS2Documents.DocumentsApp.newDocument(); await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}""")
    elif app == "spreadsheets":
        click_if(page, "#startNew")
        page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded")
    elif app == "presentations":
        click_if(page, "#startNew")
        page.wait_for_function("() => document.getElementById('startState')?.hidden === true")
    elif app == "txt":
        click_if(page, "#startNew")
        page.wait_for_function("() => document.getElementById('startState')?.hidden === true")
    elif app == "pdf":
        page.locator("#fileInput").set_input_files(str(fixtures["pdf"]))
        page.wait_for_function("() => document.getElementById('pageCount')?.textContent?.trim() !== '/ 0'", timeout=15000)
    elif app == "epub":
        page.locator("#fileInput").set_input_files(str(fixtures["epub"]))
        page.wait_for_function("() => document.getElementById('emptyState')?.hidden === true", timeout=15000)


SURFACES = {
    "home": [
        ("settings", "#appearanceButton"),
    ],
    "documents": [
        ("menu", "#menuBtn"),
        ("context", "#contextBtn"),
        ("zoom", "#zoomMenuBtn"),
        ("format", "#d1FormatBtn"),
        ("layout", "#d1LayoutBtn"),
        ("document-tools", "#d2P1Btn"),
    ],
    "spreadsheets": [
        ("menu", "#menuButton"),
        ("zoom", "#zoomMenuBtn"),
    ],
    "presentations": [
        ("menu", "#menuBtn"),
        ("zoom", "#zoomMenuBtn"),
        ("present", "#presentBtn"),
    ],
    "pdf": [
        ("menu", "#menuBtn"),
        ("navigation", "#navPanelBtn"),
    ],
    "txt": [
        ("menu", "#menuBtn"),
        ("find", "#findBtn"),
        ("list", "#listBtn"),
    ],
    "epub": [
        ("menu", "#menuBtn"),
        ("toc", "#tocBtn"),
        ("search", "#searchBtn"),
        ("appearance", "#appearanceBtn"),
        ("highlight", "#highlightBtn"),
    ],
}


def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fixtures = {"pdf": td / "audit.pdf", "epub": td / "audit.epub"}
        minimal_pdf(fixtures["pdf"])
        minimal_epub(fixtures["epub"])
        report = {"base": BASE, "apps": {}, "summary": {}, "errors": []}

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for app, rel in PAGES.items():
                context = browser.new_context(viewport={"width": 1440, "height": 810}, service_workers="block", accept_downloads=True)
                context.add_init_script("""(() => { try { localStorage.setItem('inkdos2:appearance','light'); localStorage.setItem('inkdos2:ui-density','desktop'); } catch(_){} })();""")
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda exc, bucket=errors: bucket.append("pageerror: " + str(exc)))
                page.on("console", lambda msg, bucket=errors: bucket.append("console-error: " + msg.text) if msg.type == "error" else None)
                page.on("dialog", lambda dialog: dialog.dismiss())
                page.on("download", lambda download: download.cancel())
                report["apps"][app] = {"stages": [], "discovered": {}, "visibleUnion": {}, "surfaceOpen": [], "errors": errors}
                page.goto(urljoin(BASE, rel), wait_until="load", timeout=30000)
                page.wait_for_timeout(250)
                record(report["apps"], app, "initial", page)
                if app != "home":
                    prepare_active(app, page, fixtures)
                    page.wait_for_timeout(250)
                    record(report["apps"], app, "active", page)

                for stage, selector in SURFACES[app]:
                    # Re-enter a clean page state for every transient surface so
                    # one drawer/popover cannot intercept the next surface's click.
                    page.goto(urljoin(BASE, rel), wait_until="load", timeout=30000)
                    page.wait_for_timeout(180)
                    if app != "home":
                        prepare_active(app, page, fixtures)
                        page.wait_for_timeout(180)
                    opened = click_if(page, selector)
                    if opened:
                        report["apps"][app]["surfaceOpen"].append(stage)
                        record(report["apps"], app, stage, page)
                        if app == "presentations" and stage == "present":
                            click_if(page, "[data-present-exit]")
                    else:
                        report["apps"][app]["surfaceOpen"].append(stage + ":not-opened")
                page.close()
                context.close()
            browser.close()

        total_discovered = total_visible = 0
        for app, data in report["apps"].items():
            discovered = set(data["discovered"])
            visible = set(data["visibleUnion"])
            data["coverage"] = {
                "discoveredButtons": len(discovered),
                "visibleAtLeastOnce": len(visible),
                "remainingNeverVisible": sorted(discovered - visible),
                "coveragePercent": round(100 * len(visible) / max(1, len(discovered)), 1),
            }
            total_discovered += len(discovered)
            total_visible += len(visible)
        report["summary"] = {
            "discoveredButtons": total_discovered,
            "visibleAtLeastOnce": total_visible,
            "coveragePercent": round(100 * total_visible / max(1, total_discovered), 1),
            "appsWithJsErrors": sum(1 for x in report["apps"].values() if x["errors"]),
        }
        (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(report["summary"], indent=2))
        for app, data in report["apps"].items():
            print(app, json.dumps(data["coverage"]))


if __name__ == "__main__":
    main()

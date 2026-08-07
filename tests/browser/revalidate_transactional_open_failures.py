"""Regression checks that failed opens preserve the active document state."""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser, requested_browser_name
from zipfile import ZipFile
import json
import os

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")
CORRUPT_BYTES = b"not a valid Office package"


def load_app(page, workspace, scripts):
    soup = BeautifulSoup((ROOT / f"apps/{workspace}/index.html").read_text(), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    base = soup.new_tag("base", href=ROOT.as_uri() + "/")
    if soup.head:
        soup.head.insert(0, base)
    page.set_content(str(soup), wait_until="domcontentloaded")
    for css in (ROOT / f"apps/{workspace}/styles.css", ROOT / "shared/office-shell.css"):
        page.add_style_tag(path=str(css))
    for script in scripts:
        page.add_script_tag(path=str(ROOT / script))


def verify_docx(browser):
    fixture = ROOT / "tests/compatibility-fixtures/documents/era2_office_2007_2013_baseline.docx"
    output = OUT / "transactional_docx_after_failed_open.docx"
    page = browser.new_page(viewport={"width": 1400, "height": 900}, accept_downloads=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    load_app(page, "documents", (
        "shared/office-runtime.js",
        "shared/vendor/pako_inflate.min.js",
        "apps/documents/docx-parser.js",
        "shared/vendor/jszip.min.js",
        "apps/documents/docx-writer.js",
        "shared/office-shell.js",
        "apps/documents/app.js",
    ))
    page.set_input_files("#fileInput", str(fixture))
    page.wait_for_function("document.querySelector('#pagesHost').innerText.includes('ERA2-DOCX-MARKER')")
    before = page.locator("#pagesHost").inner_text()
    page.set_input_files("#fileInput", {"name": "corrupt.docx", "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "buffer": CORRUPT_BYTES})
    page.wait_for_function("document.querySelector('#statusText').textContent.includes('previous document preserved')")
    after = page.locator("#pagesHost").inner_text()
    if before != after or page.locator("#titleText").input_value() != fixture.name:
        raise RuntimeError("DOCX state changed after a failed open")
    page.click("#dismissError")
    page.click("#saveBtn")
    page.wait_for_selector("#saveReadyPanel")
    with page.expect_download(timeout=30000) as info:
        page.click("#saveCopyDownload")
    info.value.save_as(str(output))
    with ZipFile(output) as package:
        document_xml = package.read("word/document.xml").decode("utf-8", "ignore")
    if "ERA2-DOCX-MARKER" not in document_xml:
        raise RuntimeError("DOCX save used stale or corrupt state after failed open")
    page.close()
    return {"workspace": "documents", "preserved": True, "page_errors": errors}


def verify_xlsx(browser):
    fixture = ROOT / "tests/compatibility-fixtures/spreadsheets/era2_office_2007_2013_baseline.xlsx"
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    errors, dialogs = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
    load_app(page, "spreadsheets", (
        "shared/office-runtime.js",
        "shared/vendor/jszip.min.js",
        "apps/spreadsheets/xls-biff8-engine.js",
        "apps/spreadsheets/xlsx-engine.js",
        "shared/office-shell.js",
        "apps/spreadsheets/app.js",
    ))
    page.set_input_files("#fileInput", str(fixture))
    page.wait_for_function("!document.querySelector('#gridViewport').hidden && !document.querySelector('#loading').offsetParent")
    before_title = page.locator("#docTitle").inner_text()
    before_tabs = page.locator("#sheetTabs").inner_text()
    before_cell = page.locator('.cell[data-r="0"][data-c="0"]').inner_text()
    page.set_input_files("#fileInput", {"name": "corrupt.xlsx", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "buffer": CORRUPT_BYTES})
    page.wait_for_function("!document.querySelector('#loading').offsetParent")
    if page.locator("#docTitle").inner_text() != before_title or page.locator("#sheetTabs").inner_text() != before_tabs or page.locator('.cell[data-r="0"][data-c="0"]').inner_text() != before_cell:
        raise RuntimeError("XLSX state changed after a failed open")
    if not any("could not open" in message.lower() for message in dialogs):
        raise RuntimeError("XLSX controlled error dialog was not shown")
    page.close()
    return {"workspace": "spreadsheets", "preserved": True, "page_errors": errors}


def verify_pptx(browser):
    fixture = ROOT / "tests/compatibility-fixtures/presentations/era2_office_2007_2013_baseline.pptx"
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    errors, dialogs = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
    load_app(page, "presentations", (
        "shared/office-runtime.js",
        "shared/vendor/jszip.min.js",
        "apps/presentations/engine/compatibility.js",
        "shared/office-shell.js",
        "apps/presentations/ui/inspector-controller.js",
        "apps/presentations/app.js",
    ))
    page.set_input_files("#fileInput", str(fixture))
    page.wait_for_function("window.__LocalPresentationsDebug && window.__LocalPresentationsDebug.slideCount > 0")
    before = page.evaluate("({name:window.__LocalPresentationsDebug.getPresentation().name, text:window.__LocalPresentationsDebug.getPresentation().slides[0].objects.map(o=>o.text||'').join('|'), bytes:window.__LocalPresentationsDebug.getSourceBuffer().byteLength})")
    page.set_input_files("#fileInput", {"name": "corrupt.pptx", "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "buffer": CORRUPT_BYTES})
    page.wait_for_function("document.querySelector('#stateBadge').textContent.includes('previous presentation preserved')")
    after = page.evaluate("({name:window.__LocalPresentationsDebug.getPresentation().name, text:window.__LocalPresentationsDebug.getPresentation().slides[0].objects.map(o=>o.text||'').join('|'), bytes:window.__LocalPresentationsDebug.getSourceBuffer().byteLength})")
    if before != after:
        raise RuntimeError(f"PPTX state changed after a failed open: {before!r} != {after!r}")
    if not any("could not be opened" in message.lower() for message in dialogs):
        raise RuntimeError("PPTX controlled error dialog was not shown")
    page.close()
    return {"workspace": "presentations", "preserved": True, "page_errors": errors}


def main():
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        results = [verify_docx(browser), verify_xlsx(browser), verify_pptx(browser)]
        browser.close()
    page_errors = [error for item in results for error in item["page_errors"]]
    if page_errors:
        raise RuntimeError(f"Unexpected page errors: {page_errors}")
    path = OUT / "transactional_open_failures.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

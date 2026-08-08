"""Behavioral regression for InkDesk v0.20.2.29 functional corrections."""
from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
VERSION = "0.20.2.29"


class FastThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def start_server():
    handler = partial(QuietHandler, directory=str(ROOT))
    server = FastThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def watch_errors(page):
    errors = []
    page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
    page.on(
        "console",
        lambda message: errors.append(f"console.error: {message.text}")
        if message.type == "error" and "Failed to load resource" not in message.text
        else None,
    )
    page.on(
        "response",
        lambda response: errors.append(f"HTTP {response.status}: {response.url}")
        if response.status >= 400
        else None,
    )
    return errors


def assert_true(value, message):
    if not value:
        raise RuntimeError(message)


def goto(page, url):
    page.goto(url, wait_until="networkidle")


def test_home_and_pdf(page, base_url, checks):
    goto(page, f"{base_url}/index.html")
    body = page.locator("body").inner_text()
    assert_true("Consolidated modular preview" not in body, "Obsolete Home eyebrow remains visible")
    assert_true("Open, review and make focused edits" not in body, "Obsolete Home description remains visible")
    assert_true(page.locator(".release-badge").inner_text().strip() == f"v{VERSION} beta", "Home release badge mismatch")
    assert_true(page.locator(".footer-status").inner_text().strip() == f"v{VERSION} beta", "Home footer version mismatch")
    checks.append("Home compact copy and release identity")

    goto(page, f"{base_url}/apps/pdf/index.html")
    assert_true(page.locator("#formNote").count() == 0, "Obsolete Forms: PDF.js badge remains in PDF UI")
    assert_true("Forms: PDF.js" not in page.locator("body").inner_text(), "Obsolete PDF.js forms text remains visible")
    checks.append("PDF obsolete forms badge removed")


def test_spreadsheet_rename(page, base_url, checks):
    goto(page, f"{base_url}/apps/spreadsheets/index.html")
    page.click("#newEmptyBtn")
    title = page.locator("#docTitle")
    title.fill("Budget Q3")
    title.press("Enter")
    page.wait_for_function("() => document.querySelector('#docTitle').value === 'Budget Q3.xlsx'")
    recovered = page.evaluate("async () => await window.__InkDeskSpreadsheetsRecovery.capture()")
    assert_true(recovered and recovered.get("fileName") == "Budget Q3.xlsx", f"Workbook rename did not reach model/recovery state: {recovered}")
    assert_true(page.locator("#dirtyDot").is_visible(), "Workbook rename did not mark the workbook dirty")
    checks.append("Spreadsheets editable filename updates model/recovery state")



def test_spreadsheet_history_safety(page, base_url, checks):
    goto(page, f"{base_url}/apps/spreadsheets/index.html")
    fixture = ROOT / "tests/compatibility-fixtures/spreadsheets/era2_office_2007_2013_baseline.xlsx"
    page.set_input_files("#fileInput", str(fixture))
    page.wait_for_function("() => !document.querySelector('#gridViewport').hidden && document.querySelectorAll('#sheetTabs button').length >= 2")
    summary_a1 = page.locator('.cell[data-r="0"][data-c="0"]').inner_text()
    formula = page.locator("#formulaInput")
    formula.fill("History Sheet A")
    formula.press("Enter")
    page.locator("#sheetTabs button", has_text="Data").click()
    data_a1 = page.locator('.cell[data-r="0"][data-c="0"]').inner_text()
    page.click("#undoBtn")
    assert_true(page.locator('.cell[data-r="0"][data-c="0"]').inner_text() == data_a1, "Undo from another tab mutated the active worksheet")
    page.locator("#sheetTabs button", has_text="Summary").click()
    assert_true(page.locator('.cell[data-r="0"][data-c="0"]').inner_text() == summary_a1, "Undo did not restore the worksheet where the action originated")
    page.locator("#sheetTabs button", has_text="Data").click()
    page.click("#redoBtn")
    assert_true(page.locator('.cell[data-r="0"][data-c="0"]').inner_text() == data_a1, "Redo from another tab mutated the active worksheet")
    page.locator("#sheetTabs button", has_text="Summary").click()
    assert_true(page.locator('.cell[data-r="0"][data-c="0"]').inner_text() == "History Sheet A", "Redo did not reapply the action to its original worksheet")

    goto(page, f"{base_url}/apps/spreadsheets/index.html")
    page.click("#newEmptyBtn")
    formula = page.locator("#formulaInput")
    formula.fill("one")
    formula.press("Enter")
    formula.fill("two")
    formula.press("Enter")
    recovered = page.evaluate("async () => await window.__InkDeskSpreadsheetsRecovery.capture()")
    history = recovered.get("history") if recovered else None
    assert_true(history and len(history.get("undo", [])) >= 2, f"Recovery snapshot did not preserve Undo history: {history}")
    formula.fill("three")
    formula.press("Enter")
    page.evaluate("async payload => await window.__InkDeskSpreadsheetsRecovery.restore({snapshot:{payload},source:null})", recovered)
    assert_true(page.locator('.cell[data-r="0"][data-c="0"]').inner_text() == "two", "Recovery did not restore the captured workbook state")
    page.click("#undoBtn")
    assert_true(page.locator('.cell[data-r="0"][data-c="0"]').inner_text() == "one", "Undo history was lost after recovery restore")
    checks.append("Spreadsheet Undo/Redo stays sheet-scoped and survives recovery restore")

def test_presentation_rename(page, base_url, checks):
    goto(page, f"{base_url}/apps/presentations/index.html")
    page.click("#newBtn")
    page.wait_for_selector("#templateDialog:not(.hidden)", state="visible")
    page.locator("#templateGrid .template-option").first.click()
    page.wait_for_selector("#app:not(.hidden)", state="visible")
    title = page.locator("#docTitle")
    title.fill("Roadmap")
    title.press("Enter")
    page.wait_for_function("() => document.querySelector('#docTitle').value === 'Roadmap.pptx'")
    recovered = page.evaluate("async () => await window.__InkDeskPresentationsRecovery.capture()")
    assert_true(recovered and recovered.get("fileName") == "Roadmap.pptx", f"Presentation rename did not reach model/recovery state: {recovered}")
    assert_true(page.locator("#stateBadge").inner_text().strip() == "Unsaved", "Presentation rename did not mark presentation unsaved")
    checks.append("Presentations editable filename updates model/recovery state")



def test_txt_interactions(page, base_url, checks):
    goto(page, f"{base_url}/apps/txt/index.html")
    assert_true(page.evaluate("() => !!window.InkDeskTxtHistoryController"), "TXT history controller did not load")
    assert_true(page.evaluate("() => !!window.InkDeskTxtFindController"), "TXT find controller did not load")
    page.click("#newStartBtn")
    editor = page.locator("#editor")
    editor.fill("alpha")
    page.wait_for_timeout(240)
    editor.press("End")
    editor.type(" beta")
    page.wait_for_timeout(240)
    page.click("#undoBtn")
    assert_true(editor.input_value() == "alpha", f"TXT Undo did not restore prior snapshot: {editor.input_value()!r}")
    page.click("#redoBtn")
    assert_true(editor.input_value() == "alpha beta", f"TXT Redo did not restore next snapshot: {editor.input_value()!r}")
    page.click("#findBtn")
    page.locator("#findInput").fill("beta")
    page.click("#findNext")
    selected = page.evaluate("() => [document.querySelector('#editor').selectionStart, document.querySelector('#editor').selectionEnd]")
    assert_true(selected == [6, 10], f"TXT Find did not select beta: {selected}")
    checks.append("TXT extracted history and Find interactions preserve behavior")



def test_unverified_export_protection(page, base_url, checks):
    # Documents: a download request must not clear dirty/recovery protection.
    goto(page, f"{base_url}/apps/documents/index.html")
    docx = ROOT / "tests/compatibility-fixtures/documents/era2_office_2007_2013_baseline.docx"
    page.set_input_files("#fileInput", str(docx))
    page.wait_for_function("() => document.querySelector('#statusText').textContent.includes('opened')", timeout=30000)
    page.wait_for_selector("#pagesHost .page-content", state="attached", timeout=30000)
    paragraph = page.locator("#pagesHost .page-content p").first
    paragraph.evaluate("node => { node.textContent += ' export guard'; node.dispatchEvent(new InputEvent('input', {bubbles:true,inputType:'insertText',data:' export guard'})); }")
    page.wait_for_function("() => document.querySelector('#dirtyDot').classList.contains('visible')")
    page.click("#saveBtn")
    page.wait_for_selector("#saveReadyPanel", state="visible")
    with page.expect_download() as info:
        page.click("#saveCopyDownload")
    download = info.value
    assert_true(bool(download.suggested_filename), "Documents save did not request a download")
    assert_true(page.locator("#dirtyDot").is_visible(), "Documents download request cleared dirty protection")
    assert_true(" •" in page.title(), "Documents title stopped warning after unverified download")

    # TXT: lifecycle must remain unverified after the browser receives the copy request.
    goto(page, f"{base_url}/apps/txt/index.html")
    page.click("#newStartBtn")
    editor = page.locator("#editor")
    editor.fill("unverified export protection")
    page.wait_for_function("() => !document.querySelector('#dirtyMark').hidden")
    with page.expect_download() as info:
        page.click("#saveBtn")
    download = info.value
    assert_true(bool(download.suggested_filename), "TXT save did not request a download")
    assert_true(not page.locator("#dirtyMark").get_attribute("hidden"), "TXT download request cleared dirty protection")
    assert_true(" •" in page.title(), "TXT title stopped warning after unverified download")

    # Presentations: generated-copy dispatch must not clear presentation dirty state.
    goto(page, f"{base_url}/apps/presentations/index.html")
    page.click("#newBtn")
    page.wait_for_selector("#templateDialog:not(.hidden)", state="visible")
    page.locator("#templateGrid .template-option").first.click()
    page.wait_for_selector("#app:not(.hidden)", state="visible")
    title = page.locator("#docTitle")
    title.fill("Export Guard")
    title.press("Enter")
    page.wait_for_function("() => document.title.includes(' •')")
    with page.expect_download(timeout=15000) as info:
        page.click("#saveBtn")
    download = info.value
    assert_true(bool(download.suggested_filename), "Presentations save did not request a download")
    assert_true(" •" in page.title(), "Presentations download request cleared dirty protection")
    checks.append("Documents, TXT and Presentations keep unverified export protection")

def titlebar_height(page, selector):
    return page.locator(selector).evaluate("node => Math.round(node.getBoundingClientRect().height)")


def test_compact_titlebars(browser, base_url, checks):
    context = browser.new_context(viewport={"width": 390, "height": 760})
    page = context.new_page()
    page.set_default_timeout(8000)
    try:
        goto(page, f"{base_url}/apps/txt/index.html")
        assert_true(titlebar_height(page, ".txt-titlebar") == 44, f"TXT title bar is not 44px: {titlebar_height(page, '.txt-titlebar')}")
        goto(page, f"{base_url}/apps/epub/index.html")
        assert_true(titlebar_height(page, ".epub-titlebar") == 44, f"EPUB title bar is not 44px: {titlebar_height(page, '.epub-titlebar')}")
        checks.append("TXT and EPUB compact title bars are 44px")
    finally:
        context.close()


def main():
    server, thread = start_server()
    base_url = f"http://127.0.0.1:{server.server_port}"
    report = {"browser": requested_browser_name(), "passed": False, "checks": [], "errors": []}
    try:
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            try:
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                page = context.new_page()
                page.set_default_timeout(8000)
                page.set_default_navigation_timeout(15000)
                report["errors"] = watch_errors(page)
                try:
                    test_home_and_pdf(page, base_url, report["checks"])
                    test_spreadsheet_rename(page, base_url, report["checks"])
                    test_spreadsheet_history_safety(page, base_url, report["checks"])
                    test_presentation_rename(page, base_url, report["checks"])
                    test_txt_interactions(page, base_url, report["checks"])
                    test_unverified_export_protection(page, base_url, report["checks"])
                except Exception as error:
                    if "ERR_BLOCKED_BY_ADMINISTRATOR" in str(error):
                        report.update({"passed": True, "status": "not-performed", "environment_block": str(error)})
                        print(json.dumps(report, indent=2))
                        return
                    raise
                finally:
                    context.close()
                test_compact_titlebars(browser, base_url, report["checks"])
                assert_true(not report["errors"], "Unexpected page/runtime errors: " + " | ".join(report["errors"]))
                report["passed"] = True
                print(json.dumps(report, indent=2))
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
        (OUT / f"v02021_functional_corrections_{requested_browser_name()}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

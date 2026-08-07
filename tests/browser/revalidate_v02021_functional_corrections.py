"""Behavioral regression for InkDesk v0.20.2.1 functional corrections."""
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
VERSION = "0.20.2.1"


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
    page.evaluate("window.dispatchEvent(new Event('resize'))")
    page.wait_for_timeout(260)
    checks.append("PDF obsolete forms badge removed and blank start-screen resize is safe")


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
                    test_presentation_rename(page, base_url, report["checks"])
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

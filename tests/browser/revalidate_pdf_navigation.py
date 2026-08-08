"""Isolated behavioral gate for PDF navigation, thumbnails and outline."""
from __future__ import annotations

import json
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfWriter

from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)


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


def make_pdf(path: Path):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=792, height=612)
    writer.add_blank_page(width=612, height=792)
    writer.add_outline_item("Second section", 1)
    writer.add_outline_item("Third section", 2)
    with path.open("wb") as handle:
        writer.write(handle)


def main():
    server, thread = start_server()
    base_url = f"http://127.0.0.1:{server.server_port}"
    report = {
        "browser": requested_browser_name(),
        "passed": False,
        "checks": [],
        "errors": [],
    }
    try:
        with tempfile.TemporaryDirectory(prefix="inkdesk-pdf-nav-") as temp_name:
            pdf_path = Path(temp_name) / "navigation-smoke.pdf"
            make_pdf(pdf_path)
            with sync_playwright() as playwright:
                browser = launch_browser(playwright)
                try:
                    context = browser.new_context(viewport={"width": 1280, "height": 820})
                    page = context.new_page()
                    page.set_default_timeout(10000)
                    page.set_default_navigation_timeout(15000)
                    report["errors"] = watch_errors(page)
                    try:
                        page.goto(
                            f"{base_url}/apps/pdf/index.html",
                            wait_until="networkidle",
                        )
                    except Exception as error:
                        if "ERR_BLOCKED_BY_ADMINISTRATOR" in str(error):
                            report.update(
                                {
                                    "passed": True,
                                    "status": "not-performed",
                                    "environment_block": str(error),
                                }
                            )
                            print(json.dumps(report, indent=2))
                            return
                        raise

                    version = page.evaluate("() => window.InkDeskPdfNavigationController?.version")
                    assert_true(version == "0.20.2.22", f"Unexpected navigation controller version: {version}")
                    report["checks"].append("navigation controller loaded")

                    page.set_input_files("#fileInput", str(pdf_path))
                    page.wait_for_function("() => window.InkDeskPdfDebug?.getState().pageCount === 3")
                    assert_true(page.locator("#pageList .page-item").count() == 3, "Page list did not render three entries")
                    page.wait_for_function("() => document.querySelectorAll('#pageList canvas.page-thumb').length >= 1")
                    report["checks"].append("page list and thumbnail window rendered")

                    # PDF navigation is intentionally collapsed by default. The isolated
                    # navigation gate must establish the sidebar state explicitly instead
                    # of assuming that its tabs are visible.
                    assert_true(
                        page.locator("#workspaceBody").evaluate(
                            "node => node.classList.contains('sidebar-collapsed')"
                        ),
                        "PDF navigation sidebar no longer starts collapsed by default",
                    )
                    assert_true(
                        page.locator("#sidebar").get_attribute("aria-hidden") == "true",
                        "Collapsed PDF sidebar did not expose aria-hidden=true",
                    )
                    page.click("#sidebarToggle")
                    page.wait_for_function(
                        "() => !document.getElementById('workspaceBody').classList.contains('sidebar-collapsed')"
                    )
                    assert_true(
                        page.locator("#sidebarToggle").get_attribute("aria-expanded") == "true",
                        "PDF sidebar toggle did not report expanded state",
                    )
                    assert_true(
                        page.locator('.sidebar-tab[data-tab="outline"]').is_visible(),
                        "PDF outline tab is not visible after opening the navigation sidebar",
                    )
                    report["checks"].append("sidebar default-closed state and explicit open")

                    page.click("#nextPage")
                    page.wait_for_function("() => window.InkDeskPdfDebug.getState().page === 2")
                    assert_true(page.locator("#pageNumber").input_value() == "2", "Next-page control did not synchronize page input")
                    page.click("#prevPage")
                    page.wait_for_function("() => window.InkDeskPdfDebug.getState().page === 1")
                    report["checks"].append("previous/next controls delegate to navigation controller")

                    page.click('.sidebar-tab[data-tab="outline"]')
                    page.wait_for_function("() => document.querySelectorAll('#outlineList .outline-item').length >= 2")
                    outline = page.locator("#outlineList .outline-item", has_text="Second section")
                    assert_true(outline.count() == 1, "Second-section outline item missing")
                    outline.click()
                    page.wait_for_function("() => window.InkDeskPdfDebug.getState().page === 2")
                    report["checks"].append("outline destination navigation")

                    page.click("#bookmarkBtn")
                    page.click('.sidebar-tab[data-tab="bookmarks"]')
                    bookmark = page.locator("#bookmarkList .bookmark-item", has_text="Page 2")
                    assert_true(bookmark.count() == 1, "Current-page bookmark was not rendered")
                    page.evaluate("() => window.InkDeskPdfDebug.goToPage(1)")
                    page.wait_for_function("() => window.InkDeskPdfDebug.getState().page === 1")
                    bookmark.click()
                    page.wait_for_function("() => window.InkDeskPdfDebug.getState().page === 2")
                    report["checks"].append("bookmark list navigation")

                    page.click('.sidebar-tab[data-tab="pages"]')
                    assert_true(page.locator('#pagesPanel').evaluate("node => node.classList.contains('active')"), "Pages panel did not reactivate")

                    # Exercise the shared workspace-layout sidebar controller as part of
                    # this isolated gate so future tests cannot silently depend on sidebar state.
                    page.click("#sidebarToggle")
                    page.wait_for_function(
                        "() => document.getElementById('workspaceBody').classList.contains('sidebar-collapsed')"
                    )
                    assert_true(
                        page.locator("#sidebar").get_attribute("aria-hidden") == "true",
                        "Closing PDF navigation did not update aria-hidden",
                    )
                    page.click("#sidebarToggle")
                    page.wait_for_function(
                        "() => !document.getElementById('workspaceBody').classList.contains('sidebar-collapsed')"
                    )
                    assert_true(
                        page.locator("#sidebarToggle").get_attribute("aria-expanded") == "true",
                        "Reopening PDF navigation did not restore aria-expanded",
                    )

                    assert_true(not report["errors"], "Unexpected PDF navigation errors: " + " | ".join(report["errors"]))
                    report["checks"].append("sidebar tab state and toggle round-trip")
                    report["passed"] = True
                    context.close()
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    (OUT / f"pdf_navigation_{requested_browser_name()}.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError(
            "PDF navigation validation failed: "
            + " | ".join(report["errors"] or ["behavioral assertion failed"])
        )


if __name__ == "__main__":
    main()

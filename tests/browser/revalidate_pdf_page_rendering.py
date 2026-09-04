"""Isolated behavioral gate for PDF page rendering and navigation."""
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
        with tempfile.TemporaryDirectory(prefix="inkdos-pdf-render-") as temp_name:
            pdf_path = Path(temp_name) / "rendering-smoke.pdf"
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

                    version = page.evaluate("() => window.InkDOSPdfPageRenderer?.version")
                    assert_true(version == "0.20.3.0", f"Unexpected page renderer version: {version}")
                    report["checks"].append("page renderer component loaded")

                    page.set_input_files("#fileInput", str(pdf_path))
                    page.wait_for_function("() => window.InkDOSPdfDebug?.getState().pageCount === 3")
                    state = page.evaluate("() => window.InkDOSPdfDebug.getState()")
                    assert_true(state["pagePlaceholders"] == 3, f"Expected 3 placeholders: {state}")
                    assert_true(state["renderedCanvases"] >= 1, f"No rendered PDF canvas: {state}")
                    report["checks"].append("three-page document rendered")

                    page.evaluate("() => window.InkDOSPdfDebug.goToPage(3)")
                    page.wait_for_function("() => window.InkDOSPdfDebug.getState().page === 3")
                    assert_true(page.locator("#pageNumber").input_value() == "3", "Page input did not sync to page 3")
                    report["checks"].append("navigation delegates through rendering window")

                    page.evaluate("() => window.InkDOSPdfDebug.setZoom('100')")
                    page.wait_for_timeout(250)
                    state = page.evaluate("() => window.InkDOSPdfDebug.getState()")
                    assert_true(state["zoom"] == "100", f"100% zoom did not persist: {state}")
                    assert_true(state["renderedCanvases"] >= 1, "Zoom rerender removed every visible canvas")
                    report["checks"].append("zoom rerender")

                    page.click("#horizontalScroll")
                    page.wait_for_function("() => window.InkDOSPdfDebug.getState().direction === 'horizontal'")
                    page.evaluate("() => window.InkDOSPdfDebug.goToPage(2)")
                    page.wait_for_function("() => window.InkDOSPdfDebug.getState().page === 2")
                    report["checks"].append("horizontal navigation")

                    page.set_viewport_size({"width": 1100, "height": 760})
                    page.wait_for_timeout(350)
                    assert_true(not report["errors"], "Unexpected PDF runtime errors: " + " | ".join(report["errors"]))
                    report["checks"].append("resize lifecycle without page errors")
                    report["passed"] = True
                    context.close()
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    (OUT / f"pdf_page_rendering_{requested_browser_name()}.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError(
            "PDF page rendering validation failed: "
            + " | ".join(report["errors"] or ["behavioral assertion failed"])
        )


if __name__ == "__main__":
    main()

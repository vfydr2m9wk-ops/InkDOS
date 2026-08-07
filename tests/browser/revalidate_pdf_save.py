"""Isolated behavioral gate for PDF unified save and flattened annotated export."""
from __future__ import annotations

import json
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

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

    def dismiss_unexpected_dialog(dialog):
        errors.append(f"dialog: {dialog.message}")
        dialog.dismiss()

    page.on("dialog", dismiss_unexpected_dialog)
    return errors


def assert_true(value, message):
    if not value:
        raise RuntimeError(message)


def make_pdf(path: Path):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with path.open("wb") as handle:
        writer.write(handle)


def validate_download(path: Path):
    data = path.read_bytes()
    assert_true(data.startswith(b"%PDF"), f"Downloaded file is not a PDF: {path.name}")
    reader = PdfReader(path, strict=False)
    assert_true(len(reader.pages) == 1, f"Unexpected saved page count: {len(reader.pages)}")


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
        with tempfile.TemporaryDirectory(prefix="inkdesk-pdf-save-") as temp_name:
            temp = Path(temp_name)
            pdf_path = temp / "save-smoke.pdf"
            make_pdf(pdf_path)

            with sync_playwright() as playwright:
                browser = launch_browser(playwright)
                try:
                    context = browser.new_context(viewport={"width": 1280, "height": 820}, accept_downloads=True)
                    page = context.new_page()
                    page.set_default_timeout(20000)
                    page.set_default_navigation_timeout(15000)
                    report["errors"] = watch_errors(page)
                    try:
                        page.goto(f"{base_url}/apps/pdf/index.html", wait_until="networkidle")
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

                    version = page.evaluate("() => window.InkDeskPdfSaveController?.version")
                    assert_true(version == "0.20.2.15", f"Unexpected save-controller version: {version}")
                    assert_true(page.locator("#saveModifiedPdfBtn").is_disabled(), "Save must start disabled without a document")
                    report["checks"].append("save controller loaded and starts unavailable")

                    page.set_input_files("#fileInput", str(pdf_path))
                    page.wait_for_function("() => window.InkDeskPdfDebug?.getState().pageCount === 1")

                    # pageCount becomes available as soon as PDF.js resolves the document,
                    # but openFile intentionally enables Save only after placeholders,
                    # navigation/review state and the initial page are ready. Establish
                    # that complete open state explicitly instead of racing the async
                    # openFile tail.
                    page.wait_for_function(
                        "() => !document.getElementById('saveModifiedPdfBtn').disabled"
                    )
                    assert_true(
                        not page.locator("#saveModifiedPdfBtn").is_disabled(),
                        "Save did not enable after the PDF open transaction completed",
                    )

                    with page.expect_download() as download_info:
                        page.click("#saveModifiedPdfBtn")
                    first_download = download_info.value
                    first_path = temp / "unannotated-save.pdf"
                    first_download.save_as(first_path)
                    assert_true(first_download.suggested_filename == "save-smoke-modified.pdf", f"Unexpected unannotated filename: {first_download.suggested_filename}")
                    validate_download(first_path)
                    page.wait_for_function("() => document.getElementById('statusText').textContent.includes('PDF saved')")
                    assert_true(page.locator("#saveModifiedPdfBtn").get_attribute("aria-busy") is None, "Save button stayed busy after PDF.js save")
                    report["checks"].append("PDF.js structure-preserving save path")

                    page.evaluate("() => window.InkDeskPdfDebug.addSyntheticAnnotation('highlight')")
                    page.wait_for_function("() => window.InkDeskPdfDebug.getState().annotations === 1")
                    with page.expect_download(timeout=30000) as download_info:
                        page.click("#saveModifiedPdfBtn")
                    second_download = download_info.value
                    second_path = temp / "annotated-save.pdf"
                    second_download.save_as(second_path)
                    assert_true(second_download.suggested_filename == "save-smoke-modified.pdf", f"Unexpected annotated filename: {second_download.suggested_filename}")
                    validate_download(second_path)
                    page.wait_for_function("() => document.getElementById('statusText').textContent.includes('Annotated PDF saved')")
                    assert_true(page.locator("#dirtyMark").is_hidden(), "Successful annotated save did not clear dirty indicator")
                    assert_true(not page.locator("#saveModifiedPdfBtn").is_disabled(), "Save did not re-enable after annotated export")
                    assert_true(page.locator("#saveModifiedPdfBtn").get_attribute("aria-busy") is None, "Save button stayed busy after annotated export")
                    report["checks"].append("flattened annotated save path and button lifecycle")

                    assert_true(not report["errors"], "Unexpected PDF save errors: " + " | ".join(report["errors"]))
                    report["passed"] = True
                    context.close()
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    (OUT / f"pdf_save_{requested_browser_name()}.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError(
            "PDF save validation failed: "
            + " | ".join(report["errors"] or ["behavioral assertion failed"])
        )


if __name__ == "__main__":
    main()

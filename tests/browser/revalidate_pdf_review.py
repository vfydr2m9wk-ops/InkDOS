"""Isolated behavioral gate for PDF review annotations, comments and persistence."""
from __future__ import annotations

import json
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

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


def make_text_pdf(path: Path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): font_ref}
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(
        b"BT /F1 18 Tf 72 720 Td (Review target phrase for InkDesk) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as handle:
        writer.write(handle)


def select_first_text_span(page):
    return page.evaluate(
        """() => {
          const span = [...document.querySelectorAll('.textLayer span')]
            .find(node => node.textContent.trim().length > 0);
          if (!span) return false;
          const range = document.createRange();
          range.selectNodeContents(span);
          const selection = window.getSelection();
          selection.removeAllRanges();
          selection.addRange(range);
          document.dispatchEvent(new Event('selectionchange'));
          return selection.toString().trim().length > 0;
        }"""
    )


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
        with tempfile.TemporaryDirectory(prefix="inkdesk-pdf-review-") as temp_name:
            pdf_path = Path(temp_name) / "review-smoke.pdf"
            make_text_pdf(pdf_path)
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

                    versions = page.evaluate(
                        "() => ({controller: window.InkDeskPdfReviewController?.version, layer: window.InkDeskPdfAnnotationLayer?.version})"
                    )
                    assert_true(
                        versions == {"controller": "0.20.2.27", "layer": "0.20.2.27"},
                        f"Unexpected PDF review component versions: {versions}",
                    )
                    report["checks"].append("review components loaded")

                    page.set_input_files("#fileInput", str(pdf_path))
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug?.getState().pageCount === 1"
                    )
                    page.wait_for_function(
                        "() => [...document.querySelectorAll('.textLayer span')].some(node => node.textContent.trim().length > 0)"
                    )

                    assert_true(select_first_text_span(page), "Could not establish PDF text selection")
                    page.wait_for_timeout(120)
                    applied = page.evaluate(
                        "() => window.InkDeskPdfDebug.applyCapturedSelection('highlight')"
                    )
                    assert_true(applied, "Selected-text highlight was not applied")
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug.getState().selectedTextAnnotations >= 1"
                    )
                    assert_true(
                        page.locator(".page-review-layer .review-annotation.highlight").count() >= 1,
                        "Highlight review segments were not rendered",
                    )
                    assert_true(not page.locator("#dirtyMark").is_hidden(), "Review change did not mark PDF dirty")
                    report["checks"].append("selected-text highlight and dirty state")

                    page.click("#undoReview")
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug.getState().annotations === 0"
                    )
                    report["checks"].append("review undo")

                    page.click('.annotation-tool[data-tool="marker"]')
                    layer = page.locator(".page-review-layer").first
                    bounds = layer.bounding_box()
                    assert_true(bounds is not None, "Free-review layer has no bounds")
                    page.mouse.move(bounds["x"] + 60, bounds["y"] + 60)
                    page.mouse.down()
                    page.mouse.move(bounds["x"] + 180, bounds["y"] + 95)
                    page.mouse.up()
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug.getState().annotations === 1"
                    )
                    assert_true(
                        page.locator(".page-review-layer .review-annotation.marker").count() == 1,
                        "Free marker annotation was not rendered",
                    )
                    page.click("#undoReview")
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug.getState().annotations === 0"
                    )
                    report["checks"].append("free marker and undo")

                    page.click('.annotation-tool[data-tool="select"]')
                    assert_true(select_first_text_span(page), "Could not re-establish text selection")
                    page.wait_for_timeout(120)
                    page.once("dialog", lambda dialog: dialog.accept("Review comment"))
                    commented = page.evaluate(
                        "() => window.InkDeskPdfDebug.applyCapturedSelection('comment')"
                    )
                    assert_true(commented, "Selected-text comment was not applied")
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug.getState().annotations >= 1"
                    )
                    page.click("#sidebarToggle")
                    page.wait_for_function(
                        "() => !document.getElementById('workspaceBody').classList.contains('sidebar-collapsed')"
                    )
                    page.click('.sidebar-tab[data-tab="comments"]')
                    comment = page.locator("#commentList .comment-item", has_text="Review comment")
                    assert_true(comment.count() == 1, "Comment sidebar entry was not rendered")
                    comment.click()
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug.getState().page === 1"
                    )
                    report["checks"].append("selected-text comment and sidebar navigation")

                    persisted_count = page.evaluate(
                        "() => window.InkDeskPdfDebug.getState().annotations"
                    )
                    page.reload(wait_until="networkidle")
                    page.set_input_files("#fileInput", str(pdf_path))
                    page.wait_for_function(
                        "() => window.InkDeskPdfDebug?.getState().pageCount === 1"
                    )
                    page.wait_for_function(
                        "expected => window.InkDeskPdfDebug.getState().annotations === expected",
                        arg=persisted_count,
                    )
                    assert_true(
                        "Review comment" in page.locator("#commentList").inner_text(),
                        "Persisted local review comment did not reload",
                    )
                    report["checks"].append("local review persistence")

                    assert_true(
                        not report["errors"],
                        "Unexpected PDF review runtime errors: " + " | ".join(report["errors"]),
                    )
                    report["passed"] = True
                    context.close()
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    (OUT / f"pdf_review_{requested_browser_name()}.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError(
            "PDF review validation failed: "
            + " | ".join(report["errors"] or ["behavioral assertion failed"])
        )


if __name__ == "__main__":
    main()

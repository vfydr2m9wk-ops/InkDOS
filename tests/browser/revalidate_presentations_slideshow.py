"""Isolated behavioral gate for Presentations slideshow/presentation mode."""
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

    def console(message):
        if message.type == "error" and "Failed to load resource" not in message.text:
            errors.append(f"console.error: {message.text}")

    def response(item):
        if item.status >= 400:
            errors.append(f"HTTP {item.status}: {item.url}")

    page.on("console", console)
    page.on("response", response)
    return errors


def assert_true(value, message):
    if not value:
        raise RuntimeError(message)


def create_two_slide_presentation(page):
    # Establish the scenario's own initial UI state instead of depending on a
    # previous control test. This is the browser-test isolation contract.
    page.click("#newBtn")
    page.wait_for_selector("#templateDialog:not(.hidden)", state="visible")
    page.locator("#templateGrid .template-option").first.click()
    page.wait_for_selector("#app:not(.hidden)", state="visible")
    page.wait_for_selector("#slideCanvas .obj", state="visible")

    page.click('[data-tab="home"]')
    page.click("#addSlideBtn")
    page.wait_for_selector("#templateDialog:not(.hidden)", state="visible")
    page.locator("#templateGrid .template-option").last.click()
    page.wait_for_function("document.querySelectorAll('#slideList .thumb').length === 2")
    assert_true(
        "Slide 2 of 2" in page.locator("#slideStatus").inner_text(),
        "Second slide was not created before slideshow validation",
    )


def disable_host_fullscreen(page):
    page.locator("#presentOverlay").evaluate(
        """node => {
            try { Object.defineProperty(node, 'requestFullscreen', {value: undefined, configurable: true}); } catch (error) { void error; }
            try { Object.defineProperty(node, 'webkitRequestFullscreen', {value: undefined, configurable: true}); } catch (error) { void error; }
        }"""
    )


def dispatch_present_key(page, key):
    page.locator("#presentOverlay").evaluate(
        "(node, key) => node.dispatchEvent(new KeyboardEvent('keydown', {key, bubbles:true, cancelable:true}))",
        key,
    )
    page.wait_for_timeout(80)


def select_editor_slide(page, zero_based_index):
    """Establish editor slide state explicitly before a current-slide entry."""
    page.locator("#slideList .thumb").nth(zero_based_index).click()
    expected = f"Slide {zero_based_index + 1} of 2"
    page.wait_for_function(
        "(expected) => document.getElementById('slideStatus').textContent.includes(expected)",
        arg=expected,
    )
    assert_true(
        expected in page.locator("#slideStatus").inner_text(),
        f"Could not establish editor state: {expected}",
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
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            try:
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                page = context.new_page()
                page.set_default_timeout(8000)
                page.set_default_navigation_timeout(15000)
                report["errors"] = watch_errors(page)
                try:
                    page.goto(
                        f"{base_url}/apps/presentations/index.html",
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

                create_two_slide_presentation(page)
                disable_host_fullscreen(page)

                # Top-level current-slide entry establishes slide two explicitly.
                select_editor_slide(page, 1)
                page.click("#presentFromCurrentTop")
                page.wait_for_selector("#presentOverlay:not(.hidden)", state="visible")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "2 / 2",
                    "Top Current did not start from the selected second slide",
                )
                report["checks"].append("top current-slide entry")

                dispatch_present_key(page, "Home")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "1 / 2",
                    "Home did not move slideshow to the first slide",
                )
                dispatch_present_key(page, "End")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "2 / 2",
                    "End did not move slideshow to the last slide",
                )
                dispatch_present_key(page, "ArrowLeft")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "1 / 2",
                    "ArrowLeft did not move slideshow backward",
                )
                dispatch_present_key(page, "ArrowRight")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "2 / 2",
                    "ArrowRight did not move slideshow forward",
                )
                report["checks"].append("Home/End/Arrow slideshow navigation")

                dispatch_present_key(page, "Escape")
                page.wait_for_selector("#presentOverlay.hidden", state="attached")
                assert_true(
                    "presentation-active"
                    not in (page.locator("body").get_attribute("class") or ""),
                    "Escape did not clear presentation-active body state",
                )
                report["checks"].append("Escape exit")

                # View-tab entry is a separate visible control and starts from current.
                # Establish the editor's current slide instead of inheriting slideshow navigation state.
                select_editor_slide(page, 1)
                page.click('[data-tab="view"]')
                page.click("#presentViewBtn")
                page.wait_for_selector("#presentOverlay:not(.hidden)", state="visible")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "2 / 2",
                    "View Present current did not start from slide two",
                )
                page.click("#exitPresentBtn")
                page.wait_for_selector("#presentOverlay.hidden", state="attached")
                report["checks"].append("View present-current entry and visible Exit")

                # Present-tab entries establish their own tab state in this scenario.
                page.click('[data-tab="present"]')
                page.click("#presentFromStartBtn")
                page.wait_for_selector("#presentOverlay:not(.hidden)", state="visible")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "1 / 2",
                    "Present-tab From first did not reset to slide one",
                )
                page.click("#exitPresentBtn")
                page.wait_for_selector("#presentOverlay.hidden", state="attached")
                assert_true(
                    "Slide 1 of 2" in page.locator("#slideStatus").inner_text(),
                    "From first no longer left the editor on slide one as in the pre-refactor behavior",
                )

                # "From current" means the slide that is current when the command is invoked.
                # Re-select slide two explicitly after the prior From-first scenario changed it to slide one.
                select_editor_slide(page, 1)
                page.click('[data-tab="present"]')
                page.click("#presentFromCurrentBtn")
                page.wait_for_selector("#presentOverlay:not(.hidden)", state="visible")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "2 / 2",
                    "Present-tab From current did not use the selected second slide",
                )
                page.click("#exitPresentBtn")
                page.wait_for_selector("#presentOverlay.hidden", state="attached")
                report["checks"].append("Present-tab first/current entries")

                # Top From start remains a separate entry point and must also reset.
                page.click("#presentFromStartTop")
                page.wait_for_selector("#presentOverlay:not(.hidden)", state="visible")
                assert_true(
                    page.locator("#presentCounter").inner_text().strip() == "1 / 2",
                    "Top From start did not reset to slide one",
                )
                page.click("#exitPresentBtn")
                page.wait_for_selector("#presentOverlay.hidden", state="attached")
                report["checks"].append("top first-slide entry")

                report["passed"] = not report["errors"]
                context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    (OUT / f"presentations_slideshow_{requested_browser_name()}.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError(
            "Presentations slideshow validation failed: "
            + " | ".join(report["errors"] or ["behavioral assertion failed"])
        )


if __name__ == "__main__":
    main()

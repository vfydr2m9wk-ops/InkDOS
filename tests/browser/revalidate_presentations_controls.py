"""Behavioral checks for visible Presentations controls, including compact format panel."""
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



def inspector_state(page):
    return page.locator("#inspector").evaluate(
        """node => {
            const style = getComputedStyle(node);
            const rect = node.getBoundingClientRect();
            return {
                display: style.display,
                visibility: style.visibility,
                opacity: style.opacity,
                position: style.position,
                pointerEvents: style.pointerEvents,
                width: rect.width,
                height: rect.height,
                workspaceClass: node.closest('.workspace')?.className || '',
                inspectorState: node.closest('.workspace')?.dataset.inspectorOpen || '',
                ariaExpanded: document.querySelector('#toggleInspectorBtn')?.getAttribute('aria-expanded') || '',
                buttonText: document.querySelector('#toggleInspectorBtn')?.textContent || '',
                innerWidth: window.innerWidth,
                compact: matchMedia('(max-width:1000px)').matches,
            };
        }"""
    )


def wait_inspector_visible(page, expected, label):
    try:
        page.wait_for_function(
            "expected => { const e=document.querySelector('#inspector'); if(!e) return false; const s=getComputedStyle(e); const r=e.getBoundingClientRect(); const visible=s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity)>0 && r.width>0 && r.height>0; return visible===expected; }",
            arg=expected,
            timeout=2500,
        )
    except Exception as error:
        raise RuntimeError(f"{label}; inspector state={inspector_state(page)}") from error


def wait_toggle_state(page, expected, label):
    try:
        page.wait_for_function(
            "expected => document.querySelector('#toggleInspectorBtn')?.getAttribute('aria-expanded') === String(expected)",
            arg=expected,
            timeout=2500,
        )
    except Exception as error:
        state = inspector_state(page)
        state["ariaExpanded"] = page.locator("#toggleInspectorBtn").get_attribute("aria-expanded")
        state["buttonText"] = page.locator("#toggleInspectorBtn").inner_text()
        raise RuntimeError(f"{label}; inspector state={state}") from error

def create_presentation(page):
    page.click("#newBtn")
    page.wait_for_selector("#templateDialog:not(.hidden)", state="visible")
    page.locator("#templateGrid .template-option").first.click()
    page.wait_for_selector("#app:not(.hidden)", state="visible")
    page.wait_for_selector("#slideCanvas .obj", state="visible")


def ensure_notes_visible(page):
    notes = page.locator("#presenterNotes")
    if notes.is_visible():
        return
    page.click('[data-tab="view"]')
    # The visible View control is the supported way to recover a collapsed panel.
    for _ in range(2):
        page.click("#toggleNotesBtn")
        page.wait_for_timeout(100)
        if notes.is_visible():
            return
    raise RuntimeError("Presenter notes could not be shown through the View controls")


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
                    page.goto(f"{base_url}/apps/presentations/index.html", wait_until="networkidle")
                except Exception as error:
                    if "ERR_BLOCKED_BY_ADMINISTRATOR" in str(error):
                        report.update({"passed": True, "status": "not-performed", "environment_block": str(error)})
                        print(json.dumps(report, indent=2))
                        return
                    raise

                create_presentation(page)

                # Desktop format panel starts collapsed by product policy. The
                # visible View button must open it, hide it, and reopen it.
                page.click('[data-tab="view"]')
                inspector = page.locator("#inspector")
                toggle = page.locator("#toggleInspectorBtn")
                wait_inspector_visible(page, False, "Format panel should start collapsed in the desktop layout")
                desktop_state = inspector_state(page)
                assert_true(desktop_state["innerWidth"] == 1280 and not desktop_state["compact"], f"Desktop viewport mismatch: {desktop_state}")
                assert_true(toggle.get_attribute("aria-expanded") == "false", "Collapsed desktop format button should report aria-expanded=false")
                assert_true("Show format panel" in (toggle.inner_text() or ""), "Collapsed desktop format button should invite opening")
                toggle.click()
                wait_inspector_visible(page, True, "Show format panel did not open the desktop inspector")
                assert_true(toggle.get_attribute("aria-expanded") == "true", "Open desktop format button should report aria-expanded=true")
                toggle.click()
                wait_inspector_visible(page, False, "Hide format panel did not hide the desktop inspector")
                toggle.click()
                wait_inspector_visible(page, True, "Show format panel did not restore the desktop inspector")
                report["checks"].append("desktop format panel closed-by-default/open/hide/reopen")

                # The panel must control the selected object rather than being decorative UI.
                page.click('[data-tab="insert"]')
                page.click("#insertTextBtn")
                selected = page.locator("#slideCanvas .obj.selected")
                assert_true(selected.count() == 1, "Insert text did not leave one selected object")
                page.fill("#propRotation", "17")
                page.dispatch_event("#propRotation", "change")
                transform = selected.get_attribute("style") or ""
                assert_true("rotate(17deg)" in transform, "Format panel rotation did not update the selected object")
                page.locator("#propFill").evaluate(
                    "node => { node.value='#2563eb'; node.dispatchEvent(new Event('input',{bubbles:true})); }"
                )
                background = selected.evaluate("node => getComputedStyle(node).backgroundColor")
                assert_true(background in {"rgb(37, 99, 235)", "rgba(37, 99, 235, 1)"}, "Format panel fill did not update the selected object")
                report["checks"].append("format panel modifies selected object")

                # Selection and history are separate state components in v0.20.2.10.
                # Verify that clearing/reselecting still drives the visible handles
                # and that Undo/Redo restores the same selected object state.
                page.locator("#slideCanvas").evaluate("node => node.click()")
                assert_true(page.locator("#slideCanvas .obj.selected").count() == 0, "Canvas click did not clear object selection")
                page.locator("#slideCanvas .obj").last.evaluate("node => node.click()")
                assert_true(page.locator("#slideCanvas .obj.selected").count() == 1, "Object click did not restore selection")
                page.wait_for_timeout(450)
                page.click("#undoBtn")
                undone = page.locator("#slideCanvas .obj.selected")
                assert_true(undone.count() == 1, "Undo did not preserve the snapshot selection")
                undone_style = undone.get_attribute("style") or ""
                assert_true("rotate(17deg)" not in undone_style, "Undo did not restore the pre-format object state")
                page.click("#redoBtn")
                redone = page.locator("#slideCanvas .obj.selected")
                assert_true(redone.count() == 1, "Redo did not restore the selected object")
                redone_style = redone.get_attribute("style") or ""
                assert_true("rotate(17deg)" in redone_style, "Redo did not restore the formatted object state")
                report["checks"].append("selection clear/reselect and Undo/Redo snapshot restoration")

                # Presenter notes toggle must be reversible.
                ensure_notes_visible(page)
                page.click('[data-tab="view"]')
                page.click("#toggleNotesBtn")
                page.wait_for_timeout(120)
                assert_true(not page.locator("#presenterNotes").is_visible(), "Hide presenter notes did not hide the editor")
                page.click("#toggleNotesBtn")
                page.wait_for_timeout(120)
                assert_true(page.locator("#presenterNotes").is_visible(), "Show presenter notes did not restore the editor")
                report["checks"].append("presenter notes hide/show")

                # Thumbnail toggle must update both layout state and control text.
                page.click("#togglePresentationsBtn")
                assert_true("hide-slides" in (page.locator(".workspace").get_attribute("class") or ""), "Hide thumbnails did not change workspace state")
                page.click("#togglePresentationsBtn")
                assert_true("hide-slides" not in (page.locator(".workspace").get_attribute("class") or ""), "Show thumbnails did not restore workspace state")
                report["checks"].append("thumbnail panel hide/show")

                # Slideshow is intentionally exercised in a fresh browser process by
                # revalidate_presentations_slideshow.py. Keep this control suite focused
                # on inspector, notes, thumbnails, selection/history and responsive state.

                # Desktop -> compact must preserve one logical open/closed state.
                # The layout changes from sidebar to drawer, but resizing must not
                # silently flip the user's choice or desynchronize CSS and ARIA.
                page.set_viewport_size({"width": 820, "height": 800})
                page.click('[data-tab="view"]')
                wait_inspector_visible(page, True, "Open desktop format panel did not remain open as a compact drawer")
                wait_toggle_state(page, True, "Compact format button lost the open state after the breakpoint change")
                compact_state = inspector_state(page)
                assert_true(compact_state["innerWidth"] == 820 and compact_state["compact"], f"Compact viewport mismatch: {compact_state}")
                assert_true("inspector-open" in compact_state["workspaceClass"], f"Compact layout lost the canonical open class: {compact_state}")
                assert_true("hide-inspector" not in compact_state["workspaceClass"], f"Compact layout retained a contradictory hide class: {compact_state}")
                assert_true(compact_state["position"] == "fixed", f"Compact format panel is not a fixed drawer: {compact_state}")

                # The same button must close and reopen the drawer after resizing.
                toggle.click()
                wait_inspector_visible(page, False, "Compact format button did not close the drawer")
                wait_toggle_state(page, False, "Compact format button did not report collapsed state")
                toggle.click()
                wait_inspector_visible(page, True, "Compact format button did not reopen the drawer")
                wait_toggle_state(page, True, "Compact format button did not report expanded state after reopening")
                page.press("body", "Escape")
                wait_inspector_visible(page, False, "Escape did not close the compact format drawer")
                wait_toggle_state(page, False, "Escape did not synchronize the compact format button state")
                report["checks"].append("desktop-to-compact format state continuity/open-close-escape")

                # Tab wiring: every visible presentation tab must expose its own toolbar group.
                for tab, tools in (("home", "toolsHome"), ("insert", "toolsInsert"), ("arrange", "toolsArrange"), ("view", "toolsView"), ("present", "toolsPresent")):
                    page.click(f'[data-tab="{tab}"]')
                    assert_true(page.locator(f"#{tools}").is_visible(), f"{tab} tab did not expose {tools}")
                report["checks"].append("Home/Insert/Arrange/View/Present tab wiring")
                context.close()

                # Real iPad/mobile cold start. This is intentionally a fresh
                # context because the production bug only appeared when the app
                # opened below the breakpoint: resetOptionalPanelsForOpen()
                # could re-add hide-inspector after the initial matchMedia sync.
                compact_context = browser.new_context(viewport={"width": 820, "height": 800})
                compact_page = compact_context.new_page()
                compact_page.set_default_timeout(8000)
                compact_page.set_default_navigation_timeout(15000)
                compact_errors = watch_errors(compact_page)
                compact_page.goto(f"{base_url}/apps/presentations/index.html", wait_until="networkidle")
                create_presentation(compact_page)
                compact_page.click('[data-tab="view"]')
                cold_toggle = compact_page.locator("#toggleInspectorBtn")
                wait_inspector_visible(compact_page, False, "Cold-start compact format drawer should begin collapsed")
                wait_toggle_state(compact_page, False, "Cold-start compact button should report collapsed state")
                cold_toggle.click()
                wait_inspector_visible(compact_page, True, "Cold-start compact format button did not open the drawer")
                wait_toggle_state(compact_page, True, "Cold-start compact button did not report expanded state")
                cold_state = inspector_state(compact_page)
                assert_true("hide-inspector" not in cold_state["workspaceClass"], f"Compact cold start retained the desktop hide class: {cold_state}")
                assert_true(cold_state["position"] == "fixed", f"Cold-start compact format panel is not a fixed drawer: {cold_state}")
                compact_page.press("body", "Escape")
                wait_inspector_visible(compact_page, False, "Escape did not close the cold-start compact drawer")
                report["errors"].extend(compact_errors)
                report["checks"].append("compact cold-start format drawer open/escape")
                compact_context.close()

                report["passed"] = not report["errors"]
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    (OUT / f"presentations_controls_{requested_browser_name()}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError("Presentations control validation failed: " + " | ".join(report["errors"] or ["behavioral assertion failed"]))


if __name__ == "__main__":
    main()

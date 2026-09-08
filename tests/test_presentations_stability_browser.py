#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8781
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1360, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p1Tools")

            # First-open gate and new-presentation bootstrap.
            assert page.locator("#startState").is_visible()
            page.click("#startNew")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.active && document.getElementById('startState').hidden"
            )
            initial = page.evaluate("() => globalThis.__inkdosPresentations.inspect()")
            assert initial["session"]["slideCount"] == 1, initial
            assert initial["session"]["currentIndex"] == 0, initial
            assert initial["view"]["panelOpen"] is True, initial

            # Controls are bindings; editing semantics live in the workspace command registry.
            command_ids = page.evaluate("() => globalThis.__inkdosPresentations.listCommands()")
            for command in (
                "history.undo",
                "history.redo",
                "slide.add",
                "slide.duplicate",
                "slide.delete",
                "slide.move",
                "edit.insertText",
                "navigation.previous",
                "navigation.next",
            ):
                assert command in command_ids, (browser_name, command, command_ids)
            assert page.locator("#undoBtn").get_attribute("data-command") == "history.undo"
            assert page.locator("#addSlideBtn").get_attribute("data-command") == "slide.add"

            # Slide structure operations must remain coherent with history.
            page.click("#addSlideBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 2")
            page.click("#duplicateSlideBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 3")
            page.click("#deleteSlideBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 2")

            page.click("#undoBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 3")
            page.evaluate("() => document.getElementById('redoBtn').remove()")
            redone = page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.redo')")
            assert redone is True
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 2")

            # Removing a toolbar control must not destroy the command or break state projection.
            page.evaluate("() => document.getElementById('addSlideBtn').remove()")
            added = page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('slide.add')")
            assert added is True
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 3")
            undone = page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.undo')")
            assert undone is True
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 2")

            # Navigation must update the authoritative session rather than only visual state.
            page.click("#prevSlideBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.currentIndex === 0")
            page.click("#nextSlideBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.currentIndex === 1")
            active_thumb = page.locator("#slidePanelInner .slide-thumb.active")
            assert active_thumb.count() == 1

            # Panel state and viewport layout survive repeated toggle cycles.
            page.click("#slidePanelBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.panel.isOpen === false")
            assert page.locator("#workspace").get_attribute("data-panel-open") == "false"
            page.click("#slidePanelBtn")
            page.wait_for_function("() => globalThis.__inkdosPresentations.panel.isOpen === true")
            assert page.locator("#workspace").get_attribute("data-panel-open") == "true"

            # Zoom is owned by the view controller and must remain usable after structure/panel operations.
            zoom_probe = page.evaluate(
                """() => {
                    const app = globalThis.__inkdosPresentations;
                    app.zoom.setPercent(150);
                    return {mode: app.zoom.mode, manual: app.zoom.manual, scale: app.zoom.scale};
                }"""
            )
            assert zoom_probe["mode"] == "manual", zoom_probe
            assert abs(zoom_probe["manual"] - 1.5) < 0.01, zoom_probe
            page.wait_for_function("() => Math.abs(globalThis.__inkdosPresentations.zoom.scale - 1.5) < 0.02")

            # Selection and insert-text behavior remain functional after navigation/history churn.
            page.click("#insertTextBtn")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations.selection.objectId")
            selected = page.evaluate(
                """() => {
                    const app = globalThis.__inkdosPresentations;
                    const o = app.selection.getObject(app.session);
                    return o ? {type:o.type, id:o.id, slideId:app.session.currentSlideId} : null;
                }"""
            )
            assert selected and selected["type"] == "text", selected

            final = page.evaluate("() => globalThis.__inkdosPresentations.inspect()")
            assert final["session"]["slideCount"] == 2, final
            assert final["session"]["currentIndex"] == 1, final
            assert final["session"]["selectedObjectId"], final
            assert final["view"]["panelOpen"] is True, final
            assert final["geometry"]["viewport"]["width"] > 0, final
            assert final["geometry"]["canvas"]["width"] > 0, final
            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"Presentations stability browser regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

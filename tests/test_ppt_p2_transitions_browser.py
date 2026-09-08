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
PORT = 8786
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
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p2Tools")
            page.click("#startNew")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.active && !document.getElementById('pptP2Transition').disabled"
            )

            app_probe = page.evaluate(
                """() => ({
                    commands: globalThis.__inkdosPresentations.listCommands(),
                    binding: document.getElementById('pptP2Transition')?.dataset.command || null,
                    value: document.getElementById('pptP2Transition')?.value || null
                })"""
            )
            assert "slide.transition.set" in app_probe["commands"], app_probe
            assert app_probe["binding"] == "slide.transition.set", app_probe
            assert app_probe["value"] == "none", app_probe

            # UI binding -> semantic command -> history.
            page.select_option("#pptP2Transition", "fade")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide.transition === 'fade'"
            )
            fade = page.evaluate(
                """() => {
                    const s=globalThis.__inkdosPresentations.session.currentSlide;
                    return {transition:s.transition,edited:s.transitionEdited,dirty:globalThis.__inkdosPresentations.session.dirty};
                }"""
            )
            assert fade == {"transition": "fade", "edited": True, "dirty": True}, fade

            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.undo')") is True
            page.wait_for_function(
                "() => (globalThis.__inkdosPresentations.session.currentSlide.transition || 'none') === 'none'"
            )
            assert page.locator("#pptP2Transition").input_value() == "none"
            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.redo')") is True
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide.transition === 'fade'"
            )

            # The control is only a binding: removing it must not remove the feature.
            page.evaluate("() => document.getElementById('pptP2Transition').remove()")
            changed = page.evaluate(
                "() => globalThis.__inkdosPresentations.executeCommand('slide.transition.set','push')"
            )
            assert changed is True
            assert page.evaluate(
                "() => globalThis.__inkdosPresentations.session.currentSlide.transition"
            ) == "push"

            # Model -> generated PPTX -> package transition -> readback.
            package_probe = page.evaluate(
                """async() => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const base=await NS.PptxWriter.build(app.session);
                    const out=await NS.PptP2Package.applySlideTransitions(app.session,base,{});
                    const zip=await JSZip.loadAsync(out,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    const values=await NS.PptP2Package.readSlideTransitions(out,['ppt/slides/slide1.xml']);
                    return {push:/<p:push(?:\s|\/|>)/.test(xml),value:values[0],bytes:out.length};
                }"""
            )
            assert package_probe["push"] is True, package_probe
            assert package_probe["value"] == "push", package_probe
            assert package_probe["bytes"] > 0, package_probe

            # Presentation mode applies the transition visually.
            assert page.evaluate(
                "() => globalThis.__inkdosPresentations.executeCommand('slide.transition.set','fade')"
            ) is True
            assert page.evaluate("() => globalThis.__inkdosPresentations.present(false)") is True
            page.wait_for_function("() => !!document.getElementById('presentHost').firstElementChild")
            animations = page.evaluate(
                "() => document.getElementById('presentHost').firstElementChild.getAnimations?.().length || 0"
            )
            assert animations >= 1, {"browser": browser_name, "animations": animations}
            page.click("[data-present-exit]")

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPT-P2 transition regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

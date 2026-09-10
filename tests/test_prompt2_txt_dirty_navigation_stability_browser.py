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
PORT = 8789
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
            page.goto(BASE + "/apps/txt/", wait_until="load")
            page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")

            page.click("#startNew")
            editor = page.locator("#editor")
            home = page.locator('a[aria-label="Home"]')
            assert home.count() == 1
            editor.fill("unsaved prompt 2 change")
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.session.dirty === true")

            # INKBUG-001: dirty in-app Home must stop before navigation and expose
            # one InkDOS-controlled Save / Discard / Cancel decision.
            home.click()
            assert page.url.endswith("/apps/txt/"), page.url
            assert page.locator("#discardDialog").is_visible()
            assert page.locator("#discardDialog").count() == 1
            assert page.locator("#discardSave").is_visible()
            assert page.locator("#discardContinue").is_visible()
            assert page.locator("#discardCancel").is_visible()

            # Repeated activation cannot create a second dialog or navigate early.
            page.evaluate("() => document.querySelector('a[aria-label=\"Home\"]').click()")
            assert page.locator("#discardDialog").count() == 1
            assert page.url.endswith("/apps/txt/"), page.url

            # Cancel keeps editor content and dirty state intact.
            page.click("#discardCancel")
            assert page.url.endswith("/apps/txt/"), page.url
            assert editor.input_value() == "unsaved prompt 2 change"
            assert page.evaluate("() => InkDOS2.TxtAppDebug.state.session.dirty") is True

            # Failed Save does not navigate, discard, or clear dirty state.
            page.evaluate(
                """() => {
                    InkDOS2.FileDelivery.deliver = async () => {
                        const e = new Error('synthetic write failure');
                        e.code = 'write-failed';
                        throw e;
                    };
                }"""
            )
            home.click()
            page.click("#discardSave")
            page.wait_for_function("() => document.getElementById('status').textContent.includes('synthetic write failure')")
            assert page.url.endswith("/apps/txt/"), page.url
            assert page.locator("#discardDialog").is_visible()
            assert page.evaluate("() => InkDOS2.TxtAppDebug.state.session.dirty") is True
            page.click("#discardCancel")

            # Save cancellation likewise keeps the editing context intact.
            page.evaluate(
                """() => {
                    InkDOS2.FileDelivery.deliver = async () => {
                        const e = new Error('synthetic cancellation');
                        e.code = 'cancelled';
                        throw e;
                    };
                }"""
            )
            home.click()
            page.click("#discardSave")
            page.wait_for_function("() => document.getElementById('status').textContent.includes('Save cancelled')")
            assert page.url.endswith("/apps/txt/"), page.url
            assert page.locator("#discardDialog").is_visible()
            assert page.evaluate("() => InkDOS2.TxtAppDebug.state.session.dirty") is True
            page.click("#discardCancel")

            # An async Save of an older revision must not clear a newer edit.
            page.evaluate(
                """() => {
                    let resolveDelivery;
                    InkDOS2.FileDelivery.deliver = () => new Promise(resolve => { resolveDelivery = resolve; });
                    globalThis.__resolvePrompt2Save = () => resolveDelivery({
                        fileName: 'Untitled.txt', method: 'file-system-access', deliveryConfirmed: true,
                        bytes: 1, sha256: 'b'.repeat(64),
                    });
                    globalThis.__prompt2Save = InkDOS2.TxtAppDebug.commands.execute('file.save');
                }"""
            )
            editor.fill("newer change while save is pending")
            page.evaluate("() => globalThis.__resolvePrompt2Save()")
            page.evaluate("() => globalThis.__prompt2Save")
            assert page.evaluate("() => InkDOS2.TxtAppDebug.state.session.dirty") is True

            # Successful Save of the current revision clears dirty and only then
            # permits the requested Home navigation.
            page.evaluate(
                """() => {
                    InkDOS2.FileDelivery.deliver = async (blob, fileName) => ({
                        fileName, method: 'file-system-access', deliveryConfirmed: true,
                        bytes: blob.size, sha256: 'a'.repeat(64),
                    });
                }"""
            )
            home.click()
            page.click("#discardSave")
            page.wait_for_url(BASE + "/index.html")

            # Re-enter, dirty again, and verify explicit Discard proceeds without saving.
            page.goto(BASE + "/apps/txt/", wait_until="load")
            page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")
            page.click("#startNew")
            page.locator("#editor").fill("discard me")
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.session.dirty === true")
            page.locator('a[aria-label="Home"]').click()
            page.click("#discardContinue")
            page.wait_for_url(BASE + "/index.html")

            # Clean Home navigation is immediate and does not show an unnecessary prompt.
            page.goto(BASE + "/apps/txt/", wait_until="load")
            page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")
            page.locator('a[aria-label="Home"]').click()
            page.wait_for_url(BASE + "/index.html")

            browser.close()

        if errors:
            raise AssertionError("Browser runtime errors:\n" + "\n".join(errors))
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    main()

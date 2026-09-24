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
PORT = 8803
BASE = f"http://127.0.0.1:{PORT}"


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")


def recovery_key(page, errors: list[str]) -> str:
    try:
        page.wait_for_function("() => document.body?.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")
    except Exception:
        state = page.evaluate("""() => ({
          url: location.href,
          ready: document.readyState,
          runtimeReady: document.body?.dataset.runtimeReady || null,
          hasNamespace: !!globalThis.InkDOS2,
          hasDebug: !!globalThis.InkDOS2?.TxtAppDebug,
          tabId: sessionStorage.getItem('inkdos2:txt:recovery-tab')
        })""")
        raise AssertionError({"runtime": state, "errors": errors})
    key = page.evaluate("async () => { await globalThis.InkDOS2.TxtAppDebug.recoveryReady(); return globalThis.InkDOS2.TxtAppDebug.recoveryKey(); }")
    assert isinstance(key, str) and key, {"key": key, "errors": errors}
    return key


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
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context()

            errors: list[str] = []
            first = context.new_page()
            first.on("pageerror", lambda exc: errors.append(f"first pageerror: {exc}"))
            first.on("console", lambda msg: errors.append(f"first console.error: {msg.text}") if msg.type == "error" else None)
            first.goto(BASE + "/apps/txt/", wait_until="load")
            first_key = recovery_key(first, errors)

            # window.open inherits same-origin sessionStorage in the new browsing
            # context. The recovery identity handshake must detect that clone
            # and fork the second live instance before either writes a checkpoint.
            with context.expect_page() as opened:
                first.evaluate("() => window.open('/apps/txt/', '_blank')")
            second = opened.value
            second.on("pageerror", lambda exc: errors.append(f"second pageerror: {exc}"))
            second.on("console", lambda msg: errors.append(f"second console.error: {msg.text}") if msg.type == "error" else None)
            second.wait_for_load_state("load")
            inherited = second.evaluate("() => sessionStorage.getItem('inkdos2:txt:recovery-tab')")
            assert inherited == first_key.split('txt:tab:', 1)[1], {
                "first": first_key,
                "inherited": inherited,
                "reason": "test precondition: opener tab must clone the original sessionStorage identity",
            }
            second_key = recovery_key(second, errors)
            assert first_key.startswith("txt:tab:"), first_key
            assert second_key.startswith("txt:tab:"), second_key
            assert first_key != second_key, {
                "first": first_key,
                "second": second_key,
                "reason": "two Plain Text tabs must not share recovery checkpoints",
            }

            first.reload(wait_until="load")
            assert recovery_key(first, errors) == first_key, {
                "before": first_key,
                "after": recovery_key(first, errors),
                "reason": "a tab recovery identity must survive reload in the same tab",
            }

            third_context = browser.new_context()
            third = third_context.new_page()
            third.on("pageerror", lambda exc: errors.append(f"third pageerror: {exc}"))
            third.on("console", lambda msg: errors.append(f"third console.error: {msg.text}") if msg.type == "error" else None)
            third.goto(BASE + "/apps/txt/", wait_until="load")
            third_key = recovery_key(third, errors)
            assert third_key not in {first_key, second_key}, {
                "first": first_key,
                "second": second_key,
                "third": third_key,
            }

            assert not errors, errors
            third_context.close()
            context.close()
            browser.close()

        print(f"Plain Text multi-instance recovery isolation ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

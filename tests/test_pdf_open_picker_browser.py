#!/usr/bin/env python3
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8794
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "webkit").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1024, "height": 768})
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")

            # Safari/WebKit can reject fileInput.click() once the original user
            # gesture crosses an async boundary. dispatchEvent() itself is
            # synchronous, so record whether InkDOS requests the picker before
            # that dispatch returns rather than inferring timing from microtasks.
            timing = page.evaluate(
                r"""() => {
                    const button = document.querySelector('#openStartBtn');
                    const input = document.querySelector('#fileInput');
                    const state = { dispatching: true, clicks: 0, clickPhase: null };
                    window.__pdfOpenTiming = state;
                    input.click = () => {
                        state.clicks += 1;
                        state.clickPhase = state.dispatching ? 'sync' : 'async';
                    };
                    button.dispatchEvent(new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                    }));
                    state.dispatching = false;
                    return {...state};
                }"""
            )
            page.wait_for_timeout(50)
            after = page.evaluate("() => ({...window.__pdfOpenTiming})")
            assert timing["clicks"] == 1, timing
            assert timing["clickPhase"] == "sync", (
                f"Open PDF picker crossed an async boundary on {browser_name}: {timing}"
            )
            assert after["clicks"] == 1, after
            browser.close()
        print(f"PDF Open picker user-gesture regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

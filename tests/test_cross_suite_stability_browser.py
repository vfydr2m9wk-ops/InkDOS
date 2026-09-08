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
PORT = 8785
BASE = f"http://127.0.0.1:{PORT}"
WORKSPACES = (
    ("pdf", "/apps/pdf/", "() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug"),
    ("documents", "/apps/documents/", "() => !!globalThis.InkDOS2Documents?.DocumentsDebug?.executeCommand"),
    ("presentations", "/apps/presentations/", "() => !!globalThis.__inkdosPresentations?.p1Tools"),
    ("txt", "/apps/txt/", "() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug"),
    ("epub", "/apps/epub/", "() => !!globalThis.__InkEpubR4"),
    ("spreadsheets", "/apps/spreadsheets/", "() => !!globalThis.__inkdosSpreadsheetsS1"),
)


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local cross-suite test server did not start")


def stop_server(server: subprocess.Popen | None) -> None:
    if server is None or server.poll() is not None:
        return
    server.terminate()
    try:
        server.wait(timeout=3)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=3)


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    server: subprocess.Popen | None = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    phase = "bootstrap"
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1360, "height": 900})
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"{phase} pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"{phase} console.error: {msg.text}") if msg.type == "error" else None,
            )

            # Install the root service worker and wait until this client is controlled.
            page.goto(BASE + "/index.html", wait_until="load")
            assert page.evaluate("() => 'serviceWorker' in navigator") is True, browser_name
            page.evaluate("async () => { await navigator.serviceWorker.ready; return true; }")
            page.reload(wait_until="load")
            page.wait_for_function("() => !!navigator.serviceWorker.controller", timeout=15_000)
            if errors:
                raise AssertionError("\n".join(errors))

            # Online sweep: every workspace must bootstrap independently with the shared shell active.
            for name, path, ready in WORKSPACES:
                phase = f"online:{name}"
                errors.clear()
                page.goto(BASE + path, wait_until="load", timeout=20_000)
                page.wait_for_function(ready, timeout=15_000)
                probe = page.evaluate(
                    """() => ({
                        controlled:!!navigator.serviceWorker.controller,
                        title:document.title,
                        body:!!document.body,
                        localScripts:[...document.scripts].every(s => !s.src || new URL(s.src, location.href).origin === location.origin),
                        localStyles:[...document.querySelectorAll('link[rel="stylesheet"]')].every(l => !l.href || new URL(l.href, location.href).origin === location.origin),
                    })"""
                )
                assert probe["controlled"] is True, (browser_name, name, probe)
                assert probe["body"] is True and bool(probe["title"].strip()), (browser_name, name, probe)
                assert probe["localScripts"] is True and probe["localStyles"] is True, (browser_name, name, probe)
                if errors:
                    raise AssertionError("\n".join(errors))

            # Remove the origin. All subsequent navigations must be satisfied by the root
            # service worker and each workspace must execute a fresh bootstrap from cache.
            stop_server(server)
            server = None

            for name, path, ready in WORKSPACES:
                phase = f"offline:{name}"
                errors.clear()
                page.goto(BASE + path, wait_until="load", timeout=20_000)
                page.wait_for_function(ready, timeout=15_000)
                offline = page.evaluate(
                    """() => ({
                        controlled:!!navigator.serviceWorker.controller,
                        body:!!document.body,
                        title:document.title,
                        readyState:document.readyState,
                    })"""
                )
                assert offline["controlled"] is True, (browser_name, name, offline)
                assert offline["body"] is True and offline["readyState"] == "complete", (browser_name, name, offline)
                assert bool(offline["title"].strip()), (browser_name, name, offline)
                if errors:
                    raise AssertionError("\n".join(errors))

            browser.close()

        print(f"Cross-suite browser ({browser_name}): OK")
    finally:
        stop_server(server)


if __name__ == "__main__":
    main()

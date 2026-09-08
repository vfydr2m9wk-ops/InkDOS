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
PORT = 8777
BASE = f"http://127.0.0.1:{PORT}"

PDF_DYNAMIC_URLS = (
    "/apps/pdf/runtime/commands/command-registry.js",
    "/apps/pdf/ui/command-bindings.js",
    "/apps/pdf/ui/toolbar-rail.js",
    "/apps/pdf/ui/mode-bindings.js",
    "/apps/pdf/features/page-tools/page-tools-runtime.js",
    "/apps/pdf/features/page-tools/actions/move-page.js",
    "/apps/pdf/features/page-tools/actions/rotate-page.js",
    "/apps/pdf/features/page-tools/actions/delete-page.js",
    "/apps/pdf/features/page-tools/actions/extract-page.js",
    "/apps/pdf/features/page-tools/actions/split-pdf.js",
    "/apps/pdf/features/page-tools/actions/merge-pdfs.js",
)

def wait_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")

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
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            browser_type = getattr(pw, browser_name)
            browser = browser_type.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"console.error: {msg.text}")
                if msg.type == "error"
                else None,
            )

            # Install and activate the root suite service worker.
            page.goto(BASE + "/index.html", wait_until="load")
            supported = page.evaluate("() => 'serviceWorker' in navigator")
            assert supported is True, browser_name
            page.evaluate("async () => { await navigator.serviceWorker.ready; return true; }")
            page.reload(wait_until="load")
            page.wait_for_function("() => !!navigator.serviceWorker.controller")

            # Load PDF once online, then prove the dynamic modular assets are in the
            # active InkDOS cache rather than merely available from the network.
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            missing = page.evaluate(
                r"""async (paths) => {
                    const names = (await caches.keys()).filter(name => name.startsWith('inkdos-'));
                    const cachesForInkDOS = await Promise.all(names.map(name => caches.open(name)));
                    const missing = [];
                    for (const path of paths) {
                        const url = new URL(path, location.origin).href;
                        let hit = false;
                        for (const cache of cachesForInkDOS) {
                            if (await cache.match(url)) { hit = true; break; }
                        }
                        if (!hit) missing.push(path);
                    }
                    return missing;
                }""",
                list(PDF_DYNAMIC_URLS),
            )
            assert missing == [], (browser_name, missing)

            # Simulate a real network outage by taking down the origin server. This
            # avoids Playwright WebKit's context.set_offline()/reload internal error
            # while making the assertion stricter: no origin request can succeed.
            errors.clear()
            stop_server(server)
            server = None
            page.reload(wait_until="load", timeout=20_000)
            page.wait_for_function(
                "() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug",
                timeout=15_000,
            )
            offline = page.evaluate(
                r"""() => {
                    const ns = globalThis.InkDOS2PdfP4;
                    const d = ns.PdfStabilityDebug;
                    const commands = d.registry.inspect().commands;
                    return {
                        registry: !!ns.CommandRegistry,
                        bindings: !!ns.CommandBindings,
                        toolbarRail: !!ns.ToolbarRail,
                        modeBindings: !!ns.ModeBindings,
                        pageToolsRuntime: !!ns.PageToolsRuntime,
                        pageActions: [
                            'PageMoveAction',
                            'PageRotateAction',
                            'PageDeleteAction',
                            'PageExtractAction',
                            'PageSplitAction',
                            'PageMergeAction',
                        ].every(name => !!ns[name]),
                        undo: commands.includes('history.undo'),
                        deleteAnnotation: commands.includes('annotation.delete'),
                    };
                }"""
            )
            assert all(offline.values()), (browser_name, offline)
            if errors:
                raise AssertionError({"browser": browser_name, "errors": errors})

            browser.close()

        print(f"PDF offline modular boot regression passed on {browser_name}.")
    finally:
        stop_server(server)

if __name__ == "__main__":
    main()

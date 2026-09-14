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
PORT = 8784
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local Goal 4 test server did not start")


def main() -> int:
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
        wait_port(PORT)
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/index.html", wait_until="load")

            # Ordinary web/PWA Home must remain updater-free and make no updater call.
            assert page.locator("#inkdosUpdateButton").count() == 0
            assert page.locator("#inkdosDesktopUpdateModal").count() == 0

            page.evaluate(
                r"""() => {
                    window.__goal4Calls = [];
                    window.__goal4Response = {
                        available: false,
                        currentVersion: '2.3.0',
                        latestVersion: '2.3.0',
                        notes: null,
                        pubDate: null
                    };
                    window.__TAURI__ = {
                        dialog: {
                            open: async () => null,
                            save: async () => null,
                            message: async () => null
                        },
                        fs: {
                            readFile: async () => new Uint8Array(),
                            writeFile: async () => null
                        },
                        opener: { openUrl: async () => null },
                        core: {
                            invoke: async (command, args) => {
                                window.__goal4Calls.push({command, args: args || null});
                                if (command === 'inkdos_check_for_updates') return {...window.__goal4Response};
                                if (command === 'inkdos_install_update') return null;
                                throw new Error(`Unexpected command: ${command}`);
                            }
                        }
                    };
                }"""
            )
            page.add_script_tag(path=str(ROOT / "desktop" / "desktop-host.js"))
            page.wait_for_selector("#inkdosUpdateButton")

            # Loading the desktop bridge alone must not perform a network-backed updater invocation.
            assert page.evaluate("() => window.__goal4Calls.length") == 0
            assert page.get_by_role("button", name="Check for updates").count() == 1

            # Current version path: only explicit click checks, and it reports current/latest clearly.
            page.get_by_role("button", name="Check for updates").click()
            page.wait_for_function(
                "() => document.querySelector('[data-update-status]')?.textContent === \"You're using the latest version.\""
            )
            calls = page.evaluate("() => window.__goal4Calls")
            assert [item["command"] for item in calls] == ["inkdos_check_for_updates"]
            versions = page.locator("[data-update-versions]").inner_text()
            assert "Installed" in versions and "2.3.0" in versions and "Latest" in versions
            page.locator("[data-update-cancel]").click()

            # Available update path: notes are rendered as text and Cancel never installs.
            page.evaluate(
                r"""() => {
                    window.__goal4Response = {
                        available: true,
                        currentVersion: '2.3.0',
                        latestVersion: '2.3.1',
                        notes: '<img src=x onerror="window.__goal4Injected=true">Important fixes',
                        pubDate: '2026-09-14T00:00:00Z'
                    };
                }"""
            )
            page.get_by_role("button", name="Check for updates").click()
            page.wait_for_function("() => !document.querySelector('[data-update-install]')?.hidden")
            assert "InkDOS 2.3.1 is available." in page.locator("[data-update-status]").inner_text()
            assert "Important fixes" in page.locator("[data-update-notes]").inner_text()
            assert page.locator("#inkdosDesktopUpdateModal img").count() == 0
            assert page.evaluate("() => window.__goal4Injected === true") is False
            before_cancel = page.evaluate("() => window.__goal4Calls.length")
            page.locator("[data-update-cancel]").click()
            assert page.evaluate("() => window.__goal4Calls.length") == before_cancel

            # A second explicit check followed by explicit Install is the only install path.
            page.get_by_role("button", name="Check for updates").click()
            page.wait_for_function("() => !document.querySelector('[data-update-install]')?.hidden")
            page.locator("[data-update-install]").click()
            page.wait_for_function(
                "() => document.querySelector('[data-update-status]')?.textContent.includes('was installed')"
            )
            calls = page.evaluate("() => window.__goal4Calls")
            install_calls = [item for item in calls if item["command"] == "inkdos_install_update"]
            assert len(install_calls) == 1
            assert install_calls[0]["args"] == {"expectedVersion": "2.3.1"}

            if errors:
                raise AssertionError({"browser": browser_name, "errors": errors})
            browser.close()

        print(f"Goal 4 manual updater UI regression passed on {browser_name}.")
        return 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())

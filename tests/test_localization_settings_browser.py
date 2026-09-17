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
PORT = 8814
BASE = f"http://127.0.0.1:{PORT}"
WORKSPACES = [
    ("documents", "/apps/documents/index.html?suite=1"),
    ("spreadsheets", "/apps/spreadsheets/index.html?suite=1"),
    ("presentations", "/apps/presentations/index.html?suite=1"),
    ("pdf", "/apps/pdf/index.html?suite=1"),
    ("epub", "/apps/epub/index.html?suite=1"),
    ("txt", "/apps/txt/index.html?suite=1"),
]


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")


def snapshot_functional_attributes(page):
    return page.evaluate("""()=>Array.from(document.querySelectorAll('[id],[data-action],[data-cmd],[data-command]')).map(el=>({
      tag:el.tagName,
      id:el.id||'',
      action:el.getAttribute('data-action')||'',
      cmd:el.getAttribute('data-cmd')||'',
      command:el.getAttribute('data-command')||''
    }))""")


def open_menu(page) -> None:
    page.locator("#menuBtn").click()
    page.wait_for_function("() => { const d=document.querySelector('#generalMenu,aside.drawer'); return !!d && !d.hidden; }")


def choose_language(page, label: str, code: str) -> None:
    if page.locator("[data-settings-item='language']").count() == 0:
        raise AssertionError("Language settings button missing")
    page.locator("[data-settings-item='language']").click()
    popover = page.locator(".inkdos-settings-popover")
    popover.locator("button", has_text=label).click()
    page.wait_for_function(f"() => globalThis.InkDOSLocalization?.currentLanguage === {code!r}")


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
            context = browser.new_context(viewport={"width": 1280, "height": 820})
            page = context.new_page()

            # All six workspaces receive the same compact order through the shared presentation layer.
            for app, path in WORKSPACES:
                page.goto(BASE + path, wait_until="load")
                page.wait_for_function("() => !!globalThis.InkDOSSettingsStrip && !!document.querySelector('.inkdos-settings-strip')")
                state = page.evaluate("""()=>({
                  items:Array.from(document.querySelectorAll('.inkdos-settings-strip [data-settings-item]')).map(x=>x.dataset.settingsItem),
                  languageKey:globalThis.InkDOSSettingsStrip.languageStorageKey,
                  densityKey:globalThis.InkDOSUiDensity.STORAGE_KEY,
                  count:document.querySelectorAll('.inkdos-settings-strip').length
                })""")
                assert state["items"] == ["appearance", "interface", "language", "help"], (app, state)
                assert state["languageKey"] == f"inkdos2:{app}:language", (app, state)
                assert state["densityKey"] == f"inkdos2:{app}:ui-density", (app, state)
                assert state["count"] == 1, (app, state)

            # Translation is presentation-only: IDs/actions/commands and editable name remain unchanged.
            page.goto(BASE + WORKSPACES[0][1], wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOSSettingsStrip")
            open_menu(page)
            before = snapshot_functional_attributes(page)
            title_before = page.locator("#titleText").input_value()

            for label, code in [("Português", "pt-BR"), ("Русский", "ru"), ("中文（简体）", "zh-CN"), ("日本語", "ja")]:
                choose_language(page, label, code)
                after = snapshot_functional_attributes(page)
                assert after == before, (code, "functional identifiers changed")
                assert page.locator("#titleText").input_value() == title_before, (code, "user/file name changed")
                resident = page.evaluate("""()=>Array.from(document.querySelectorAll('script[id^="inkdosLocalePackage-"]')).map(x=>x.id)""")
                assert resident == [f"inkdosLocalePackage-{code}"], (code, resident)
                bounds = page.evaluate("""()=>Array.from(document.querySelectorAll('.inkdos-settings-strip [data-settings-item]')).map(x=>{const r=x.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})""")
                for rect in bounds:
                    assert rect["left"] >= -1 and rect["right"] <= 1281, (code, rect)
                    assert rect["top"] >= -1 and rect["bottom"] <= 821, (code, rect)

            choose_language(page, "English", "en")
            assert page.evaluate("() => document.querySelectorAll('script[id^=\"inkdosLocalePackage-\"]').length") == 0
            assert snapshot_functional_attributes(page) == before

            # Language and interface preferences are independent between workspaces.
            choose_language(page, "Português", "pt-BR")
            page.evaluate("() => globalThis.InkDOSUiDensity.set('mobile')")
            assert page.evaluate("() => localStorage.getItem('inkdos2:documents:language')") == "pt-BR"
            assert page.evaluate("() => localStorage.getItem('inkdos2:documents:ui-density')") == "mobile"

            page.goto(BASE + "/apps/spreadsheets/index.html?suite=1", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOSSettingsStrip && !!globalThis.InkDOSLocalization")
            assert page.evaluate("() => globalThis.InkDOSLocalization.currentLanguage") == "en"
            assert page.evaluate("() => globalThis.InkDOSUiDensity.preference") == "auto"

            page.goto(BASE + "/apps/documents/index.html?suite=1", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOSSettingsStrip && globalThis.InkDOSLocalization?.currentLanguage === 'pt-BR'")
            assert page.evaluate("() => globalThis.InkDOSUiDensity.preference") == "mobile"

            context.close()
            browser.close()
        print(f"InkDOS 2.4 localization/settings browser ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

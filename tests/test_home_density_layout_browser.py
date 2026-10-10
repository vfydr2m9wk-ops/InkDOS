#!/usr/bin/env python3
"""Home keeps no Interface (density) choice since 2026-10-10 (owner): the Appearance menu fits the window at Windows
100/125/150% scale and on a phone, shows no Auto/Desktop/Smartphone control, and the page uses the desktop density."""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8784
BASE = f"http://127.0.0.1:{PORT}"


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Home test server did not start")


def inspect(page):
    page.goto(BASE + "/index.html", wait_until="load")
    page.click("#appearanceButton")
    page.wait_for_selector("#appearanceMenu:not([hidden])")
    data = page.evaluate("""()=>{const r=document.getElementById('appearanceMenu').getBoundingClientRect();return {
      controls:document.querySelectorAll('[data-inkdos-density-control],[data-inkdos-density-mode]').length,
      density:document.documentElement.dataset.uiDensity,left:r.left,right:r.right}}""")
    assert data["controls"] == 0, data
    assert data["density"] == "desktop", data
    assert data["left"] >= 0 and data["right"] <= page.viewport_size["width"], data


def main():
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for scale in (1.0, 1.25, 1.5):
                context = browser.new_context(viewport={"width": round(1280 / scale), "height": round(900 / scale)}, device_scale_factor=scale)
                inspect(context.new_page())
                context.close()
            context = browser.new_context(viewport={"width": 390, "height": 844})
            inspect(context.new_page())
            context.close(); browser.close()
        print("Home Appearance menu without an Interface choice: OK at Windows 100%, 125%, 150% and on a phone.")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()


if __name__ == "__main__": main()

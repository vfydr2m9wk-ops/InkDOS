#!/usr/bin/env python3
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


def assert_no_overlap(rects):
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            separated = (a["right"] <= b["left"] or b["right"] <= a["left"] or a["bottom"] <= b["top"] or b["bottom"] <= a["top"])
            assert separated, (a, b)


def inspect(page):
    page.goto(BASE + "/index.html", wait_until="load")
    page.click("#appearanceButton")
    page.wait_for_selector("#appearanceMenu:not([hidden])")
    data = page.evaluate("""()=>{
      const buttons=[...document.querySelectorAll('.home-density-control [data-inkdos-density-mode]')];
      return {
        labels:buttons.map(x=>x.textContent.trim()), modes:buttons.map(x=>x.dataset.inkdosDensityMode),
        rects:buttons.map(x=>{const r=x.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}}),
        icons:buttons.map(x=>{const svg=x.querySelector('.inkdos-density-icon');if(!svg)return null;const r=svg.getBoundingClientRect();return {width:r.width,height:r.height}}),
        menu:(()=>{const r=document.getElementById('appearanceMenu').getBoundingClientRect();return {left:r.left,right:r.right,width:r.width}})()
      };
    }""")
    assert data["labels"] == ["Auto", "Desktop", "Smartphone"], data
    assert data["modes"] == ["auto", "desktop", "mobile"], data
    assert data["icons"][0] is None, data
    for icon in data["icons"][1:]: assert 12 <= icon["width"] <= 16 and 12 <= icon["height"] <= 16, data
    assert_no_overlap(data["rects"])
    assert data["menu"]["left"] >= 0 and data["menu"]["right"] <= page.viewport_size["width"], data
    return data


def inspect_desktop_scale(browser, scale):
    # Deterministic CSS/device-pixel scaling coverage analogous to Windows
    # 100/125/150%. Native WebView2/device validation remains a release gate.
    context = browser.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=scale)
    try:
        data = inspect(context.new_page())
        assert len({round(r["top"], 1) for r in data["rects"]}) == 1, (scale, data)
        heights = [r["height"] for r in data["rects"]]
        assert max(heights) - min(heights) <= 1, (scale, data)
        return data
    finally:
        context.close()


def main():
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            scaled = {scale: inspect_desktop_scale(browser, scale) for scale in (1.0, 1.25, 1.5)}
            baseline = [r["width"] for r in scaled[1.0]["rects"]]
            for scale, data in scaled.items():
                widths = [r["width"] for r in data["rects"]]
                for expected, actual in zip(baseline, widths): assert abs(actual - expected) <= 1, (scale, baseline, widths, data)
            context = browser.new_context(viewport={"width": 390, "height": 844})
            n = inspect(context.new_page())
            tops = [r["top"] for r in n["rects"]]
            assert tops[0] < tops[1] < tops[2], n
            context.close(); browser.close()
        print("Home 2.4.3 density layout browser regression passed at 100%, 125%, and 150% scale.")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()


if __name__ == "__main__": main()

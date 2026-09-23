#!/usr/bin/env python3
from __future__ import annotations
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8793
BASE = f"http://127.0.0.1:{PORT}"

SHELLS = {
    "documents": ("#formatbar", "#viewport"),
    "spreadsheets": ("#formatbar", "#contentViewport"),
    "presentations": ("#editbar", "#viewport"),
    "pdf": ("#editbar", "#contentViewport"),
    "txt": ("#toolbar", "#surface"),
    "epub": ("#toolbar", "#contentViewport"),
}

def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("local server did not start")

def positive_box(page, selector):
    box = page.locator(selector).bounding_box()
    assert box and box["width"] > 1 and box["height"] > 1, (selector, box)

def presentation_probe(page):
    page.click("#startNew")
    page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session?.active")
    page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('slide.add')")
    page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('slide.add')")
    page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 3")
    page.wait_for_timeout(200)
    probe = page.evaluate("""() => {
      const q=id=>document.getElementById(id);
      const rect=e=>{const r=e.getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
      const canvas=rect(q('slideCanvas')), viewport=rect(q('viewport'));
      const thumbs=[...q('slidePanelInner').querySelectorAll('.slide-thumb')].map(rect);
      const x=(canvas.left+canvas.right)/2, y=(canvas.top+canvas.bottom)/2;
      const hit=document.elementFromPoint(x,y);
      return {
        slideCount: globalThis.__inkdosPresentations.session.slides.length,
        canvas, viewport, thumbs,
        canvasPainted: !!hit && (hit===q('slideCanvas') || q('slideCanvas').contains(hit))
      };
    }""")
    assert probe["slideCount"] == 3, probe
    c, v = probe["canvas"], probe["viewport"]
    assert c["width"] > 100 and c["height"] > 60, probe
    assert c["right"] > v["left"] and c["left"] < v["right"], probe
    assert c["bottom"] > v["top"] and c["top"] < v["bottom"], probe
    assert len(probe["thumbs"]) == 3, probe
    assert any(t["width"] > 40 and t["height"] > 30 for t in probe["thumbs"]), probe
    assert probe["canvasPainted"] is True, probe

def main():
    engine = sys.argv[1] if len(sys.argv) > 1 else "chromium"
    if engine not in {"chromium", "webkit"}:
        raise SystemExit("usage: test_workspace_smoke_browser.py [chromium|webkit]")
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, engine).launch(headless=True)
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=3 if engine == "webkit" else 1,
                is_mobile=(engine == "webkit"),
                has_touch=(engine == "webkit"),
            )
            for app, (toolbar, surface) in SHELLS.items():
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda exc, bucket=errors: bucket.append(str(exc)))
                page.goto(f"{BASE}/apps/{app}/", wait_until="load")
                positive_box(page, toolbar)
                positive_box(page, surface)
                assert not errors, (app, errors)
                if app == "presentations":
                    presentation_probe(page)
                page.close()
            context.close()
            browser.close()
        print(f"Workspace rendered smoke passed in {engine}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

if __name__ == "__main__":
    main()

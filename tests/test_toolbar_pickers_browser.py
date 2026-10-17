#!/usr/bin/env python3
"""Tool bar pickers of Documents, Presentations and Spreadsheets in a browser (owner, 2026-10-15).

Each picker is a fixed box: icon pickers 28px wide with their icon, value pickers (font size, Functions) showing the
chosen value, and the real dropdown invisible on top, at least 260px wide so its list is not cut. The boxes keep that
look in light and dark, before and after a new file is opened, and when the host restyles native dropdowns and adds
its own control next to them the way XeOS does.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8797
BASE = f"http://127.0.0.1:{PORT}"
APPS = {
    "documents": "#formatbar",
    "presentations": "#editbar",
    "spreadsheets": "#formatbar",
}
# XeOS draws native dropdowns its own way after the page loads: wide, dark, with a control of its own beside them
HOST_RESTYLE = """
select{width:160px!important;max-width:none!important;min-width:160px!important;background:#000!important;
color:#fff!important;-webkit-appearance:auto!important;appearance:auto!important}
"""
HOST_EXTRA = """() => { for (const s of document.querySelectorAll('.inkdos-picker>select')) {
  const extra = document.createElement('span'); extra.className = 'host-extra'; extra.textContent = 'Host menu';
  extra.style.cssText = 'display:inline-block;width:140px;height:30px;background:#000;color:#fff';
  s.after(extra);
} }"""
MEASURE = """bar => {
  const bar_ = document.querySelector(bar);
  const boxes = [...document.querySelectorAll('.inkdos-picker')].filter(w => w.offsetParent && bar_?.contains(w) || w.dataset.for === 'functionSelect');
  return boxes.map(w => {
    const s = w.querySelector(':scope>select'), r = w.getBoundingClientRect(), sr = s.getBoundingClientRect();
    const label = w.querySelector(':scope>.inkdos-picker-label');
    const center = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    const cs = getComputedStyle(w);
    return {
      id: w.dataset.for, value: w.classList.contains('inkdos-value-picker'), width: r.width, height: r.height,
      icon: cs.backgroundImage.startsWith('url('), selectOpacity: getComputedStyle(s).opacity, selectWidth: sr.width,
      label: label ? label.textContent : null,
      chosen: s.options[s.selectedIndex] ? s.options[s.selectedIndex].textContent : s.value,
      labelMiddle: label ? Math.abs((label.getBoundingClientRect().top + label.getBoundingClientRect().height / 2) - (r.top + r.height / 2)) : 0,
      hitsSelect: center === s || (w.contains(center) && center !== label && center !== w), extrasVisible: [...w.children].filter(c => c !== s && c !== label && getComputedStyle(c).opacity !== '0').length,
    };
  });
}"""


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("tool bar picker test server did not start")


def check(boxes, where):
    assert boxes, f"{where}: no picker boxes in the tool bar"
    for box in boxes:
        tag = f"{where} {box['id']}"
        assert box["selectOpacity"] == "0", f"{tag}: the dropdown shows ({box})"
        assert box["selectWidth"] >= 260, f"{tag}: the dropdown list would be cut ({box})"
        assert box["extrasVisible"] == 0, f"{tag}: a host control shows in the box ({box})"
        assert box["hitsSelect"], f"{tag}: a tap on the box reaches neither the dropdown nor the host control in its place ({box})"
        if box["value"]:
            assert box["width"] >= 44 and box["width"] < 200, f"{tag}: value box size {box}"
            assert box["label"] == box["chosen"], f"{tag}: the box does not show the chosen value ({box})"
            assert box["labelMiddle"] <= 2, f"{tag}: the value is not vertically centred ({box})"
        else:
            assert box["width"] == 28 and box["height"] == 28, f"{tag}: icon box size {box}"
            assert box["icon"], f"{tag}: the icon is missing ({box})"


def run(page, app, theme):
    bar = APPS[app]
    page.add_init_script(f"try{{localStorage.setItem('inkdos2:appearance','{theme}')}}catch(e){{}}")
    page.goto(f"{BASE}/apps/{app}/index.html")
    page.wait_for_selector(f"{bar} .inkdos-picker")
    page.wait_for_timeout(600)
    check(page.evaluate(MEASURE, bar), f"{app} {theme} start")
    page.click("#startNew")
    page.wait_for_timeout(1200)
    check(page.evaluate(MEASURE, bar), f"{app} {theme} new file")
    page.add_style_tag(content=HOST_RESTYLE)
    page.evaluate(HOST_EXTRA)
    page.wait_for_timeout(700)
    check(page.evaluate(MEASURE, bar), f"{app} {theme} host restyle")


def main():
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for app in APPS:
                for theme in ("light", "dark"):
                    context = browser.new_context(viewport={"width": 1440, "height": 900}, service_workers="block")
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    run(page, app, theme)
                    if app == "documents":
                        # a new value shows in the box at once
                        page.select_option("#sizeSelect", "14")
                        page.wait_for_timeout(100)
                        assert page.text_content('.inkdos-picker[data-for="sizeSelect"] .inkdos-picker-label') == "14"
                    assert not errors, f"{app} {theme}: {errors}"
                    context.close()
            browser.close()
        print("Tool bar pickers keep the 2.8 look, full-width lists and host restyles in Documents, Presentations and Spreadsheets.")
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()

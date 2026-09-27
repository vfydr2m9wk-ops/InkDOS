#!/usr/bin/env python3
"""Presentations matches the Documents reference on an iPad-class touch viewport (audit V6/V8):
same top-bar height and the same frame tokens. The toolbar-button geometry is deliberately not
compared: 2.5.2 restored the 2.5.0 Presentations toolbar (test_252_presentations_hotfix_contract)."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8850
BASE = f"http://127.0.0.1:{PORT}"
UA = "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
PROBE = r"""(sel) => {
  const vis = e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.display !== 'none' && c.visibility !== 'hidden' };
  const header = [...document.querySelectorAll('header')].find(vis);
  const root = getComputedStyle(document.documentElement);
  const tokens = {};
  for (const name of ['--safe-t', '--safe-b', '--safe-l', '--safe-r', '--chrome', '--muted', '--line', '--line-strong'])
    tokens[name] = root.getPropertyValue(name).trim();
  return {header: Math.round(header.getBoundingClientRect().height), tokens};
}"""
APPS = ("documents", "presentations")

def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")

def main():
    browser_name = os.environ.get("BROWSER", "chromium")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            found = {}
            for app in APPS:
                ctx = browser.new_context(viewport={"width": 1180, "height": 820}, is_mobile=True, has_touch=True, user_agent=UA)
                page = ctx.new_page()
                page.goto(f"{BASE}/apps/{app}/", wait_until="load")
                page.click("#startNew")
                page.wait_for_timeout(900)
                found[app] = page.evaluate(PROBE, None)
                ctx.close()
            browser.close()
        ref, got = found["documents"], found["presentations"]
        assert got["header"] == ref["header"], found
        assert got["tokens"] == ref["tokens"], found
        print(f"Presentations iPad visual consistency ({browser_name}): OK {got}")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    main()

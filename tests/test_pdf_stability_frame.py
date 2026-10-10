#!/usr/bin/env python3
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=8779;BASE=f"http://127.0.0.1:{PORT}"
def wait_port(port,timeout=10.0):
    deadline=time.time()+timeout
    while time.time()<deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1",port))==0:return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")
def main():
    browser_name=os.environ.get("BROWSER","chromium").strip().lower()
    if browser_name not in {"chromium", "webkit"}:raise RuntimeError(f"Unsupported BROWSER={browser_name}")
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    errors=[]
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            browser=getattr(pw,browser_name).launch(headless=True);page=browser.new_page(viewport={"width":1280,"height":900})
            page.on("pageerror",lambda exc:errors.append(f"pageerror: {exc}"));page.on("console",lambda msg:errors.append(f"console.error: {msg.text}") if msg.type=="error" else None)
            page.goto(BASE+"/apps/pdf/",wait_until="load");page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            commands=page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.registry.inspect().commands")
            for command in ("file.open",):assert command in commands
            # The hamburger menu was removed (2.7.5): the header carries the actions directly.
            assert page.locator("#menuBtn").count()==0 and page.locator("#closeMenuBtn").count()==0
            assert page.locator("#openStartBtn").get_attribute("data-command")=="file.open"
            page.wait_for_selector('[data-frame-action="sun"]')
            page.click('[data-frame-action="sun"]');assert page.locator(".inkdos-settings-popover").is_visible()
            page.keyboard.press("Escape");assert page.locator(".inkdos-settings-popover").is_hidden()
            # Chromium opens through showOpenFilePicker (file-launch.js requestPicker); other engines fall back to the input.
            if page.evaluate("() => typeof window.showOpenFilePicker === 'function'"):
                page.evaluate("() => { window.__pickerCalls = 0; window.showOpenFilePicker = async () => { window.__pickerCalls++; throw new DOMException('cancelled', 'AbortError') } }")
                page.click("#openStartBtn");page.wait_for_function("() => window.__pickerCalls === 1", timeout=5000)
            else:
                with page.expect_file_chooser(timeout=5000):page.click("#openStartBtn")
            if errors:raise AssertionError({"browser":browser_name,"errors":errors})
            browser.close()
        print(f"PDF frame command regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Regression: documents follows a newer Home appearance choice, keeps its own later
choice, and applies Home changes made in another tab while open."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8813
BASE=f'http://127.0.0.1:{PORT}'
APP='documents'
RESOLVED="()=>document.documentElement.dataset.appearanceResolved"

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

def home_choose(page,mode):
    page.goto(BASE+'/',wait_until='load')
    page.click('#appearanceButton'); page.click(f'[data-home-appearance-mode="{mode}"]')
    page.wait_for_timeout(50)

def open_app(page):
    page.goto(BASE+f'/apps/{APP}/',wait_until='load')
    page.wait_for_function("() => !!document.querySelector('[data-settings-item=\"appearance\"]')",timeout=10000)

def app_choose(page,mode):
    page.locator('#menuBtn:visible,#menuButton:visible').first.click()
    page.locator('[data-settings-item="appearance"]').first.click()
    page.locator(f'.inkdos-settings-option[data-settings-value="{mode}"]').first.click()
    page.wait_for_function(f"()=>document.documentElement.dataset.appearanceResolved==='{mode}'")

def main():
    browser_name=os.environ.get('BROWSER','chromium')
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            args={'headless':True}
            if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
            browser=getattr(pw,browser_name).launch(**args)
            ctx=browser.new_context(color_scheme='light'); page=ctx.new_page(); page.on('dialog',lambda d:d.accept())
            open_app(page)
            home_choose(page,'dark'); open_app(page)
            assert page.evaluate(RESOLVED)=='dark','app did not follow Home'
            app_choose(page,'light'); page.wait_for_timeout(20)
            open_app(page)
            assert page.evaluate(RESOLVED)=='light','app lost its own later choice'
            home_choose(page,'dark'); open_app(page)
            assert page.evaluate(RESOLVED)=='dark','app did not follow a newer Home choice'
            home=ctx.new_page(); home_choose(home,'light')
            page.wait_for_function(f"()=>document.documentElement.dataset.appearanceResolved==='light'",timeout=5000)
            browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'{APP} follows Home appearance ({browser_name}): OK')

if __name__=='__main__':
    main()

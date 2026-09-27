#!/usr/bin/env python3
"""Regression: choosing an appearance in Home records when it changed, so each
workspace can adopt a newer Home choice while keeping its own later choices."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8812
BASE=f'http://127.0.0.1:{PORT}'

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

def main():
    browser_name=os.environ.get('BROWSER','chromium')
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            args={'headless':True}
            if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
            browser=getattr(pw,browser_name).launch(**args)
            page=browser.new_page()
            page.goto(BASE+'/',wait_until='load')
            before=int(time.time()*1000)-1000
            for mode in ('dark','light'):
                page.click('#appearanceButton'); page.click(f'[data-home-appearance-mode="{mode}"]')
                state=page.evaluate("()=>({mode:localStorage.getItem('inkdos2:appearance'),at:Number(localStorage.getItem('inkdos2:appearance:changedAt'))})")
                assert state['mode']==mode and state['at']>=before,state
                before=state['at']
            browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Home theme broadcast timestamp ({browser_name}): OK')

if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Regression: files rejected on the native-picker or launchQueue paths must surface a
visible Spreadsheets error instead of failing silently (inkdos:file-launch-error)."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8803
BASE=f'http://127.0.0.1:{PORT}'
INIT=r"""(()=>{window.showOpenFilePicker=async()=>[{kind:'file',name:'notes.zip',getFile:async()=>new File(['PK garbage'],'notes.zip',{type:'application/zip'})}];
Object.defineProperty(window,'launchQueue',{configurable:true,value:{setConsumer(fn){window.__launchConsumer=fn}}});})();"""
VISIBLE="()=>{const e=document.getElementById('errorOverlay');return !!e&&e.getBoundingClientRect().height>0&&!e.hidden?e.innerText:null}"

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
            for path in ('picker','launchQueue'):
                ctx=browser.new_context(viewport={'width':1280,'height':900}); ctx.add_init_script(INIT); page=ctx.new_page()
                page.goto(BASE+'/apps/spreadsheets/',wait_until='load')
                page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')
                if path=='picker':
                    page.click('#startOpen')
                else:
                    page.evaluate("""()=>window.__launchConsumer({files:[{kind:'file',name:'fake.bin',getFile:async()=>new File(['x'],'fake.bin',{type:'application/octet-stream'})}]})""")
                page.wait_for_function(VISIBLE,timeout=5000)
                text=page.evaluate(VISIBLE)
                assert 'could not' in text.lower() or 'unsupported' in text.lower() or 'x' in text.lower(),(path,text)
                ctx.close()
            browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Spreadsheets file-launch error visibility ({browser_name}): OK')

if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Regression: a failed presentation save is titled as a save failure without the
'Choose another file' action; open failures keep their wording and action."""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8809
BASE=f'http://127.0.0.1:{PORT}'
STUB=r"""window.showSaveFilePicker=async()=>({name:'x.pptx',kind:'file',createWritable:async()=>{throw new DOMException('disk full','QuotaExceededError')}});"""
PANEL=r"""()=>{const p=document.getElementById('openErrorPanel');if(!p||p.hidden)return null;const r=p.querySelector('#retryOpen');return {title:p.querySelector('h2').innerText,retryVisible:!!r&&!r.hidden&&r.getBoundingClientRect().width>0}}"""

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
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/'broken.pptx'; bad.write_bytes(b'not a zip')
            with sync_playwright() as pw:
                args={'headless':True}
                if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
                browser=getattr(pw,browser_name).launch(**args)
                ctx=browser.new_context(viewport={'width':1280,'height':900}); ctx.add_init_script(STUB); page=ctx.new_page()
                page.goto(BASE+'/apps/presentations/',wait_until='load')
                page.wait_for_function('() => !!globalThis.__inkdosPresentations')
                page.click('#startNew')
                page.wait_for_function('() => globalThis.__inkdosPresentations.session.active')
                page.click('#addSlideBtn')
                page.click('#menuBtn'); page.click('#saveMenuBtn')
                page.wait_for_function(PANEL,timeout=8000)
                save=page.evaluate(PANEL)
                assert 'saved' in save['title'].lower() and 'opened' not in save['title'].lower(),save
                assert save['retryVisible'] is False,save
                page.click('#dismissError')
                page.set_input_files('#fileInput',str(bad))
                deadline=time.time()+8
                while time.time()<deadline and not page.evaluate(PANEL):
                    d=page.locator('#presentationsUnsavedDialog [data-choice="discard"]')
                    if d.count() and d.first.is_visible():d.first.click()
                    page.wait_for_timeout(200)
                opened=page.evaluate(PANEL)
                assert 'opened' in opened['title'].lower() and opened['retryVisible'] is True,opened
                browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Presentations save-error title ({browser_name}): OK')

if __name__=='__main__':
    main()

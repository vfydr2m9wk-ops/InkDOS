#!/usr/bin/env python3
"""Regression: a failed Save copy is reported as a save failure (no 'could not be
opened' title, no 'Choose another file' action); open failures keep their wording."""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8807
BASE=f'http://127.0.0.1:{PORT}'
STUB=r"""window.showSaveFilePicker=async()=>({name:'x.docx',kind:'file',createWritable:async()=>{throw new DOMException('disk full','QuotaExceededError')}});"""
PANEL=r"""()=>{const p=document.getElementById('openErrorPanel');if(!p||p.classList.contains('hidden'))return null;const r=p.querySelector('#retryOpen');return {title:p.querySelector('h2').innerText,retryVisible:!!r&&!r.hidden&&r.getBoundingClientRect().width>0}}"""

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
            bad=Path(td)/'broken.docx'; bad.write_bytes(b'not a zip')
            with sync_playwright() as pw:
                args={'headless':True}
                if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
                browser=getattr(pw,browser_name).launch(**args)
                ctx=browser.new_context(viewport={'width':1280,'height':900}); ctx.add_init_script(STUB); page=ctx.new_page()
                page.goto(BASE+'/apps/documents/',wait_until='load')
                page.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsApp')
                page.click('#startNew')
                page.locator('.page-content').click(); page.keyboard.type('hello')
                page.click('#menuBtn'); page.click('#saveMenuBtn')
                page.wait_for_selector('#deliverCopy'); page.click('#deliverCopy')
                page.wait_for_function(PANEL,timeout=8000)
                save=page.evaluate(PANEL)
                assert 'saved' in save['title'].lower() and 'opened' not in save['title'].lower(),save
                assert save['retryVisible'] is False,save
                page.click('#dismissError')
                page.locator('#saveReadyPanel #closeSave').click() if page.locator('#saveReadyPanel #closeSave').count() else None
                page.set_input_files('#fileInput',str(bad))
                discard=page.get_by_role('button',name='Discard',exact=True)
                deadline=time.time()+8
                while time.time()<deadline and not page.evaluate(PANEL):
                    if discard.count() and discard.first.is_visible():discard.first.click()
                    page.wait_for_timeout(200)
                opened=page.evaluate(PANEL)
                assert 'opened' in opened['title'].lower() and opened['retryVisible'] is True,opened
                browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Documents save-error title ({browser_name}): OK')

if __name__=='__main__':
    main()

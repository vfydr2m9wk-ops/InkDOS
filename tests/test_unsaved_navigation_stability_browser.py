#!/usr/bin/env python3
from __future__ import annotations
import os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8786
BASE=f'http://127.0.0.1:{PORT}'

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

def assert_three_way_dialog(page, workspace, boot_js, dirty_js, action_js):
    page.goto(f'{BASE}/{workspace}',wait_until='load')
    page.wait_for_function(boot_js)
    page.evaluate(dirty_js)
    page.evaluate(f'()=>{{ {action_js}; return true; }}')
    page.wait_for_selector('#sessionReplacePanel:not([hidden])')
    controls=page.evaluate("""()=>({
      save:!!document.getElementById('sessionReplaceSave'),
      discard:!!document.getElementById('sessionReplaceDiscard'),
      cancel:!!document.getElementById('sessionReplaceCancel'),
      labels:[...document.querySelectorAll('#sessionReplacePanel button')].map(b=>b.textContent.trim())
    })""")
    assert controls['save'] is True,controls
    assert controls['discard'] is True,controls
    assert controls['cancel'] is True,controls
    assert controls['labels']==['Cancel','Discard','Save'],controls
    page.click('#sessionReplaceCancel')

def main():
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser_name=os.environ.get('BROWSER','chromium')
            browser=getattr(pw,browser_name).launch(headless=True)
            page=browser.new_page(viewport={'width':1280,'height':900})
            page.goto(BASE+'/apps/documents/',wait_until='load')
            page.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsApp')
            page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.newDocument()')
            page.wait_for_function('() => globalThis.InkDOS2Documents.DocumentsApp.session.active')
            assert_three_way_dialog(
                page,'apps/documents/',
                '() => !!globalThis.InkDOS2Documents?.DocumentsApp',
                '()=>{globalThis.InkDOS2Documents.DocumentsApp.session.markDirty()}',
                'void globalThis.InkDOS2Documents.DocumentsApp.newDocument()'
            )
            assert_three_way_dialog(
                page,'apps/spreadsheets/',
                '() => !!globalThis.__inkdosSpreadsheetsS1?.session',
                '()=>{const s=globalThis.__inkdosSpreadsheetsS1.session;const b=globalThis.LocalXLSX.createBlank();b.loaded=true;b.fileName="Untitled.xlsx";s.newBook(b);s.markDirty()}',
                'void globalThis.__inkdosSpreadsheetsS1.openController.newWorkbook()'
            )
            browser.close()
        print(f'Unsaved in-app navigation three-way decision passed on {browser_name}.')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

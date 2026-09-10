#!/usr/bin/env python3
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8794
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
            browser=getattr(pw,browser_name).launch(headless=True)
            page=browser.new_page(viewport={'width':1280,'height':900},accept_downloads=True)
            page.goto(BASE+'/apps/spreadsheets/',wait_until='load')
            page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')
            page.evaluate("""async()=>{
              const api=globalThis.__inkdosSpreadsheetsS1;
              await api.openController.newWorkbook();
              api.editor.editor.commitValue('unsaved',0,0);
              globalThis.__inkdosBookId=api.session.documentId;
              globalThis.__inkdosPending=api.openController.newWorkbook();
            }""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            labels=page.locator('#sessionReplacePanel .error-actions button').all_text_contents()
            assert labels==['Cancel','Discard','Save'],labels

            # Cancel keeps the current dirty workbook and identity intact.
            page.get_by_role('button',name='Cancel').click()
            assert page.evaluate('async()=>await globalThis.__inkdosPending') is False
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.dirty') is True
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.documentId===globalThis.__inkdosBookId') is True

            # Repeated requests reuse one dialog and cancel the older request.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1;
              globalThis.__inkdosFirst=api.openController.newWorkbook();
              globalThis.__inkdosSecond=api.openController.newWorkbook();
            }""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            assert page.locator('#sessionReplacePanel').count()==1
            page.get_by_role('button',name='Cancel').click()
            assert page.evaluate('async()=>[await globalThis.__inkdosFirst,await globalThis.__inkdosSecond]')==[False,False]
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.dirty') is True

            # Discard replaces without saving and leaves the new workbook clean.
            page.evaluate('()=>{globalThis.__inkdosPending=globalThis.__inkdosSpreadsheetsS1.openController.newWorkbook()}')
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            page.get_by_role('button',name='Discard').click()
            assert page.evaluate('async()=>await globalThis.__inkdosPending') is True
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.dirty') is False

            # Save delivery completes before replacement proceeds.
            page.evaluate("""()=>{const api=globalThis.__inkdosSpreadsheetsS1;api.editor.editor.commitValue('save-me',0,0);globalThis.__inkdosPending=api.openController.newWorkbook()}""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            with page.expect_download() as info:
                page.get_by_role('button',name='Save').click()
            assert info.value.suggested_filename.lower().endswith('.xlsx')
            assert page.evaluate('async()=>await globalThis.__inkdosPending') is True
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.dirty') is False

            # Cancelled save must not replace the workbook.
            page.evaluate("""()=>{const api=globalThis.__inkdosSpreadsheetsS1;api.editor.editor.commitValue('stay',0,0);globalThis.__inkdosBookId=api.session.documentId;globalThis.showSaveFilePicker=async()=>{throw new DOMException('cancelled','AbortError')};globalThis.__inkdosPending=api.openController.newWorkbook()}""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            page.get_by_role('button',name='Save').click()
            assert page.evaluate('async()=>await globalThis.__inkdosPending') is False
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.dirty') is True
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.documentId===globalThis.__inkdosBookId') is True
            page.evaluate('()=>{try{delete globalThis.showSaveFilePicker}catch(_){}}')

            # Clean replacement should not raise an unnecessary prompt.
            clean=page.evaluate("""async()=>{
              const api=globalThis.__inkdosSpreadsheetsS1;
              api.session.markClean(api.session.revision);
              const before=!!document.querySelector('#sessionReplacePanel:not([hidden])');
              const result=await api.openController.newWorkbook();
              return {result,before,open:!!document.querySelector('#sessionReplacePanel:not([hidden])')};
            }""")
            assert clean=={'result':True,'before':False,'open':False},clean

            # Dirty in-app Home is guarded by InkDOS rather than navigating immediately.
            page.evaluate("""()=>{const api=globalThis.__inkdosSpreadsheetsS1;api.editor.editor.commitValue('home-stay',0,0);globalThis.__inkdosBookId=api.session.documentId}""")
            page.locator('a[aria-label="Home"]').click()
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            assert '/apps/spreadsheets/' in page.url,page.url
            assert page.locator('#sessionReplacePanel .error-actions button').all_text_contents()==['Cancel','Discard','Save']
            page.get_by_role('button',name='Cancel').click()
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.dirty') is True
            assert page.evaluate('()=>globalThis.__inkdosSpreadsheetsS1.session.documentId===globalThis.__inkdosBookId') is True

            # Browser-level unload remains platform-native and separate.
            unload=page.evaluate("""()=>{const ev=new Event('beforeunload',{cancelable:true});return {ok:window.dispatchEvent(ev),prevented:ev.defaultPrevented}}""")
            assert unload=={'ok':False,'prevented':True},unload
            browser.close()
        print(f'Spreadsheets unsaved-exit browser ({browser_name}): OK')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

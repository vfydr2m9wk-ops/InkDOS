#!/usr/bin/env python3
from __future__ import annotations
import os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8772
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
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser_name=os.environ.get('BROWSER','chromium')
            browser=getattr(pw,browser_name).launch(headless=True)
            page=browser.new_page(viewport={'width':1280,'height':900},accept_downloads=True)
            page.add_init_script("""
              document.addEventListener('DOMContentLoaded',()=>{
                document.querySelector('.fmt-btn[data-cmd="bold"]')?.remove();
              },{once:true});
            """)
            page.goto(BASE+'/apps/documents/',wait_until='load')
            page.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsDebug?.executeCommand')
            result=page.evaluate("""async()=>{
              const dbg=globalThis.InkDOS2Documents.DocumentsDebug;
              const before=dbg.listCommands();
              const boldControlMissing=!document.querySelector('.fmt-btn[data-cmd="bold"]');
              const formatCommandSurvived=dbg.hasCommand('format.bold');
              document.getElementById('newMenuBtn')?.remove();
              document.getElementById('undoBtn')?.remove();
              document.getElementById('redoBtn')?.remove();
              const stillRegistered=['file.new','edit.undo','edit.redo','format.bold','format.fontName','format.lineSpacing','insert.image'].every(id=>dbg.hasCommand(id));
              await dbg.executeCommand('file.new');
              await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
              await dbg.executeCommand('format.bold');
              return {
                boldControlMissing,
                formatCommandSurvived,
                stillRegistered,
                commandCount:before.length,
                pageCount:document.querySelectorAll('#pagesHost .doc-page').length,
                welcomeHidden:document.getElementById('welcome')?.hidden===true,
                status:document.getElementById('statusText')?.textContent||''
              };
            }""")
            assert result['boldControlMissing'] is True,result
            assert result['formatCommandSurvived'] is True,result
            assert result['stillRegistered'] is True,result
            assert result['commandCount']>=20,result
            assert result['pageCount']>=1,result
            assert result['welcomeHidden'] is True,result

            # INKBUG-0002: dirty replacement exposes explicit tri-state semantics.
            page.evaluate("""()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              app.session.markDirty();
              globalThis.__inkdosDocumentId=app.session.documentId;
              globalThis.__inkdosPendingReplacement=app.newDocument();
            }""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            labels=page.locator('#sessionReplacePanel .error-actions button').all_text_contents()
            assert labels==['Cancel','Discard','Save'],labels

            # Cancel: remain in the same dirty document with state intact.
            page.get_by_role('button',name='Cancel').click()
            cancelled=page.evaluate('async()=>await globalThis.__inkdosPendingReplacement')
            assert cancelled is False,cancelled
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.dirty') is True
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.documentId===globalThis.__inkdosDocumentId') is True

            # Repeated requests must not create duplicate dialogs; the older request cancels.
            page.evaluate("""()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              globalThis.__inkdosFirst=app.newDocument();
              globalThis.__inkdosSecond=app.newDocument();
            }""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            assert page.locator('#sessionReplacePanel').count()==1
            page.get_by_role('button',name='Cancel').click()
            repeated=page.evaluate('async()=>[await globalThis.__inkdosFirst,await globalThis.__inkdosSecond]')
            assert repeated==[False,False],repeated
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.dirty') is True

            # Discard: replacement proceeds without saving and leaves the new document clean.
            page.evaluate('()=>{globalThis.__inkdosPendingReplacement=globalThis.InkDOS2Documents.DocumentsApp.newDocument()}')
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            page.get_by_role('button',name='Discard').click()
            discarded=page.evaluate('async()=>await globalThis.__inkdosPendingReplacement')
            assert discarded is True,discarded
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.dirty') is False

            # Save: file delivery must happen before replacement resolves.
            page.evaluate("""()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              app.session.markDirty();
              try{delete globalThis.showSaveFilePicker}catch(_){}
              globalThis.__inkdosPendingReplacement=app.newDocument();
            }""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            with page.expect_download() as download_info:
                page.get_by_role('button',name='Save').click()
            download=download_info.value
            saved=page.evaluate('async()=>await globalThis.__inkdosPendingReplacement')
            assert saved is True,saved
            assert download.suggested_filename.lower().endswith('.docx'),download.suggested_filename
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.dirty') is False

            # Save cancellation: do not navigate and preserve dirty state/document identity.
            page.evaluate("""()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              app.session.markDirty();
              globalThis.__inkdosDocumentId=app.session.documentId;
              globalThis.showSaveFilePicker=async()=>{throw new DOMException('cancelled','AbortError')};
              globalThis.__inkdosPendingReplacement=app.newDocument();
            }""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            page.get_by_role('button',name='Save').click()
            save_cancelled=page.evaluate('async()=>await globalThis.__inkdosPendingReplacement')
            assert save_cancelled is False,save_cancelled
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.dirty') is True
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.documentId===globalThis.__inkdosDocumentId') is True

            # Clean replacement: no unnecessary dialog.
            clean_result=page.evaluate("""async()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              app.session.markSaved(app.session.revision);
              try{delete globalThis.showSaveFilePicker}catch(_){}
              const before=document.querySelector('#sessionReplacePanel:not([hidden])');
              const result=await app.newDocument();
              return {result,dialogOpen:!!document.querySelector('#sessionReplacePanel:not([hidden])'),before:!!before};
            }""")
            assert clean_result=={'result':True,'dialogOpen':False,'before':False},clean_result
            page.close()

            # RED continuation: actual suite Home must be guarded before dirty data can be abandoned.
            home=browser.new_page(viewport={'width':1280,'height':900},accept_downloads=True)
            home.goto(BASE+'/apps/documents/?suite=1',wait_until='load')
            home.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsApp')
            home.evaluate("""async()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              await app.newDocument();
              app.session.markDirty();
              globalThis.__inkdosHomeDocumentId=app.session.documentId;
            }""")
            home.locator('a[aria-label="Home"]').click()
            home.wait_for_selector('#sessionReplacePanel:not([hidden])')
            assert '/apps/documents/' in home.url,home.url
            assert home.locator('#sessionReplacePanel .error-actions button').all_text_contents()==['Cancel','Discard','Save']
            home.get_by_role('button',name='Cancel').click()
            assert home.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.dirty') is True
            assert home.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.documentId===globalThis.__inkdosHomeDocumentId') is True

            # Browser-level refresh/unload is separate and should request the platform-native warning while dirty.
            unload_guard=home.evaluate("""()=>{
              const ev=new Event('beforeunload',{cancelable:true});
              return {dispatchResult:window.dispatchEvent(ev),defaultPrevented:ev.defaultPrevented};
            }""")
            assert unload_guard['dispatchResult'] is False and unload_guard['defaultPrevented'] is True,unload_guard
            home.close()
            browser.close()
        print(f"Documents command/control and unsaved-exit browser isolation passed on {os.environ.get('BROWSER','chromium')}.")
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

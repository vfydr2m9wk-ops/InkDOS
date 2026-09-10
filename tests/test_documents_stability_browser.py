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
            page=browser.new_page(viewport={'width':1280,'height':900})
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

            # INKBUG-0002 reproduction: a dirty in-app replacement must expose
            # explicit Save / Discard / Cancel semantics, not a binary Continue.
            page.evaluate("""()=>{
              const app=globalThis.InkDOS2Documents.DocumentsApp;
              app.session.markDirty();
              globalThis.__inkdosPendingReplacement=app.newDocument();
            }""")
            page.wait_for_selector('#sessionReplacePanel:not([hidden])')
            labels=page.locator('#sessionReplacePanel .error-actions button').all_text_contents()
            assert labels==['Cancel','Discard','Save'],labels
            page.get_by_role('button',name='Cancel').click()
            page.wait_for_function('() => globalThis.__inkdosPendingReplacement instanceof Promise')
            cancelled=page.evaluate('async()=>await globalThis.__inkdosPendingReplacement')
            assert cancelled is False,cancelled
            assert page.evaluate('()=>globalThis.InkDOS2Documents.DocumentsApp.session.dirty') is True
            browser.close()
        print(f"Documents command/control and unsaved-exit browser isolation passed on {os.environ.get('BROWSER','chromium')}.")
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

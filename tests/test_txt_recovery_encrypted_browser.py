#!/usr/bin/env python3
"""Regression: Plain Text recovery checkpoints follow the suite's draft rules. The text and file name are not
stored in plain text in IndexedDB, plain checkpoints of earlier versions are encrypted in place and still
offered, and nothing is kept while drafts are turned off in Settings."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8812
BASE=f'http://127.0.0.1:{PORT}'
SECRET='SECRET-PLAINTEXT-7731'

# every checkpoint record as stored, with its bytes made searchable
DUMP=r"""() => new Promise((resolve,reject)=>{const r=indexedDB.open('inkdos2-txt-recovery');r.onerror=()=>reject(r.error);
 r.onsuccess=()=>{const db=r.result;const q=db.transaction('checkpoints','readonly').objectStore('checkpoints').getAll();
  q.onsuccess=()=>{db.close();resolve(q.result.map(rec=>JSON.stringify(rec,(k,v)=>v instanceof Uint8Array?Array.from(v):v)))};q.onerror=()=>reject(q.error)}})"""
LEGACY=r"""secret => new Promise((resolve,reject)=>{const r=indexedDB.open('inkdos2-txt-recovery',1);
 r.onupgradeneeded=()=>r.result.createObjectStore('checkpoints',{keyPath:'key'});r.onerror=()=>reject(r.error);
 r.onsuccess=()=>{const db=r.result,tx=db.transaction('checkpoints','readwrite');tx.objectStore('checkpoints').put({key:'txt:tab:legacy-closed-tab',generation:1,createdAt:Date.now(),
  payload:{schema:1,fileName:'legacy.txt',text:secret,encoding:'utf-8',bom:false,lineEnding:'\n',wrap:true,fontSize:15,revision:1,sessionId:'legacy',dirty:true}});
  tx.oncomplete=()=>{db.close();resolve(true)};tx.onerror=()=>reject(tx.error)}})"""

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

def ready(page):
    page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug")

def open_app(ctx):
    page=ctx.new_page(); page.on('dialog',lambda d:d.accept())
    page.goto(BASE+'/apps/txt/',wait_until='load'); ready(page); return page

def type_unsaved(page,text):
    page.click('#startNew'); page.wait_for_function('() => InkDOS2.TxtAppDebug.state.loaded')
    page.click('#editor'); page.keyboard.type(text)
    page.wait_for_function("() => InkDOS2.TxtAppDebug.state.session.checkpointRevision===InkDOS2.TxtAppDebug.state.session.revision",timeout=5000)

def main():
    browser_name=os.environ.get('BROWSER','chromium')
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            args={'headless':True}
            if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
            browser=getattr(pw,browser_name).launch(**args)

            # 1. A checkpoint exists, but neither the text nor the file name is readable in storage.
            ctx=browser.new_context(); page=open_app(ctx)
            type_unsaved(page,SECRET)
            stored=page.evaluate(DUMP)
            assert stored,'no recovery checkpoint was written'
            assert not any(SECRET in rec or 'Untitled' in rec for rec in stored),'checkpoint stored in plain text'
            # ... and it is still recovered after a reload
            page.reload(wait_until='load'); ready(page)
            page.wait_for_selector('.txt-recovery-offer',state='visible',timeout=2500)
            page.click('#recoveryAccept')
            page.wait_for_function(f"() => document.getElementById('editor').value.includes('{SECRET}')")
            ctx.close()

            # 2. A plain checkpoint left by an earlier version is offered and encrypted in place.
            ctx=browser.new_context(); page=ctx.new_page(); page.goto(BASE+'/robots.txt')
            page.evaluate(LEGACY,SECRET); page.close()
            page=open_app(ctx)
            page.wait_for_selector('.txt-recovery-offer',state='visible',timeout=2500)
            assert not any(SECRET in rec for rec in page.evaluate(DUMP)),'legacy checkpoint left in plain text'
            page.click('#recoveryAccept')
            page.wait_for_function(f"() => document.getElementById('editor').value.includes('{SECRET}')")
            ctx.close()

            # 3. Drafts turned off in Settings: nothing is kept.
            ctx=browser.new_context(); ctx.add_init_script("try{localStorage.setItem('inkdos.recoveryDrafts','off')}catch(_){}")
            page=open_app(ctx)
            type_unsaved(page,SECRET)
            assert page.evaluate(DUMP)==[],'checkpoint written while drafts are off'
            ctx.close()
            browser.close()
    finally:
        server.terminate(); server.wait(timeout=5)
    print('Plain Text recovery encryption regression passed.')

if __name__=='__main__':
    main()

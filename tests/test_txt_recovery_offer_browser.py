#!/usr/bin/env python3
"""Regression: unsaved Plain Text is offered for recovery (never restored silently)
after a reload or after its tab closed; Discard, Save and live sibling tabs are respected."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8811
BASE=f'http://127.0.0.1:{PORT}'
OFFER='.txt-recovery-offer'
STUB=r"""window.showSaveFilePicker=async()=>({name:'x.txt',kind:'file',createWritable:async()=>({write:async()=>{},close:async()=>{}})});"""

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

def offer_visible(page,timeout=2500):
    try: page.wait_for_selector(OFFER,state='visible',timeout=timeout); return True
    except Exception: return False

def main():
    browser_name=os.environ.get('BROWSER','chromium')
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            args={'headless':True}
            if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
            browser=getattr(pw,browser_name).launch(**args)

            # 1. Reload in the same tab: offered, not auto-restored; Recover restores.
            ctx=browser.new_context(); page=open_app(ctx)
            type_unsaved(page,'RELOAD-DRAFT')
            page.reload(wait_until='load'); ready(page)
            assert offer_visible(page),'no recovery offer after reload'
            assert page.evaluate('() => InkDOS2.TxtAppDebug.state.loaded') is False,'restored without asking'
            page.click('#recoveryAccept')
            page.wait_for_function("() => document.getElementById('editor').value.includes('RELOAD-DRAFT')")
            assert page.evaluate('() => InkDOS2.TxtAppDebug.state.session.dirty') is True
            ctx.close()

            # 2. Closed tab, new tab: offered; Discard removes it for good.
            ctx=browser.new_context(); page=open_app(ctx)
            type_unsaved(page,'CLOSED-DRAFT'); page.close()
            page=open_app(ctx)
            assert offer_visible(page),'no recovery offer after tab closed'
            page.click('#recoveryDiscard')
            page.wait_for_selector(OFFER,state='detached')
            page.close(); page=open_app(ctx)
            assert not offer_visible(page,1500),'discarded checkpoint offered again'
            ctx.close()

            # 3. Saved text is not offered.
            ctx=browser.new_context(); ctx.add_init_script(STUB); page=open_app(ctx)
            type_unsaved(page,'SAVED-TEXT')
            page.evaluate("()=>document.querySelector('#saveBtn').click()")
            page.wait_for_function('() => !InkDOS2.TxtAppDebug.state.session.dirty',timeout=5000)
            page.wait_for_timeout(400); page.close()
            page=open_app(ctx)
            assert not offer_visible(page,1500),'saved text offered for recovery'
            ctx.close()

            # 4. A live sibling tab's draft is not offered to another tab.
            ctx=browser.new_context(); a=open_app(ctx)
            type_unsaved(a,'LIVE-SIBLING')
            b=open_app(ctx)
            assert not offer_visible(b,1500),'live sibling draft offered'
            ctx.close()
            browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Plain Text recovery offer ({browser_name}): OK')

if __name__=='__main__':
    main()

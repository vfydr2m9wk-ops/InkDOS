#!/usr/bin/env python3
"""Regression: re-applying the current language must not rewrite unchanged text,
attributes or <html lang>. Those identical writes invalidated layout on every
status update, which made typing in a large Plain Text file stall."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8810
BASE=f'http://127.0.0.1:{PORT}'
WATCH=r"""()=>{window.__writes=[];new MutationObserver(rs=>{for(const r of rs){if(r.type==='attributes')window.__writes.push('attr:'+r.attributeName+'@'+(r.target.id||r.target.tagName));else if(r.type==='characterData')window.__writes.push('text')}}).observe(document.documentElement,{attributes:true,attributeFilter:['lang','placeholder','title','aria-label'],characterData:true,subtree:true})}"""

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
            page=browser.new_page(viewport={'width':1280,'height':900})
            page.goto(BASE+'/apps/txt/',wait_until='load')
            page.wait_for_function("() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOSLocalization")
            page.click('#startNew')
            page.wait_for_function("() => InkDOS2.TxtAppDebug.state.loaded")
            page.wait_for_timeout(500)
            page.evaluate(WATCH)
            page.click('#editor')
            for ch in 'abc':
                page.keyboard.type(ch)
                page.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r())))")
            page.wait_for_timeout(300)
            writes=page.evaluate('()=>window.__writes')
            assert not writes,writes
            # Real language changes still apply.
            page.evaluate("() => InkDOSLocalization.setLanguage('pt-BR')")
            page.wait_for_function("() => document.documentElement.lang === 'pt-BR'")
            page.evaluate("() => InkDOSLocalization.setLanguage('en')")
            page.wait_for_function("() => document.documentElement.lang === 'en'")
            browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Localization no-op apply ({browser_name}): OK')

if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Regression: the Presentations unsaved-changes guard is a styled overlay above the
menu drawer, so Cancel/Discard/Save are reachable when triggered from the menu."""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8798
BASE=f'http://127.0.0.1:{PORT}'
PROBE=r"""()=>{const d=document.getElementById('presentationsUnsavedDialog');if(!d)return null;const cs=getComputedStyle(d),card=d.querySelector('.error-card');
const hit=b=>{const r=b.getBoundingClientRect();const h=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return !!h&&b.contains(h)};
const drawer=document.querySelector('.drawer');return {position:cs.position,z:Number(cs.zIndex)||0,drawerZ:drawer?Number(getComputedStyle(drawer).zIndex)||0:0,
cardBg:getComputedStyle(card).backgroundColor,reachable:[...d.querySelectorAll('[data-choice]')].every(hit),inViewport:card.getBoundingClientRect().bottom<=innerHeight}}"""

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
            ctx=browser.new_context(viewport={'width':1280,'height':900})
            # Force the <input type=file> path so the picker is observable in every engine.
            ctx.add_init_script('window.showOpenFilePicker=undefined')
            page=ctx.new_page()
            page.goto(BASE+'/apps/presentations/?suite=1',wait_until='load')
            page.wait_for_function('() => !!globalThis.__inkdosPresentations')
            page.click('#startNew')
            page.wait_for_function('() => globalThis.__inkdosPresentations.session.active')
            page.click('#addSlideBtn')
            page.wait_for_function('() => globalThis.__inkdosPresentations.session.dirty')
            for trigger in ('#openMenuBtn','#newMenuBtn'):
                page.click('#menuBtn'); page.click(trigger)
                page.wait_for_selector('#presentationsUnsavedDialog')
                probe=page.evaluate(PROBE)
                assert probe['position']=='fixed' and probe['z']>probe['drawerZ'],probe
                assert probe['cardBg'] not in ('rgba(0, 0, 0, 0)','transparent'),probe
                assert probe['reachable'] and probe['inViewport'],probe
                page.locator('#presentationsUnsavedDialog [data-choice="cancel"]').click()
                page.wait_for_selector('#presentationsUnsavedDialog',state='detached')
                assert page.evaluate('() => globalThis.__inkdosPresentations.session.dirty') is True
                if page.locator('#menuBackdrop').is_visible():page.click('#closeMenuBtn')
            page.click('#menuBtn'); page.click('#openMenuBtn')
            page.wait_for_selector('#presentationsUnsavedDialog')
            with page.expect_file_chooser(timeout=5000):
                page.locator('#presentationsUnsavedDialog [data-choice="discard"]').click()
            browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Presentations unsaved-guard overlay ({browser_name}): OK')

if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Regression: a 0-byte EPUB reports an empty file, not the input-size budget."""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8806
BASE=f'http://127.0.0.1:{PORT}'
STATUS="()=>document.querySelector('footer')?.innerText||''"

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
            path=Path(td)/'empty.epub'; path.write_bytes(b'')
            with sync_playwright() as pw:
                args={'headless':True}
                if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
                browser=getattr(pw,browser_name).launch(**args)
                page=browser.new_page(viewport={'width':1280,'height':900})
                page.goto(BASE+'/apps/epub/',wait_until='load')
                page.wait_for_function('() => !!globalThis.__InkEpubR4')
                page.set_input_files('#fileInput',str(path))
                page.wait_for_function(f"()=>/empty|budget/i.test(({STATUS})())",timeout=8000)
                text=page.evaluate(STATUS).lower()
                assert 'empty' in text and 'budget' not in text,text
                browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'EPUB empty-file message ({browser_name}): OK')

if __name__=='__main__':
    main()

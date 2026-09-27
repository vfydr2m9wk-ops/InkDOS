#!/usr/bin/env python3
"""Regression: a 0-byte presentation reports an empty file, not the size budget."""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8805
BASE=f'http://127.0.0.1:{PORT}'
PANEL="()=>{const p=document.getElementById('openErrorPanel');return p&&!p.hidden&&p.getBoundingClientRect().height>0?p.innerText:null}"

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
            with sync_playwright() as pw:
                args={'headless':True}
                if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
                browser=getattr(pw,browser_name).launch(**args)
                for name in ('empty.pptx','empty.ppt'):
                    path=Path(td)/name; path.write_bytes(b'')
                    page=browser.new_page(viewport={'width':1280,'height':900})
                    page.goto(BASE+'/apps/presentations/',wait_until='load')
                    page.wait_for_function('() => !!globalThis.__inkdosPresentations')
                    page.set_input_files('#fileInput',str(path))
                    page.wait_for_function(PANEL,timeout=8000)
                    text=page.evaluate(PANEL).lower()
                    assert 'empty' in text and 'budget' not in text,(name,text)
                    page.close()
                browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Presentations empty-file message ({browser_name}): OK')

if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""A page navigation made while visible pages re-render must not be undone by the stale scroll anchor."""
from __future__ import annotations
import os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=8781;BASE=f"http://127.0.0.1:{PORT}"
def wait_port(port,timeout=10.0):
    deadline=time.time()+timeout
    while time.time()<deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1",port))==0:return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")
def main():
    browser_name=os.environ.get("BROWSER","chromium").strip().lower()
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            browser=getattr(pw,browser_name).launch(headless=True);page=browser.new_page(viewport={"width":1280,"height":900})
            page.goto(BASE+"/apps/pdf/",wait_until="load");page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            page.add_script_tag(url=BASE+"/apps/pdf/vendor/pdf-lib/pdf-lib.min.js");page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument",timeout=15000)
            opened=page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create();for(let i=1;i<=3;i++){const p=pdf.addPage([612,792]);p.drawText(`Page ${i}`,{x:48,y:730,size:20})}const bytes=new Uint8Array(await pdf.save());return await d.fileOpen.openFile(new File([bytes],'nav.pdf',{type:'application/pdf'}));}""");assert opened is True
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 3")
            result=page.evaluate(r"""async()=>{const L=globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout;L.goToPage(1);await new Promise(r=>setTimeout(r,300));const render=L.render;let slow=true;L.render=async function(...args){if(slow)await new Promise(r=>setTimeout(r,250));return render.apply(this,args)};const rerender=L.rerenderVisible(true);slow=false;const nav=L.goToPage(2);await Promise.all([rerender,nav]);L.render=render;await new Promise(r=>setTimeout(r,500));return L.currentPage}""")
            assert result==2,{"browser":browser_name,"currentPage":result}
            browser.close()
        print(f"PDF navigation during re-render regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()
if __name__=="__main__":main()

#!/usr/bin/env python3
from __future__ import annotations
import socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8792
BASE=f"http://127.0.0.1:{PORT}"

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1",PORT))==0:return
        time.sleep(.1)
    raise RuntimeError("server did not start")

def main():
    check=sys.argv[1] if len(sys.argv)>1 else "all"
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    pageerrors=[]; consoleerrors=[]
    try:
        wait_port()
        with sync_playwright() as pw:
            browser=pw.webkit.launch(headless=True)
            page=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=3,is_mobile=True,has_touch=True)
            page.set_default_timeout(10000)
            page.on("pageerror",lambda exc:pageerrors.append(str(exc)))
            page.on("console",lambda msg:consoleerrors.append(msg.text) if msg.type=="error" else None)
            page.goto(BASE+"/apps/presentations/",wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations")
            page.click("#startNew")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.active")
            page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('slide.add')")
            page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('slide.add')")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length===3")
            page.wait_for_timeout(250)
            probe=page.evaluate("""() => {
              const app=globalThis.__inkdosPresentations, q=id=>document.getElementById(id), rect=e=>{const r=e.getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
              const canvas=rect(q('slideCanvas')), viewport=rect(q('viewport')), panel=rect(q('slidePanel'));
              const thumbs=[...q('slidePanelInner').querySelectorAll('.slide-thumb')].map(rect);
              const cx=(canvas.left+canvas.right)/2, cy=(canvas.top+canvas.bottom)/2, hit=document.elementFromPoint(cx,cy);
              const first=q('slidePanelInner').querySelector('.slide-thumb'), fr=first?first.getBoundingClientRect():null, thit=fr?document.elementFromPoint((fr.left+fr.right)/2,(fr.top+fr.bottom)/2):null;
              return {inspect:app.inspect(),canvas,viewport,panel,thumbs,paint:{canvasHit:!!hit&&(hit===q('slideCanvas')||q('slideCanvas').contains(hit)),thumbHit:!!first&&!!thit&&(thit===first||first.contains(thit)),hitTag:hit?.tagName||null,hitClass:hit?.className||null},html:{w:innerWidth,h:innerHeight}};
            }""")
            assert probe["inspect"]["session"]["slideCount"]==3,probe
            c,v=probe["canvas"],probe["viewport"]
            if check in ("all","dimensions"):
                assert c["width"]>100 and c["height"]>60,probe
            if check in ("all","intersection"):
                assert c["right"]>v["left"] and c["left"]<v["right"] and c["bottom"]>v["top"] and c["top"]<v["bottom"],probe
            if check in ("all","thumbs"):
                assert len(probe["thumbs"])==3,probe
                assert any(t["width"]>40 and t["height"]>30 for t in probe["thumbs"]),probe
            if check in ("all","paint"):
                assert probe["paint"]["canvasHit"] is True,probe
                assert probe["paint"]["thumbHit"] is True,probe
            browser.close()
        if check in ("all","pageerrors") and pageerrors: raise AssertionError(pageerrors)
        if check in ("all","consoleerrors") and consoleerrors: raise AssertionError(consoleerrors)
        print("Presentations iPhone/WebKit visibility regression passed (canvas + thumbnails).")
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__=="__main__": main()

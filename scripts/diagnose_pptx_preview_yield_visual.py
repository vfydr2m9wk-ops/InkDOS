#!/usr/bin/env python3
from __future__ import annotations
import base64,json,subprocess,sys,time,socket
from pathlib import Path
from playwright.sync_api import sync_playwright
from diagnose_pptx_preview_overhead import ROOT, instrument_open, instrument_app, fixture

PORT=8892
BASE=f"http://127.0.0.1:{PORT}"
OUT=ROOT/"artifacts/pptx-preview-yield-visual"
MODES=("current","one_raf","timeout_only")
TARGETS=(90,105,120,150,180)

def wait_port():
    end=time.time()+10
    while time.time()<end:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1",PORT))==0:return
        time.sleep(.1)
    raise RuntimeError("server start failed")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    open_src=instrument_open((ROOT/"apps/presentations/io/pptx-open-controller.js").read_text(encoding="utf-8"))
    app_raw=(ROOT/"apps/presentations/app.js").read_text(encoding="utf-8")
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
      wait_port()
      with sync_playwright() as pw:
        browser=pw.webkit.launch(headless=True)
        c0=browser.new_context(viewport={"width":1280,"height":820},service_workers="block");p0=c0.new_page()
        p0.goto(BASE+"/apps/presentations/index.html?suite=1",wait_until="load",timeout=30000)
        p0.wait_for_function("() => !!globalThis.InkDOS2Presentations?.PptxWriter")
        data=fixture(p0,44);c0.close()
        encoded=base64.b64encode(data).decode("ascii")
        report={}
        for mode in MODES:
          app_src=instrument_app(app_raw,mode);rows=[]
          for target in TARGETS:
            ctx=browser.new_context(viewport={"width":1280,"height":820},service_workers="block")
            ctx.route("**/apps/presentations/io/pptx-open-controller.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body=open_src))
            ctx.route("**/apps/presentations/app.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body=app_src))
            page=ctx.new_page()
            page.goto(BASE+"/apps/presentations/index.html?suite=1",wait_until="load",timeout=30000)
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session")
            page.evaluate("""encoded=>{
              const raw=atob(encoded),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
              const input=document.getElementById('fileInput');
              const dt=new DataTransfer();
              dt.items.add(new File([bytes],'visual-44.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'}));
              input.files=dt.files;
            }""",encoded)
            start=time.perf_counter()
            page.evaluate("() => document.getElementById('fileInput').dispatchEvent(new Event('change',{bubbles:true}))")
            remaining=target-(time.perf_counter()-start)*1000
            if remaining>0: page.wait_for_timeout(remaining)
            actual=(time.perf_counter()-start)*1000
            state=page.evaluate("""() => ({
              preview:document.body.dataset.presentationOpeningPreview==='true',
              transient:document.getElementById('slideCanvas')?.dataset?.transientPreview==='true',
              committed:globalThis.__inkdosPresentations?.session?.sourceKind==='pptx'&&globalThis.__inkdosPresentations?.session?.slides?.length===44,
              status:document.getElementById('statusText')?.textContent||'',
              text:(document.getElementById('slideCanvas')?.innerText||'').slice(0,100),
              panelVisibility:document.getElementById('slidePanel')?.style?.visibility||''
            })""")
            d=OUT/mode;d.mkdir(parents=True,exist_ok=True);shot=d/f"t{target}.png";page.screenshot(path=str(shot),full_page=False)
            rows.append({"targetMs":target,"actualMs":round(actual,2),**state,"screenshot":str(shot.relative_to(OUT))})
            ctx.close()
          report[mode]=rows
        browser.close()
      (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
      print(json.dumps(report,indent=2))
    finally:
      server.terminate()
      try:server.wait(timeout=3)
      except subprocess.TimeoutExpired:server.kill()
if __name__=="__main__":main()

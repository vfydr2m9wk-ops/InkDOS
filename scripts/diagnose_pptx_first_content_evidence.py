#!/usr/bin/env python3
from __future__ import annotations
import base64,json,os,socket,statistics,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=int(os.environ.get("INKDOS_FIRST_CONTENT_PORT","8881"))
BASE=f"http://127.0.0.1:{PORT}"
OUT=Path(os.environ.get("INKDOS_FIRST_CONTENT_OUT","artifacts/pptx-first-content-evidence"))
TARGETS_44=(100,150,200,250,300,400,800)
TARGETS_100=(150,250,400,600,800)

PROBE=r"""
(() => {
 const p=globalThis.__firstContentProbe={previewDom:null,previewPaint:null,commitDom:null,commitPaint:null};
 const check=()=>{
   const c=document.getElementById('slideCanvas'),app=globalThis.__inkdosPresentations;
   if(c?.dataset?.transientPreview==='true'&&c.childNodes.length&&p.previewDom==null){
     p.previewDom=performance.now();requestAnimationFrame(t=>{if(p.previewPaint==null)p.previewPaint=t});
   }
   if(app?.session?.active&&c?.dataset?.transientPreview!=='true'&&c?.childNodes.length&&p.commitDom==null){
     p.commitDom=performance.now();requestAnimationFrame(t=>{if(p.commitPaint==null)p.commitPaint=t});
   }
 };
 const install=()=>{new MutationObserver(check).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['data-transient-preview']});setInterval(check,2);check()};
 if(document.documentElement)install();else document.addEventListener('DOMContentLoaded',install,{once:true});
})();
"""

def wait_port():
    end=time.time()+10
    while time.time()<end:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1",PORT))==0:return
        time.sleep(.1)
    raise RuntimeError("server start failed")

def med(xs): return statistics.median(xs) if xs else None
def p95(xs):
    if not xs:return None
    a=sorted(xs);return a[min(len(a)-1,round(.95*(len(a)-1)))]

def launch_script(data:bytes,name:str)->str:
    enc=base64.b64encode(data).decode("ascii")
    return f"""(() => {{
      const raw=atob({json.dumps(enc)}),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
      const q={{consumer:null,setConsumer(fn){{this.consumer=fn;Promise.resolve().then(()=>fn({{files:[{{kind:'file',async getFile(){{return new File([bytes],{json.dumps(name)},{{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'}})}}}}]}}))}}}};
      Object.defineProperty(globalThis,'launchQueue',{{value:q,configurable:true}});
    }})();"""

def fixture(page,count:int)->bytes:
    b64=page.evaluate(r"""async count=>{
      const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel,s=new NS.PresentationSession();s.resetNew();
      const title=(slide,text)=>{const o=slide.objects[0];o.text=text;o.paragraphs=M.normalizeParagraphs(null,text,o)};
      title(s.slides[0],'InkDOS synthetic slide 1');
      for(let i=2;i<=count;i++){s.addSlide();title(s.currentSlide,'InkDOS synthetic slide '+i)}
      s.setCurrentByIndex(0);const bytes=await NS.PptxWriter.build(s);let raw='',chunk=0x8000;
      for(let i=0;i<bytes.length;i+=chunk)raw+=String.fromCharCode(...bytes.subarray(i,i+chunk));
      return btoa(raw)
    }""",count)
    return base64.b64decode(b64)

def context(browser,data,name,theme=None):
    kw={"viewport":{"width":1280,"height":820},"service_workers":"block"}
    if theme:kw["color_scheme"]=theme
    c=browser.new_context(**kw)
    c.add_init_script(PROBE);c.add_init_script(launch_script(data,name))
    if theme:c.add_init_script(f"try{{localStorage.setItem('inkdos2:appearance',{json.dumps(theme)})}}catch(_){{}}")
    return c

def numeric(browser,data,count,iterations):
    rows=[]
    for _ in range(iterations):
        c=context(browser,data,f"evidence-{count}.pptx");p=c.new_page()
        t=time.perf_counter();p.goto(BASE+"/apps/presentations/index.html?suite=1",wait_until="commit",timeout=30000)
        p.wait_for_function("""() => {
          const a=globalThis.__inkdosPresentations;
          return !!a?.session?.active && !a.openingPreview &&
            document.getElementById('slideCanvas')?.dataset?.transientPreview!=='true' &&
            document.getElementById('statusText')?.textContent?.startsWith('Opened');
        }""",timeout=30000)
        p.wait_for_timeout(30)
        wall=(time.perf_counter()-t)*1000
        r=p.evaluate("""() => {
          const q=globalThis.__firstContentProbe||{};
          return {previewDom:q.previewDom,previewPaint:q.previewPaint,commitDom:q.commitDom,commitPaint:q.commitPaint,
            previewSeen:q.previewDom!=null,status:document.getElementById('statusText')?.textContent||''};
        }""")
        first=r["previewPaint"] if r["previewPaint"] is not None else r["commitPaint"]
        r.update({"firstContentPaintMs":first,"fullCommitPaintMs":r["commitPaint"],"wallReadyMs":wall})
        rows.append(r);c.close()
    keys=("firstContentPaintMs","fullCommitPaintMs","wallReadyMs")
    return {"samples":rows,"summary":{k:{"median":med([x[k] for x in rows if x[k] is not None]),"p95":p95([x[k] for x in rows if x[k] is not None])} for k in keys},
            "previewSeenCount":sum(1 for x in rows if x["previewSeen"])}

def visual(browser,data,count,theme,targets):
    out=[]
    d=OUT/"visual"/theme/f"presentations-pptx-{count}";d.mkdir(parents=True,exist_ok=True)
    for target in targets:
        c=context(browser,data,f"evidence-{count}.pptx",theme);p=c.new_page()
        start=time.perf_counter();p.goto(BASE+"/apps/presentations/index.html?suite=1",wait_until="commit",timeout=30000)
        rem=target-(time.perf_counter()-start)*1000
        if rem>0:p.wait_for_timeout(rem)
        actual=(time.perf_counter()-start)*1000
        state=p.evaluate("""() => ({
          preview:document.getElementById('slideCanvas')?.dataset?.transientPreview==='true',
          committed:!!globalThis.__inkdosPresentations?.session?.active&&!globalThis.__inkdosPresentations?.openingPreview,
          text:(document.getElementById('slideCanvas')?.innerText||'').slice(0,120),
          status:document.getElementById('statusText')?.textContent||'',
          panelVisible:getComputedStyle(document.getElementById('slidePanel')).visibility!=='hidden'
        })""")
        shot=d/f"t{target}.png";p.screenshot(path=str(shot),full_page=False)
        out.append({"requestedMs":target,"actualMs":round(actual,2),**state,"screenshot":str(shot.relative_to(OUT))})
        c.close()
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
      wait_port()
      with sync_playwright() as pw:
        browser=pw.webkit.launch(headless=True)
        b=browser.new_context(viewport={"width":1280,"height":820},service_workers="block");p=b.new_page()
        p.goto(BASE+"/apps/presentations/index.html?suite=1",wait_until="load");p.wait_for_function("() => !!globalThis.InkDOS2Presentations?.PptxWriter")
        f44=fixture(p,44);f100=fixture(p,100);b.close()
        report={"productHead":os.environ.get("INKDOS_PRODUCT_HEAD","unknown"),"browser":"webkit",
          "numeric":{"44":numeric(browser,f44,44,5),"100":numeric(browser,f100,100,3)},
          "visual":{}}
        for theme in ("light","dark"):
          report["visual"][theme]={"44":visual(browser,f44,44,theme,TARGETS_44),"100":visual(browser,f100,100,theme,TARGETS_100)}
        browser.close()
      (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
      print(json.dumps(report["numeric"],indent=2))
    finally:
      server.terminate()
      try:server.wait(timeout=3)
      except subprocess.TimeoutExpired:server.kill()

if __name__=="__main__":main()

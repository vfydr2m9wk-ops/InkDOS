#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=int(os.environ.get("INKDOS_FIRST_SLIDE_AB_PORT","8881"))
BASE=f"http://127.0.0.1:{PORT}"
BROWSER=os.environ.get("BROWSER","webkit").strip().lower()
OUT=Path(os.environ.get("INKDOS_FIRST_SLIDE_AB_OUT",f"artifacts/first-slide-ab/{BROWSER}"))
COUNTS=[44,100,200]
ITERATIONS={44:5,100:3,200:3}
VISUAL_44=[100,150,200,250,300,400,800]
VISUAL_100=[150,250,400,600,800]

def wait_port(timeout:float=10.0)->None:
    end=time.time()+timeout
    while time.time()<end:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1",PORT))==0:return
        time.sleep(.1)
    raise RuntimeError("benchmark server did not start")

def median(vals):
    vals=[float(x) for x in vals if x is not None]
    return statistics.median(vals) if vals else None

def p95(vals):
    vals=sorted(float(x) for x in vals if x is not None)
    if not vals:return None
    return vals[max(0,min(len(vals)-1,round(.95*(len(vals)-1))))]

def stat(samples,key):
    vals=[s.get(key) for s in samples if s.get(key) is not None]
    return {"median":median(vals),"p95":p95(vals)}

def instrument(source:str)->str:
    candidate="slides.push(slide);if(i===0&&typeof onFirstSlide==='function')"
    if candidate in source:
        return source.replace(
            candidate,
            "slides.push(slide);if(i===0)global.__inkdosFirstSafe?.(performance.now());if(i===0&&typeof onFirstSlide==='function')",
            1,
        )
    baseline="const bg=sb?.color||'#ffffff';slides.push({id:`slide-${i+1}`,slideNumber:i+1,widthEmu:w,heightEmu:h,background:bg,backgroundImage:sb?.image||null,sourcePart:part,objects})}"
    if baseline in source:
        return source.replace(
            baseline,
            "const bg=sb?.color||'#ffffff';slides.push({id:`slide-${i+1}`,slideNumber:i+1,widthEmu:w,heightEmu:h,background:bg,backgroundImage:sb?.image||null,sourcePart:part,objects});if(i===0)global.__inkdosFirstSafe?.(performance.now())}",
            1,
        )
    raise RuntimeError("Could not instrument first-slide completion")

def fixture_script():
    return r"""async ({count,marker})=>{
      const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
      const s=new NS.PresentationSession();s.resetNew();
      const setTitle=(slide,text)=>{
        const o=slide.objects.find(x=>x.type==='text');o.text=text;
        o.paragraphs=M.normalizeParagraphs(null,text,o);
      };
      s.currentSlide.background='#17324D';setTitle(s.currentSlide,marker+' 1');
      const shape=s.addShape('ellipse');shape.fill='#22AA88';shape.x=4300000;shape.y=3300000;
      for(let i=2;i<=count;i++){s.addSlide();setTitle(s.currentSlide,marker+' '+i)}
      s.setCurrentByIndex(0);
      const bytes=await NS.PptxWriter.build(s);
      let raw='',chunk=0x8000;
      for(let i=0;i<bytes.length;i+=chunk)raw+=String.fromCharCode(...bytes.subarray(i,i+chunk));
      return {b64:btoa(raw),size:bytes.length};
    }"""

def main()->None:
    if BROWSER not in {"chromium","firefox","webkit"}:raise RuntimeError(BROWSER)
    OUT.mkdir(parents=True,exist_ok=True)
    source=(ROOT/"apps/presentations/io/pptx-open-controller.js").read_text(encoding="utf-8")
    instrumented=instrument(source)
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            browser=getattr(pw,BROWSER).launch(headless=True)
            page=browser.new_page(viewport={"width":1360,"height":900})
            errors=[]
            page.on("pageerror",lambda e:errors.append(f"pageerror: {e}"))
            page.on("console",lambda m:errors.append(f"console.error: {m.text}") if m.type=="error" else None)
            page.route("**/apps/presentations/io/pptx-open-controller.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body=instrumented))
            page.goto(BASE+"/apps/presentations/",wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session && !!globalThis.InkDOS2Presentations?.PptxWriter")

            results={}
            for count in COUNTS:
                samples=[]
                for iteration in range(ITERATIONS[count]):
                    marker=f"AB-{count}-{iteration}-{BROWSER}"
                    fixture=page.evaluate(fixture_script(),{"count":count,"marker":marker})
                    sample=page.evaluate(r"""async ({fixture,marker,count})=>{
                      const app=globalThis.__inkdosPresentations;
                      await app.newPresentation();
                      const raw=atob(fixture.b64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
                      const file=new File([bytes],'ab-'+count+'.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                      const canvas=document.getElementById('slideCanvas');
                      let safeAt=null,visualAt=null,previewAt=null,commitAt=null,previewClearedAt=null;
                      const longTasks=[],ticks=[];
                      let ticking=true,po=null;
                      globalThis.__inkdosFirstSafe=ts=>{if(safeAt==null)safeAt=ts};
                      if(globalThis.PerformanceObserver&&PerformanceObserver.supportedEntryTypes?.includes('longtask')){
                        po=new PerformanceObserver(list=>{for(const e of list.getEntries())longTasks.push({start:e.startTime,duration:e.duration})});
                        po.observe({entryTypes:['longtask']});
                      }
                      const tick=()=>{ticks.push(performance.now());if(ticking)setTimeout(tick,0)};
                      setTimeout(tick,0);
                      const originalReplace=app.session.replaceCandidate;
                      app.session.replaceCandidate=function(candidate,op){
                        if(commitAt==null)commitAt=performance.now();
                        return originalReplace.call(this,candidate,op);
                      };
                      const observe=()=>{
                        if(previewAt==null&&document.body.dataset.presentationOpeningPreview==='true')previewAt=performance.now();
                        if(previewClearedAt==null&&previewAt!=null&&document.body.dataset.presentationOpeningPreview!=='true')previewClearedAt=performance.now();
                        if(visualAt==null&&canvas.innerText.includes(marker)){
                          requestAnimationFrame(()=>{if(visualAt==null)visualAt=performance.now()});
                        }
                      };
                      const mo=new MutationObserver(observe);
                      mo.observe(document.body,{subtree:true,childList:true,attributes:true,characterData:true});
                      const start=performance.now();observe();
                      const ok=await app.open(file);
                      const openResolved=performance.now();
                      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                      observe();
                      ticking=false;await new Promise(r=>setTimeout(r,0));
                      mo.disconnect();po?.disconnect?.();app.session.replaceCandidate=originalReplace;globalThis.__inkdosFirstSafe=null;
                      const gaps=ticks.slice(1).map((v,i)=>v-ticks[i]).filter((_,i)=>ticks[i]>=start);
                      const lt=longTasks.filter(x=>x.start+x.duration>=start);
                      return {
                        count,ok,fixtureBytes:fixture.size,
                        firstSafeMs:safeAt==null?null:safeAt-start,
                        firstVisualMs:visualAt==null?null:visualAt-start,
                        previewVisibleMs:previewAt==null?null:previewAt-start,
                        fullCandidateMs:commitAt==null?null:commitAt-start,
                        previewClearedMs:previewClearedAt==null?null:previewClearedAt-start,
                        fullyInteractiveMs:openResolved-start,
                        openResolvedMs:openResolved-start,
                        maxTaskGapMs:gaps.length?Math.max(...gaps):0,
                        gapsOver50:gaps.filter(x=>x>50).length,
                        longTasks:lt.length,
                        maxLongTaskMs:lt.length?Math.max(...lt.map(x=>x.duration)):0,
                        previewWasUsed:previewAt!=null,
                        finalSlides:app.session.slides.length,
                        finalMarker:app.session.slides[0]?.objects?.some(o=>o.type==='text'&&o.text.includes(marker))||false
                      };
                    }""",{"fixture":fixture,"marker":marker,"count":count})
                    samples.append(sample)
                results[str(count)]=samples

            visual_meta={}
            if BROWSER=="webkit":
                for count,times in [(44,VISUAL_44),(100,VISUAL_100)]:
                    for theme in ["light","dark"]:
                        vp=browser.new_page(viewport={"width":1360,"height":900})
                        vp.route("**/apps/presentations/io/pptx-open-controller.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body=instrumented))
                        vp.goto(BASE+"/apps/presentations/",wait_until="load")
                        vp.wait_for_function("() => !!globalThis.__inkdosPresentations?.session && !!globalThis.InkDOS2Presentations?.PptxWriter")
                        vp.evaluate("(theme)=>globalThis.InkDOS2Presentations.Appearance.set(theme)",theme)
                        marker=f"VISUAL-{count}-{theme}"
                        fixture=vp.evaluate(fixture_script(),{"count":count,"marker":marker})
                        start=vp.evaluate(r"""({fixture,count})=>{
                          const raw=atob(fixture.b64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
                          const file=new File([bytes],'visual-'+count+'.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                          globalThis.__abVisualStart=performance.now();
                          globalThis.__abVisualPromise=globalThis.__inkdosPresentations.open(file);
                          return globalThis.__abVisualStart;
                        }""",{"fixture":fixture,"count":count})
                        key=f"{count}-{theme}";visual_meta[key]=[]
                        d=OUT/"visual"/str(count)/theme;d.mkdir(parents=True,exist_ok=True)
                        for target in times:
                            while True:
                                elapsed=vp.evaluate("performance.now()-globalThis.__abVisualStart")
                                remain=target-float(elapsed)
                                if remain<=1:break
                                vp.wait_for_timeout(min(remain,20))
                            state=vp.evaluate(r"""marker=>({
                              elapsed:performance.now()-globalThis.__abVisualStart,
                              startHidden:document.getElementById('startState')?.hidden,
                              preview:document.body.dataset.presentationOpeningPreview==='true',
                              canvasPreview:document.getElementById('slideCanvas')?.dataset.transientPreview==='true',
                              markerVisible:document.getElementById('slideCanvas')?.innerText.includes(marker)||false,
                              status:document.getElementById('statusText')?.textContent||'',
                              saveDisabled:document.getElementById('saveMenuBtn')?.disabled??null,
                              thumbs:document.querySelectorAll('#slidePanelInner .slide-thumb').length
                            })""",marker)
                            vp.screenshot(path=str(d/f"t{target}.png"),full_page=True)
                            visual_meta[key].append({"targetMs":target,**state})
                        await_ok=vp.evaluate("async()=>!!(await globalThis.__abVisualPromise)")
                        visual_meta[key].append({"openResolved":await_ok})
                        vp.close()

            browser.close()
            if errors:raise AssertionError({"browser":BROWSER,"errors":errors})

        metrics=["firstSafeMs","firstVisualMs","previewVisibleMs","fullCandidateMs","previewClearedMs","fullyInteractiveMs","openResolvedMs","maxTaskGapMs","gapsOver50","longTasks","maxLongTaskMs"]
        summary={}
        for count,samples in results.items():
            summary[count]={m:stat(samples,m) for m in metrics}
            summary[count]["previewUsedCount"]=sum(1 for x in samples if x["previewWasUsed"])
        report={
          "browser":BROWSER,
          "product_commit":os.environ.get("INKDOS_PRODUCT_COMMIT","unknown"),
          "variant":os.environ.get("INKDOS_AB_VARIANT","unknown"),
          "summary":summary,
          "samples":results,
          "visual":visual_meta,
          "definitions":{
            "firstSafeMs":"first slide fully decoded; benchmark-only probe immediately after slides.push",
            "firstVisualMs":"first requestAnimationFrame after canvas contains fixture marker",
            "previewVisibleMs":"transient-preview body state first observed; null on #209",
            "fullCandidateMs":"session.replaceCandidate invocation",
            "fullyInteractiveMs":"app.open promise resolution after atomic commit/onCommit"
          }
        }
        (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps(summary,indent=2))
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=="__main__":main()

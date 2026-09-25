#!/usr/bin/env python3
from __future__ import annotations
import base64,json,os,socket,statistics,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=int(os.environ.get("INKDOS_PREVIEW_OVERHEAD_PORT","8891"))
BASE=f"http://127.0.0.1:{PORT}"
OUT=Path(os.environ.get("INKDOS_PREVIEW_OVERHEAD_OUT","artifacts/pptx-preview-overhead-diagnostic"))
COUNTS=(44,100)
ITERS={44:5,100:3}
MODES=("current","one_raf","timeout_only")

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

def instrument_open(src:str)->str:
    old="slides.push(slide);if(i===0&&ids.length>10&&typeof onFirstSlide==='function')await onFirstSlide(JSON.parse(JSON.stringify(slide)))}return {fileName:"
    new=("slides.push(slide);"
         "if(i===0){global.__previewOverheadProbe?.('p0',{index:1});"
         "if(ids.length>10&&typeof onFirstSlide==='function'){global.__previewOverheadProbe?.('p1',{index:1});"
         "await onFirstSlide(JSON.parse(JSON.stringify(slide)));global.__previewOverheadProbe?.('p5',{index:1});global.__previewOverheadProbe?.('p6',{index:2})}}"
         "if(i===ids.length-1)global.__previewOverheadProbe?.('p7',{index:i+1})}"
         "global.__previewOverheadProbe?.('p8',{slideCount:slides.length});return {fileName:")
    if old not in src: raise RuntimeError("open-controller loop pattern changed")
    src=src.replace(old,new,1)
    old="if(!session.replaceCandidate(candidate,op))"
    new="global.__previewOverheadProbe?.('p9',{slideCount:candidate?.slides?.length||0});if(!session.replaceCandidate(candidate,op))"
    if old not in src: raise RuntimeError("replaceCandidate pattern changed")
    return src.replace(old,new,1)

def instrument_app(src:str,mode:str)->str:
    old=("async function showOpeningPreview({slide,op}){if(!slide||op!==session.operationId)return false;"
         "const state=$('startState'),workspace=$('workspace'),panelNode=$('slidePanel');"
         "previewState={op,startHidden:!!state?.hidden,startActive:state?.dataset?.active||'false'};"
         "surface.renderPreview(slide);zoom.applyForSlide(slide,{preserveFocus:false});adapter.center();"
         "if(panelNode)panelNode.style.visibility='hidden';"
         "if(workspace){workspace.dataset.openingPreview='true';workspace.setAttribute('aria-busy','true')}"
         "document.body.dataset.presentationOpeningPreview='true';dismissStartState();commands?.sync();"
         "return await new Promise(resolve=>requestAnimationFrame(()=>setTimeout(()=>resolve(!!previewState&&previewState.op===op&&session.operationId===op),0)))}")
    if mode=="current":
        schedule=("global.__previewOverheadProbe?.('schedule-start',{});"
                  "return await new Promise(resolve=>requestAnimationFrame(ts=>{"
                  "global.__previewOverheadProbe?.('p3',{frameTs:ts});"
                  "setTimeout(()=>{global.__previewOverheadProbe?.('p4',{});"
                  "resolve(!!previewState&&previewState.op===op&&session.operationId===op)},0)}))")
    elif mode=="one_raf":
        schedule=("global.__previewOverheadProbe?.('schedule-start',{});"
                  "return await new Promise(resolve=>requestAnimationFrame(ts=>{"
                  "global.__previewOverheadProbe?.('p3',{frameTs:ts});global.__previewOverheadProbe?.('p4',{});"
                  "resolve(!!previewState&&previewState.op===op&&session.operationId===op)}))")
    elif mode=="timeout_only":
        schedule=("global.__previewOverheadProbe?.('schedule-start',{});"
                  "return await new Promise(resolve=>setTimeout(()=>{global.__previewOverheadProbe?.('p4',{});"
                  "resolve(!!previewState&&previewState.op===op&&session.operationId===op)},0))")
    else: raise RuntimeError(mode)
    new=("async function showOpeningPreview({slide,op}){if(!slide||op!==session.operationId)return false;"
         "global.__previewOverheadProbe?.('preview-start',{});"
         "const state=$('startState'),workspace=$('workspace'),panelNode=$('slidePanel');"
         "previewState={op,startHidden:!!state?.hidden,startActive:state?.dataset?.active||'false'};"
         "const __dom0=performance.now();surface.renderPreview(slide);global.__previewOverheadProbe?.('p2',{domMs:performance.now()-__dom0});"
         "const __layout0=performance.now();zoom.applyForSlide(slide,{preserveFocus:false});adapter.center();"
         "global.__previewOverheadProbe?.('layout-done',{layoutMs:performance.now()-__layout0});"
         "if(panelNode)panelNode.style.visibility='hidden';"
         "if(workspace){workspace.dataset.openingPreview='true';workspace.setAttribute('aria-busy','true')}"
         "document.body.dataset.presentationOpeningPreview='true';dismissStartState();commands?.sync();"
         "global.__previewOverheadProbe?.('ui-done',{});"+schedule+"}")
    if old not in src: raise RuntimeError("showOpeningPreview pattern changed")
    return src.replace(old,new,1)

def fixture(page,count:int)->bytes:
    b64=page.evaluate(r"""async count=>{
      const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel,s=new NS.PresentationSession();s.resetNew();
      const setTitle=(slide,text)=>{const o=slide.objects[0];o.text=text;o.paragraphs=M.normalizeParagraphs(null,text,o)};
      setTitle(s.slides[0],'Preview overhead slide 1');
      for(let i=2;i<=count;i++){s.addSlide();setTitle(s.currentSlide,'Preview overhead slide '+i)}
      s.setCurrentByIndex(0);const bytes=await NS.PptxWriter.build(s);let raw='',chunk=0x8000;
      for(let i=0;i<bytes.length;i+=chunk)raw+=String.fromCharCode(...bytes.subarray(i,i+chunk));
      return btoa(raw)
    }""",count)
    return base64.b64decode(b64)

def sample(browser,open_src,app_src,data:bytes,count:int,mode:str):
    ctx=browser.new_context(viewport={"width":1280,"height":820},service_workers="block")
    ctx.route("**/apps/presentations/io/pptx-open-controller.js",lambda r:r.fulfill(status=200,content_type="application/javascript",body=open_src))
    ctx.route("**/apps/presentations/app.js",lambda r:r.fulfill(status=200,content_type="application/javascript",body=app_src))
    page=ctx.new_page()
    page.goto(BASE+"/apps/presentations/index.html?suite=1",wait_until="load",timeout=30000)
    page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session && !!globalThis.InkDOS2Presentations?.PptxWriter",timeout=30000)
    encoded=base64.b64encode(data).decode("ascii")
    result=page.evaluate(r"""async ({encoded,count,mode})=>{
      const raw=atob(encoded),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
      const file=new File([bytes],'overhead-'+count+'.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
      const events=[],ticks=[],longTasks=[];let ticking=true,po=null;
      globalThis.__previewOverheadProbe=(name,data={})=>events.push({name,t:performance.now(),...data});
      if(globalThis.PerformanceObserver&&PerformanceObserver.supportedEntryTypes?.includes('longtask')){
        po=new PerformanceObserver(list=>{for(const e of list.getEntries())longTasks.push({start:e.startTime,duration:e.duration})});
        po.observe({entryTypes:['longtask']});
      }
      const tick=()=>{ticks.push(performance.now());if(ticking)setTimeout(tick,0)};setTimeout(tick,0);
      const wall0=performance.now();
      const ok=await globalThis.__inkdosPresentations.open(file);
      const wall1=performance.now();events.push({name:'p10',t:wall1});
      await new Promise(r=>setTimeout(r,10));ticking=false;po?.disconnect?.();globalThis.__previewOverheadProbe=null;
      const one=n=>events.find(e=>e.name===n);
      const t=n=>one(n)?.t??null;
      const d=(a,b)=>t(a)!=null&&t(b)!=null?t(b)-t(a):null;
      const p1=t('p1'),p10=t('p10');
      const gaps=ticks.slice(1).map((v,i)=>({start:ticks[i],gap:v-ticks[i]})).filter(x=>p1==null||x.start>=p1);
      const lt=longTasks.filter(x=>p1==null||x.start+x.duration>=p1);
      return {
        count,mode,ok,wallOpenMs:wall1-wall0,
        p0:t('p0')-wall0,p1:t('p1')-wall0,p2:t('p2')-wall0,p3:t('p3')!=null?t('p3')-wall0:null,
        p4:t('p4')-wall0,p5:t('p5')-wall0,p6:t('p6')-wall0,p7:t('p7')-wall0,p8:t('p8')-wall0,p9:t('p9')-wall0,p10:p10-wall0,
        previewCallbackMs:d('p1','p5'),preScheduleCpuMs:d('p1','schedule-start'),
        domMs:one('p2')?.domMs??null,layoutMs:one('layout-done')?.layoutMs??null,
        scheduleWaitMs:d('schedule-start','p4'),resumeDelayMs:d('p4','p6'),
        postResumeDecodeMs:d('p6','p8'),commitToResolvedMs:d('p9','p10'),
        maxTaskGapMs:gaps.length?Math.max(...gaps.map(x=>x.gap)):0,gapsOver50:gaps.filter(x=>x.gap>50).length,
        longTasks:lt.length,maxLongTaskMs:lt.length?Math.max(...lt.map(x=>x.duration)):0,
        previewDataset:document.body.dataset.presentationOpeningPreview||null,
        events
      };
    }""",{"encoded":encoded,"count":count,"mode":mode})
    ctx.close();return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    open_raw=(ROOT/"apps/presentations/io/pptx-open-controller.js").read_text(encoding="utf-8")
    app_raw=(ROOT/"apps/presentations/app.js").read_text(encoding="utf-8")
    open_src=instrument_open(open_raw)
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
      wait_port()
      with sync_playwright() as pw:
        browser=pw.webkit.launch(headless=True)
        base=browser.new_context(viewport={"width":1280,"height":820},service_workers="block");p=base.new_page()
        p.goto(BASE+"/apps/presentations/index.html?suite=1",wait_until="load",timeout=30000)
        p.wait_for_function("() => !!globalThis.InkDOS2Presentations?.PptxWriter",timeout=30000)
        fixtures={n:fixture(p,n) for n in COUNTS};base.close()
        results={}
        for mode in MODES:
          app_src=instrument_app(app_raw,mode)
          results[mode]={}
          for count in COUNTS:
            results[mode][str(count)]=[sample(browser,open_src,app_src,fixtures[count],count,mode) for _ in range(ITERS[count])]
        browser.close()
      metrics=("wallOpenMs","previewCallbackMs","preScheduleCpuMs","domMs","layoutMs","scheduleWaitMs","resumeDelayMs",
               "postResumeDecodeMs","commitToResolvedMs","maxTaskGapMs","gapsOver50","longTasks","maxLongTaskMs",
               "p0","p1","p2","p3","p4","p5","p6","p7","p8","p9","p10")
      summary={}
      for mode,by_count in results.items():
        summary[mode]={}
        for count,rows in by_count.items():
          summary[mode][count]={}
          for m in metrics:
            vals=[r[m] for r in rows if r.get(m) is not None]
            summary[mode][count][m]={"median":med(vals),"p95":p95(vals)}
      report={"browser":"webkit","baseline":"PR #211 / a89c8c51c214514c4ce52a55976793ee8d7be483",
              "modes":MODES,"counts":COUNTS,"iterations":ITERS,"summary":summary,"samples":results,
              "notes":[
                "current preserves the exact rAF -> setTimeout(0) preview yield.",
                "one_raf and timeout_only are diagnostic-only scheduling substitutions served via Playwright routing; repository product bytes are unchanged.",
                "P0/P1 occur after slide 1 is fully decoded and after the policy security gate; P6 is decoder resume immediately after onFirstSlide resolves.",
                "This diagnostic measures scheduling cost, not visual proof. Visual preservation must be tested separately before any product candidate."
              ]}
      (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
      print(json.dumps(summary,indent=2))
    finally:
      server.terminate()
      try:server.wait(timeout=3)
      except subprocess.TimeoutExpired:server.kill()

if __name__=="__main__":main()

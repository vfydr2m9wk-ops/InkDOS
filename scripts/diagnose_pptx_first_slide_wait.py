#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=int(os.environ.get("INKDOS_PPTX_SLIDE_DIAG_PORT","8871"))
BASE=f"http://127.0.0.1:{PORT}"
BROWSER_NAME=os.environ.get("BROWSER","webkit").strip().lower()
OUT=Path(os.environ.get("INKDOS_PPTX_SLIDE_DIAG_OUT",f"artifacts/pptx-first-slide-diagnostic/{BROWSER_NAME}"))
COUNTS=[1,10,44,100,200]
ITERATIONS={1:3,10:3,44:5,100:3,200:3}

def wait_port(timeout:float=10.0)->None:
    deadline=time.time()+timeout
    while time.time()<deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1",PORT))==0:return
        time.sleep(.1)
    raise RuntimeError("Local diagnostic server did not start")

def median(values):
    vals=[float(v) for v in values if v is not None]
    return statistics.median(vals) if vals else None

def p95(values):
    vals=sorted(float(v) for v in values if v is not None)
    if not vals:return None
    return vals[max(0,min(len(vals)-1,round(.95*(len(vals)-1))))]

def stat(samples,key):
    vals=[s.get(key) for s in samples if s.get(key) is not None]
    return {"median":median(vals),"p95":p95(vals)}

def instrument_controller(source:str)->str:
    replacements=[
      (
        "async function decodePptx(bytes,fileName){if(!global.JSZip)",
        "async function decodePptx(bytes,fileName){const __probe=(event,data={})=>{try{global.__inkdosPptxDecodeProbe?.(event,{...data,now:performance.now()})}catch(_){}};__probe('decode-start');if(!global.JSZip)"
      ),
      (
        "const slides=[],compat=[],sharedContext={layouts:new Map(),masters:new Map(),themes:new Map()};for(let i=0;i<ids.length;i++){const rel=prels.get(rid(ids[i])),part=rel?.target;",
        "const slides=[],compat=[],sharedContext={layouts:new Map(),masters:new Map(),themes:new Map()};__probe('package-ready',{slideCount:ids.length});for(let i=0;i<ids.length;i++){const rel=prels.get(rid(ids[i])),part=rel?.target;__probe('slide-start',{index:i+1,part});"
      ),
      (
        "const sd=parseXml(await z.async('text'),",
        "__probe('slide-xml-read-start',{index:i+1,part});const __slideXml=await z.async('text');__probe('slide-xml-read-end',{index:i+1,part});const sd=parseXml(__slideXml,"
      ),
      (
        "),ctx=await contextForSlide(zip,part,w,h,sharedContext),tree=first(sd,'spTree');",
        ");__probe('slide-xml-parse-end',{index:i+1,part});__probe('context-start',{index:i+1,part});const ctx=await contextForSlide(zip,part,w,h,sharedContext);__probe('context-end',{index:i+1,part});const tree=first(sd,'spTree');"
      ),
      (
        "const objects=tree?await parseTree(zip,tree,ctx.srels,w,h,ctx.theme,ctx.map,ctx.layoutMap,ctx.masterMap,compat,part):[];const sb=await backgroundOf(sd,ctx.theme,ctx.map,ctx.srels,zip);const bg=sb?.color||'#ffffff';slides.push({id:`slide-${i+1}`,slideNumber:i+1,widthEmu:w,heightEmu:h,background:bg,backgroundImage:sb?.image||null,sourcePart:part,objects})}",
        "__probe('objects-start',{index:i+1,part});const objects=tree?await parseTree(zip,tree,ctx.srels,w,h,ctx.theme,ctx.map,ctx.layoutMap,ctx.masterMap,compat,part):[];__probe('objects-end',{index:i+1,part,objectCount:objects.length});__probe('background-start',{index:i+1,part});const sb=await backgroundOf(sd,ctx.theme,ctx.map,ctx.srels,zip);__probe('background-end',{index:i+1,part});const bg=sb?.color||'#ffffff';const __slide={id:`slide-${i+1}`,slideNumber:i+1,widthEmu:w,heightEmu:h,background:bg,backgroundImage:sb?.image||null,sourcePart:part,objects};slides.push(__slide);__probe('slide-complete',{index:i+1,part,objectCount:objects.length,slide:global.__inkdosPptxDecodeProbeIncludeSlide?__slide:null})}"
      ),
      (
        "return {fileName:/\\.pptx$/i.test(fileName)?fileName:fileName+'.pptx',sourceKind:'pptx',sourceBytes:new Uint8Array(bytes),sourceSlideParts:slides.map(s=>s.sourcePart),slides,compatibility:[...new Set(compat)].slice(0,30)}}",
        "__probe('last-slide-complete',{slideCount:slides.length});const __candidate={fileName:/\\.pptx$/i.test(fileName)?fileName:fileName+'.pptx',sourceKind:'pptx',sourceBytes:new Uint8Array(bytes),sourceSlideParts:slides.map(s=>s.sourcePart),slides,compatibility:[...new Set(compat)].slice(0,30)};__probe('candidate-ready',{slideCount:slides.length});return __candidate}"
      )
    ]
    for idx,(old,new) in enumerate(replacements,1):
        if old not in source:
            raise RuntimeError(f"instrumentation pattern {idx} changed")
        source=source.replace(old,new,1)
    return source

def main()->None:
    if BROWSER_NAME not in {"chromium","firefox","webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={BROWSER_NAME}")
    OUT.mkdir(parents=True,exist_ok=True)
    controller_path=ROOT/"apps/presentations/io/pptx-open-controller.js"
    instrumented=instrument_controller(controller_path.read_text(encoding="utf-8"))

    server=subprocess.Popen(
        [sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],
        cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser=getattr(pw,BROWSER_NAME).launch(headless=True)
            page=browser.new_page(viewport={"width":1360,"height":900})
            errors=[]
            page.on("pageerror",lambda exc:errors.append(f"pageerror: {exc}"))
            page.on("console",lambda msg:errors.append(f"console.error: {msg.text}") if msg.type=="error" else None)
            page.route("**/apps/presentations/io/pptx-open-controller.js",lambda route:route.fulfill(
                status=200,content_type="application/javascript",body=instrumented
            ))
            page.goto(BASE+"/apps/presentations/",wait_until="load")
            page.wait_for_function(
                "() => !!globalThis.__inkdosPresentations?.session && "
                "!!globalThis.InkDOS2Presentations?.PptxWriter && "
                "!!globalThis.InkDOS2Presentations?.PptxOpenController"
            )

            fixtures={}
            for count in COUNTS:
                fixtures[count]=page.evaluate(r"""async count=>{
                    const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
                    const src=new NS.PresentationSession();src.resetNew();
                    const setTitle=(slide,text)=>{
                      const o=slide.objects[0];o.text=text;o.paragraphs=M.normalizeParagraphs(null,text,o);
                    };
                    setTitle(src.slides[0],'Slide 1 diagnostic');
                    for(let i=2;i<=count;i++){src.addSlide();setTitle(src.currentSlide,'Slide '+i+' diagnostic')}
                    src.setCurrentByIndex(0);
                    const bytes=await NS.PptxWriter.build(src);
                    let s='',chunk=0x8000;
                    for(let i=0;i<bytes.length;i+=chunk)s+=String.fromCharCode(...bytes.subarray(i,i+chunk));
                    return {b64:btoa(s),size:bytes.length};
                }""",count)

            results={}
            for count in COUNTS:
                samples=[]
                for _ in range(ITERATIONS[count]):
                    sample=page.evaluate(r"""async ({fixture,count})=>{
                      const NS=globalThis.InkDOS2Presentations;
                      const raw=atob(fixture.b64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
                      const events=[],zipReads=[],longTasks=[],ticks=[];
                      let decodeStartAbs=null,ticking=true,po=null;
                      globalThis.__inkdosPptxDecodeProbeIncludeSlide=false;
                      globalThis.__inkdosPptxDecodeProbe=(event,data)=>{
                        events.push({event,...data});
                        if(event==='decode-start')decodeStartAbs=data.now;
                      };

                      const realLoad=JSZip.loadAsync;
                      JSZip.loadAsync=async function(...args){
                        const zip=await realLoad.apply(this,args),realFile=zip.file.bind(zip),decorated=new WeakSet();
                        zip.file=function(name,...rest){
                          const obj=realFile(name,...rest);
                          if(typeof name==='string'&&obj&&typeof obj.async==='function'&&!decorated.has(obj)){
                            decorated.add(obj);
                            const realAsync=obj.async.bind(obj);
                            obj.async=async function(type,...a){
                              const start=performance.now(),value=await realAsync(type,...a),end=performance.now();
                              zipReads.push({part:name,type,start,end,duration:end-start});
                              return value;
                            };
                          }
                          return obj;
                        };
                        return zip;
                      };

                      if(globalThis.PerformanceObserver&&PerformanceObserver.supportedEntryTypes?.includes('longtask')){
                        po=new PerformanceObserver(list=>{for(const e of list.getEntries())longTasks.push({start:e.startTime,duration:e.duration})});
                        po.observe({entryTypes:['longtask']});
                      }
                      const tick=()=>{ticks.push(performance.now());if(ticking)setTimeout(tick,0)};
                      setTimeout(tick,0);

                      const secureStart=performance.now();
                      let candidate;
                      try{candidate=await NS.PptxOpenController.decodePptx(bytes,'diag-'+count+'.pptx')}
                      finally{
                        const secureEnd=performance.now();
                        ticking=false;await new Promise(r=>setTimeout(r,0));po?.disconnect?.();
                        JSZip.loadAsync=realLoad;
                        globalThis.__inkdosPptxDecodeProbe=null;

                        const ev=(name,index=null)=>events.find(e=>e.event===name&&(index==null||e.index===index));
                        const at=(name,index=null)=>ev(name,index)?.now??null;
                        const t0=at('decode-start'),t1=at('package-ready');
                        const complete=i=>at('slide-complete',i);
                        const n=count;
                        const i25=Math.max(1,Math.ceil(n*.25)),i50=Math.max(1,Math.ceil(n*.50)),i75=Math.max(1,Math.ceil(n*.75));
                        const slideDurations=[];
                        for(let i=1;i<=n;i++){
                          const st=at('slide-start',i),en=complete(i);
                          if(st!=null&&en!=null)slideDurations.push(en-st);
                        }
                        const afterFirst=slideDurations.slice(1);
                        const sumPhase=(startName,endName)=>{
                          let sum=0;
                          for(let i=1;i<=n;i++){
                            const a=at(startName,i),b=at(endName,i);
                            if(a!=null&&b!=null)sum+=b-a;
                          }
                          return sum;
                        };
                        const decoderReads=zipReads.filter(x=>t0!=null&&x.start>=t0);
                        const slideXmlRead=decoderReads.filter(x=>/^ppt\/slides\/slide\d+\.xml$/i.test(x.part)&&x.type==='text').reduce((a,x)=>a+x.duration,0);
                        const slideRelsRead=decoderReads.filter(x=>/^ppt\/slides\/_rels\/slide\d+\.xml\.rels$/i.test(x.part)&&x.type==='text').reduce((a,x)=>a+x.duration,0);
                        const mediaRead=decoderReads.filter(x=>/^ppt\/media\//i.test(x.part)).reduce((a,x)=>a+x.duration,0);
                        const phase={
                          packageSetupMs:t0!=null&&t1!=null?t1-t0:null,
                          slideXmlReadMs:slideXmlRead,
                          slideXmlParseMs:sumPhase('slide-xml-read-end','slide-xml-parse-end'),
                          contextMs:sumPhase('context-start','context-end'),
                          objectsMs:sumPhase('objects-start','objects-end'),
                          backgroundMs:sumPhase('background-start','background-end'),
                          slideRelsReadMs:slideRelsRead,
                          mediaReadMs:mediaRead
                        };
                        const decodeEnd=at('candidate-ready'),decodeTotal=t0!=null&&decodeEnd!=null?decodeEnd-t0:null;
                        const known=Object.values(phase).filter(v=>typeof v==='number').reduce((a,v)=>a+v,0);
                        const gaps=ticks.slice(1).map((v,i)=>v-ticks[i]).filter((_,i)=>ticks[i]>= (t0??secureStart));
                        const lt=longTasks.filter(x=>t0!=null&&x.start+x.duration>=t0);
                        globalThis.__diagResult={
                          count,fixtureBytes:fixture.size,
                          securityBeforeDecodeMs:t0!=null?t0-secureStart:null,
                          secureTotalMs:secureEnd-secureStart,
                          decodeTotalMs:decodeTotal,
                          t0:0,
                          t1:t1!=null?t1-t0:null,
                          t2:at('slide-xml-read-end',1)!=null?at('slide-xml-read-end',1)-t0:null,
                          t3:at('context-end',1)!=null?at('context-end',1)-t0:null,
                          t4:complete(1)!=null?complete(1)-t0:null,
                          t5:n>=2&&complete(2)!=null?complete(2)-t0:null,
                          t6:n>=10&&complete(10)!=null?complete(10)-t0:null,
                          t7:complete(i25)!=null?complete(i25)-t0:null,
                          t8:complete(i50)!=null?complete(i50)-t0:null,
                          t9:complete(i75)!=null?complete(i75)-t0:null,
                          t10:complete(n)!=null?complete(n)-t0:null,
                          t11:decodeEnd!=null?decodeEnd-t0:null,
                          firstWaitMs:(complete(1)!=null&&complete(n)!=null)?complete(n)-complete(1):0,
                          firstSlideMs:slideDurations[0]??null,
                          meanAfterFirstMs:afterFirst.length?afterFirst.reduce((a,v)=>a+v,0)/afterFirst.length:0,
                          medianSlideMs:slideDurations.length?slideDurations.slice().sort((a,b)=>a-b)[Math.floor(slideDurations.length/2)]:null,
                          p95SlideMs:slideDurations.length?slideDurations.slice().sort((a,b)=>a-b)[Math.min(slideDurations.length-1,Math.floor(slideDurations.length*.95))]:null,
                          maxSlideMs:slideDurations.length?Math.max(...slideDurations):null,
                          phase,
                          otherMs:decodeTotal!=null?Math.max(0,decodeTotal-known):null,
                          maxTaskGapMs:gaps.length?Math.max(...gaps):0,
                          gapsOver50:gaps.filter(x=>x>50).length,
                          longTasks:lt.length,
                          maxLongTaskMs:lt.length?Math.max(...lt.map(x=>x.duration)):0,
                          candidateSlides:candidate?.slides?.length??0
                        };
                      }
                      return globalThis.__diagResult;
                    }""",{"fixture":fixtures[count],"count":count})
                    samples.append(sample)
                results[str(count)]=samples

            # Separate semantic proof: snapshot first slide at T4 and compare with final candidate.
            semantics=page.evaluate(r"""async fixture=>{
              const NS=globalThis.InkDOS2Presentations,raw=atob(fixture.b64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
              let firstSnapshot=null,firstCompleteAt=null,finalAt=null;
              globalThis.__inkdosPptxDecodeProbeIncludeSlide=true;
              globalThis.__inkdosPptxDecodeProbe=(event,data)=>{
                if(event==='slide-complete'&&data.index===1){
                  firstSnapshot=JSON.parse(JSON.stringify(data.slide));
                  firstCompleteAt=data.now;
                }
                if(event==='candidate-ready')finalAt=data.now;
              };
              const candidate=await NS.PptxOpenController.decodePptx(bytes,'semantics-44.pptx');
              globalThis.__inkdosPptxDecodeProbe=null;
              globalThis.__inkdosPptxDecodeProbeIncludeSlide=false;
              return {
                equal:JSON.stringify(firstSnapshot)===JSON.stringify(candidate.slides[0]),
                firstCompleteAt,finalAt,
                waitMs:(firstCompleteAt!=null&&finalAt!=null)?finalAt-firstCompleteAt:null,
                firstObjectCount:firstSnapshot?.objects?.length??null,
                finalObjectCount:candidate.slides[0]?.objects?.length??null
              };
            }""",fixtures[44])

            # Full-open markers T12/T13, separate from decoder phase timing.
            full_open={}
            for count in [44,100,200]:
                samples=[]
                for _ in range(3):
                    samples.append(page.evaluate(r"""async ({fixture,count})=>{
                      const app=globalThis.__inkdosPresentations;
                      const raw=atob(fixture.b64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
                      const file=new File([bytes],'open-'+count+'.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                      let decodeT0=null,replaceAt=null,visibleAt=null;
                      globalThis.__inkdosPptxDecodeProbe=(event,data)=>{if(event==='decode-start'&&decodeT0==null)decodeT0=data.now};
                      const original=app.session.replaceCandidate;
                      app.session.replaceCandidate=function(candidate,op){
                        replaceAt=performance.now();
                        return original.call(this,candidate,op);
                      };
                      const canvas=document.getElementById('slideCanvas');
                      const observer=new MutationObserver(()=>{
                        if(replaceAt!=null&&visibleAt==null&&canvas.dataset.slideId){
                          requestAnimationFrame(ts=>{if(visibleAt==null)visibleAt=ts});
                        }
                      });
                      observer.observe(canvas,{childList:true,subtree:true,attributes:true,attributeFilter:['data-slide-id']});
                      const wallStart=performance.now();
                      const ok=await app.open(file);
                      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                      observer.disconnect();
                      app.session.replaceCandidate=original;
                      globalThis.__inkdosPptxDecodeProbe=null;
                      return {
                        ok,wallOpenMs:performance.now()-wallStart,
                        t12:decodeT0!=null&&replaceAt!=null?replaceAt-decodeT0:null,
                        t13:decodeT0!=null&&visibleAt!=null?visibleAt-decodeT0:null,
                        decodeToVisibleGapMs:replaceAt!=null&&visibleAt!=null?visibleAt-replaceAt:null
                      };
                    }""",{"fixture":fixtures[count],"count":count}))
                full_open[str(count)]=samples

            browser.close()
            if errors: raise AssertionError({"browser":BROWSER_NAME,"errors":errors})

        metrics=[
          "securityBeforeDecodeMs","secureTotalMs","decodeTotalMs","t1","t2","t3","t4","t5","t6","t7","t8","t9","t10","t11",
          "firstWaitMs","firstSlideMs","meanAfterFirstMs","medianSlideMs","p95SlideMs","maxSlideMs",
          "otherMs","maxTaskGapMs","gapsOver50","longTasks","maxLongTaskMs"
        ]
        summary={}
        for count,samples in results.items():
            summary[count]={m:stat(samples,m) for m in metrics}
            for phase in ["packageSetupMs","slideXmlReadMs","slideXmlParseMs","contextMs","objectsMs","backgroundMs","slideRelsReadMs","mediaReadMs"]:
                vals=[s["phase"].get(phase) for s in samples]
                summary[count][phase]={"median":median(vals),"p95":p95(vals)}
        full_summary={}
        for count,samples in full_open.items():
            full_summary[count]={m:stat(samples,m) for m in ["wallOpenMs","t12","t13","decodeToVisibleGapMs"]}

        report={
          "browser":BROWSER_NAME,
          "baseline":"PR #209 / 25524f0a8135846a3fe78b2236dc93aac547a5e3",
          "counts":COUNTS,
          "iterations":ITERATIONS,
          "summary":summary,
          "samples":results,
          "semantic_first_slide":semantics,
          "full_open_summary":full_summary,
          "full_open_samples":full_open,
          "definitions":{
            "T0":"original decodePptx begins after full security wrapper validation",
            "T1":"presentation.xml, presentation rels, dimensions and slide order ready",
            "T2":"slide 1 XML text available",
            "T3":"slide 1 shared context/slide rels ready",
            "T4":"slide 1 fully decoded and pushed to local candidate slides array",
            "T5":"slide 2 fully decoded",
            "T6":"slide 10 fully decoded",
            "T7":"25% of slides fully decoded",
            "T8":"50% fully decoded",
            "T9":"75% fully decoded",
            "T10":"last slide fully decoded",
            "T11":"final candidate object assembled",
            "T12":"session.replaceCandidate called during full app open",
            "T13":"first rAF after committed slide canvas mutation during full app open"
          },
          "notes":[
            "The browser receives an instrumented copy of pptx-open-controller.js via Playwright route interception; repository product files are unchanged.",
            "Security timing is separated because the policy wrapper validates ZIP structure, CRC, XML budgets and forbidden DTD/entity declarations before the original decoder starts.",
            "Synthetic scaling fixtures contain text objects only; media/table phase cost is therefore expected to be zero or near zero.",
            "Phase totals are measured wall-time buckets and can overlap with zip-read submetrics; do not sum slideRelsReadMs on top of contextMs when computing percentages."
          ]
        }
        (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps({"summary":summary,"semantic_first_slide":semantics,"full_open_summary":full_summary},indent=2))
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=="__main__":main()

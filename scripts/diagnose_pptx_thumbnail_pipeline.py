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

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("INKDOS_PPTX_THUMB_DIAG_PORT", "8861"))
BASE = f"http://127.0.0.1:{PORT}"
BROWSER_NAME = os.environ.get("BROWSER", "webkit").strip().lower()
OUT = Path(os.environ.get("INKDOS_PPTX_THUMB_DIAG_OUT", f"artifacts/pptx-thumbnail-diagnostic/{BROWSER_NAME}"))
COUNTS = [1, 10, 44, 100, 200]
ITERATIONS = {1: 3, 10: 3, 44: 5, 100: 3, 200: 2}

def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local diagnostic server did not start")

def median(values):
    values = [float(v) for v in values if v is not None]
    return statistics.median(values) if values else None

def p95(values):
    values = sorted(float(v) for v in values if v is not None)
    if not values:
        return None
    return values[max(0, min(len(values)-1, round(.95*(len(values)-1))))]

def stat(samples, key):
    vals=[s.get(key) for s in samples if s.get(key) is not None]
    return {"median": median(vals), "p95": p95(vals)}

INIT_SCRIPT = r"""
(() => {
  const NS = globalThis.InkDOS2Presentations = globalThis.InkDOS2Presentations || {};
  const wrapFactoryProperty = (name, kind) => {
    let stored;
    Object.defineProperty(NS, name, {
      configurable: true,
      enumerable: true,
      get(){ return stored; },
      set(value){
        if(!value?.create){ stored=value; return; }
        const originalCreate=value.create;
        stored=Object.freeze({
          ...value,
          create(options){
            const inner=originalCreate(options);
            if(kind==='surface'){
              return Object.freeze({
                ...inner,
                render(...args){
                  const d=globalThis.__pptxThumbDiag;
                  if(d?.active && d.marks.t4==null)d.marks.t4=performance.now();
                  const t0=performance.now();
                  const result=inner.render(...args);
                  const t1=performance.now();
                  if(d?.active){
                    d.marks.surfaceEnd=t1;
                    d.surfaceMs=(d.surfaceMs||0)+(t1-t0);
                    if(d.marks.t5dom==null)d.marks.t5dom=t1;
                    requestAnimationFrame(ts=>{
                      if(d.active && d.marks.t5==null)d.marks.t5=ts;
                    });
                  }
                  return result;
                }
              });
            }
            return Object.freeze({
              ...inner,
              render(...args){
                const d=globalThis.__pptxThumbDiag;
                if(d?.active && d.marks.t6==null)d.marks.t6=performance.now();
                const t0=performance.now();
                const result=inner.render(...args);
                const t1=performance.now();
                if(d?.active){
                  d.marks.panelEnd=t1;
                  d.panelMs=(d.panelMs||0)+(t1-t0);
                  const innerEl=document.getElementById('slidePanelInner');
                  d.thumbCount=innerEl?.querySelectorAll('.slide-thumb').length||0;
                  if(d.marks.t7==null)d.marks.t7=t1;
                  if(d.marks.t9==null)d.marks.t9=t1;
                  requestAnimationFrame(ts=>{
                    if(!d.active)return;
                    const panel=document.getElementById('slidePanel');
                    const pr=panel?.getBoundingClientRect();
                    let visible=0;
                    if(pr){
                      for(const el of document.querySelectorAll('#slidePanelInner .slide-thumb')){
                        const r=el.getBoundingClientRect();
                        if(r.bottom>pr.top && r.top<pr.bottom)visible++;
                      }
                    }
                    d.visibleThumbs=visible;
                    if(d.marks.t8==null)d.marks.t8=ts;
                    if(d.marks.panelPaint==null)d.marks.panelPaint=ts;
                  });
                }
                return result;
              }
            });
          }
        });
      }
    });
  };
  wrapFactoryProperty('SlideSurface','surface');
  wrapFactoryProperty('SlidePanelController','panel');
})();
"""

def main() -> None:
    if BROWSER_NAME not in {"chromium","firefox","webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={BROWSER_NAME}")
    OUT.mkdir(parents=True, exist_ok=True)
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
            page.on("pageerror",lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console",lambda msg: errors.append(f"console.error: {msg.text}") if msg.type=="error" else None)
            page.add_init_script(INIT_SCRIPT)
            page.goto(BASE+"/apps/presentations/",wait_until="load")
            page.wait_for_function(
                "() => !!globalThis.__inkdosPresentations?.session && "
                "!!globalThis.InkDOS2Presentations?.PptxWriter"
            )

            fixtures={}
            for count in COUNTS:
                fixtures[count]=page.evaluate(
                    r"""async count => {
                      const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
                      const src=new NS.PresentationSession();src.resetNew();
                      const setTitle=(slide,text)=>{
                        const o=slide.objects[0];o.text=text;
                        o.paragraphs=M.normalizeParagraphs(null,text,o);
                      };
                      setTitle(src.slides[0],'Thumb diagnostic slide 1');
                      for(let i=2;i<=count;i++){src.addSlide();setTitle(src.currentSlide,'Thumb diagnostic slide '+i)}
                      src.setCurrentByIndex(0);
                      const bytes=await NS.PptxWriter.build(src);
                      let s='',chunk=0x8000;
                      for(let i=0;i<bytes.length;i+=chunk)s+=String.fromCharCode(...bytes.subarray(i,i+chunk));
                      return {b64:btoa(s),size:bytes.length};
                    }""",count
                )

            results={}
            for count in COUNTS:
                samples=[]
                for _ in range(ITERATIONS[count]):
                    sample=page.evaluate(
                        r"""async ({fixture,count}) => {
                          const app=globalThis.__inkdosPresentations;
                          const raw=atob(fixture.b64);
                          const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
                          const file=new File([bytes],'thumb-diag-'+count+'.pptx',{
                            type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                          });
                          const realArrayBuffer=file.arrayBuffer.bind(file);
                          const marks={};
                          const diag=globalThis.__pptxThumbDiag={
                            active:true,marks,surfaceMs:0,panelMs:0,thumbCount:0,visibleThumbs:0
                          };

                          const longTasks=[];
                          let po=null;
                          if(globalThis.PerformanceObserver &&
                             PerformanceObserver.supportedEntryTypes?.includes('longtask')){
                            po=new PerformanceObserver(list=>{
                              for(const e of list.getEntries())longTasks.push({start:e.startTime,duration:e.duration});
                            });
                            po.observe({entryTypes:['longtask']});
                          }

                          Object.defineProperty(file,'arrayBuffer',{
                            configurable:true,
                            value:async()=>{
                              const out=await realArrayBuffer();
                              if(diag.active && marks.t1==null)marks.t1=performance.now();
                              return out;
                            }
                          });

                          const realReplace=app.session.replaceCandidate.bind(app.session);
                          app.session.replaceCandidate=function(candidate,op){
                            if(diag.active && marks.t2==null)marks.t2=performance.now();
                            const out=realReplace(candidate,op);
                            if(diag.active && marks.t3==null){
                              marks.t3=performance.now();
                              setTimeout(()=>{
                                if(diag.active && marks.t10==null)marks.t10=performance.now();
                              },0);
                            }
                            return out;
                          };

                          const ticks=[];
                          let ticking=true;
                          const tick=()=>{
                            ticks.push(performance.now());
                            if(ticking)setTimeout(tick,0);
                          };
                          setTimeout(tick,0);

                          marks.t0=performance.now();
                          const ok=await app.open(file);
                          marks.openResolved=performance.now();

                          await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
                          if(marks.t10==null)await new Promise(resolve=>setTimeout(resolve,0));
                          ticking=false;
                          await new Promise(resolve=>setTimeout(resolve,0));
                          po?.disconnect?.();
                          diag.active=false;
                          app.session.replaceCandidate=realReplace;

                          const tickGaps=ticks.slice(1).map((v,i)=>v-ticks[i]);
                          const postModelLong=longTasks.filter(e=>marks.t2!=null && e.start+e.duration>=marks.t2);

                          const p0=performance.now();
                          app.panel.render({ensureActive:false});
                          const p1=performance.now();
                          const panel=document.getElementById('slidePanel');
                          const pr=panel?.getBoundingClientRect();
                          let visible=0;
                          if(pr){
                            for(const el of document.querySelectorAll('#slidePanelInner .slide-thumb')){
                              const r=el.getBoundingClientRect();
                              if(r.bottom>pr.top && r.top<pr.bottom)visible++;
                            }
                          }

                          const rel=(x)=>x==null?null:x-marks.t0;
                          const firstUsefulAbs=Math.max(
                            marks.t5??marks.t5dom??marks.openResolved,
                            marks.t10??marks.openResolved
                          );
                          return {
                            count,ok,fixtureBytes:fixture.size,
                            t0:0,t1:rel(marks.t1),t2:rel(marks.t2),t3:rel(marks.t3),
                            t4:rel(marks.t4),t5dom:rel(marks.t5dom),t5:rel(marks.t5),
                            t6:rel(marks.t6),t7:rel(marks.t7),t8:rel(marks.t8),
                            t9:rel(marks.t9),t10:rel(marks.t10),
                            openResolved:rel(marks.openResolved),
                            decodeToCandidateMs:(marks.t2!=null&&marks.t1!=null)?marks.t2-marks.t1:null,
                            commitMs:(marks.t3!=null&&marks.t2!=null)?marks.t3-marks.t2:null,
                            surfaceMs:diag.surfaceMs,
                            panelMs:diag.panelMs,
                            panelAfterSlideDomMs:(marks.panelEnd!=null&&marks.t5dom!=null)?marks.panelEnd-marks.t5dom:null,
                            firstUsefulUiMs:firstUsefulAbs-marks.t0,
                            firstSlidePaintMs:(marks.t5??marks.t5dom)-marks.t0,
                            firstThumbPaintMs:(marks.panelPaint??marks.t8??marks.t9)-marks.t0,
                            fullPanelDomMs:(marks.t9??marks.panelEnd)-marks.t0,
                            thumbCount:diag.thumbCount,
                            visibleThumbs:diag.visibleThumbs,
                            offscreenThumbs:Math.max(0,diag.thumbCount-diag.visibleThumbs),
                            isolatedPanelRenderMs:p1-p0,
                            maxTaskGapMs:tickGaps.length?Math.max(...tickGaps):0,
                            gapsOver50:tickGaps.filter(x=>x>50).length,
                            longTasks:postModelLong.length,
                            maxLongTaskMs:postModelLong.length?Math.max(...postModelLong.map(x=>x.duration)):0
                          };
                        }""",
                        {"fixture":fixtures[count],"count":count},
                    )
                    samples.append(sample)
                results[str(count)]=samples

            browser.close()
            if errors:
                raise AssertionError({"browser":BROWSER_NAME,"errors":errors})

        metrics=[
            "t1","t2","t3","t4","t5dom","t5","t6","t7","t8","t9","t10",
            "openResolved","decodeToCandidateMs","commitMs","surfaceMs","panelMs",
            "panelAfterSlideDomMs","firstUsefulUiMs","firstSlidePaintMs",
            "firstThumbPaintMs","fullPanelDomMs","thumbCount","visibleThumbs",
            "offscreenThumbs","isolatedPanelRenderMs","maxTaskGapMs","gapsOver50",
            "longTasks","maxLongTaskMs"
        ]
        summary={}
        for count,samples in results.items():
            summary[count]={m:stat(samples,m) for m in metrics}
        report={
            "browser":BROWSER_NAME,
            "baseline":"PR #209 / 25524f0a8135846a3fe78b2236dc93aac547a5e3",
            "counts":COUNTS,
            "iterations":ITERATIONS,
            "summary":summary,
            "samples":results,
            "definitions":{
                "T0":"app.open start",
                "T1":"File.arrayBuffer resolved",
                "T2":"replaceCandidate entered; decoded candidate available",
                "T3":"replaceCandidate returned",
                "T4":"SlideSurface.render entered",
                "T5dom":"SlideSurface.render completed DOM replacement",
                "T5":"first requestAnimationFrame after slide surface DOM replacement",
                "T6":"SlidePanelController.render entered",
                "T7":"first thumbnail can be attached; baseline uses one fragment so equals full attach",
                "T8":"first rAF after thumbnail fragment attach; visible thumbnails measurable",
                "T9":"full thumbnail fragment attached",
                "T10":"first zero-delay task scheduled immediately after session commit"
            },
            "notes":[
                "Instrumentation is test-only; product files are unchanged.",
                "The current panel builds every thumbnail off-DOM in one DocumentFragment and attaches the full fragment at once, so T7 and T9 are intentionally equal in this baseline.",
                "T5 is a paint opportunity, not a proof of GPU presentation; because panel rendering remains in the same JS task, its callback cannot run until synchronous panel work completes.",
                "isolatedPanelRenderMs measures a second full panel rebuild after open and is useful for scaling, not end-to-end latency."
            ]
        }
        (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps(summary,indent=2))
    finally:
        server.terminate()
        try: server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill()

if __name__=="__main__":
    main()

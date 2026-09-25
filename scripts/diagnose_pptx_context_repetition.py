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
PORT = int(os.environ.get("INKDOS_PPTX_DIAG_PORT", "8851"))
BASE = f"http://127.0.0.1:{PORT}"
BROWSER_NAME = os.environ.get("BROWSER", "webkit").strip().lower()
ITERATIONS = max(1, int(os.environ.get("INKDOS_PPTX_DIAG_ITERATIONS", "5")))
OUT = Path(os.environ.get("INKDOS_PPTX_DIAG_OUT", f"artifacts/pptx-context-diagnostic/{BROWSER_NAME}"))


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
    return statistics.median(values) if values else 0.0


def p95(values):
    values = sorted(float(v) for v in values if v is not None)
    if not values:
        return 0.0
    index = max(0, min(len(values) - 1, int(round(0.95 * (len(values) - 1)))))
    return values[index]


def main() -> None:
    if BROWSER_NAME not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={BROWSER_NAME}")

    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, BROWSER_NAME).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 820})
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"console.error: {msg.text}")
                if msg.type == "error"
                else None,
            )
            page.goto(BASE + "/apps/presentations/index.html?suite=1", wait_until="load")
            page.wait_for_function(
                "() => !!globalThis.InkDOS2Presentations?.PptxWriter && "
                "!!globalThis.InkDOS2Presentations?.PptxOpenController"
            )

            fixture = page.evaluate(
                """async () => {
                  const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
                  const src=new NS.PresentationSession();
                  src.resetNew();
                  const setTitle=(slide,text)=>{
                    const o=slide.objects[0];
                    o.text=text;
                    o.paragraphs=M.normalizeParagraphs(null,text,o);
                  };
                  setTitle(src.slides[0],'InkDOS diagnostic slide 1');
                  for(let i=2;i<=44;i++){
                    src.addSlide();
                    setTitle(src.currentSlide,'InkDOS diagnostic slide '+i);
                  }
                  src.setCurrentByIndex(0);
                  const bytes=await NS.PptxWriter.build(src);
                  let s='';
                  const chunk=0x8000;
                  for(let i=0;i<bytes.length;i+=chunk){
                    s+=String.fromCharCode(...bytes.subarray(i,i+chunk));
                  }
                  return {b64:btoa(s),size:bytes.length};
                }"""
            )

            samples = []
            for _ in range(ITERATIONS):
                sample = page.evaluate(
                    """async ({b64}) => {
                      const NS=globalThis.InkDOS2Presentations;
                      const raw=atob(b64);
                      const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
                      const realLoad=JSZip.loadAsync;
                      const RealDOMParser=DOMParser;
                      let loadSeq=0;
                      const loads=[],parts=[],parses=[];
                      const textPaths=new Map();
                      const loadStarts={};

                      function category(path){
                        if(path==='ppt/presentation.xml')return 'presentation_xml';
                        if(path==='ppt/_rels/presentation.xml.rels')return 'presentation_rels';
                        if(/^ppt\/slides\/slide\d+\.xml$/i.test(path))return 'slide_xml';
                        if(/^ppt\/slides\/_rels\/slide\d+\.xml\.rels$/i.test(path))return 'slide_rels';
                        if(/^ppt\/slideLayouts\/slideLayout\d+\.xml$/i.test(path))return 'layout_xml';
                        if(/^ppt\/slideLayouts\/_rels\/slideLayout\d+\.xml\.rels$/i.test(path))return 'layout_rels';
                        if(/^ppt\/slideMasters\/slideMaster\d+\.xml$/i.test(path))return 'master_xml';
                        if(/^ppt\/slideMasters\/_rels\/slideMaster\d+\.xml\.rels$/i.test(path))return 'master_rels';
                        if(/^ppt\/theme\/theme\d+\.xml$/i.test(path))return 'theme_xml';
                        return 'other';
                      }

                      JSZip.loadAsync=async function(input,options){
                        const id=++loadSeq;
                        const start=performance.now();
                        loadStarts[id]=start;
                        const zip=await realLoad.call(this,input,options);
                        const end=performance.now();
                        loads.push({id,start,end,duration:end-start,crc:!!options?.checkCRC32});
                        const realFile=zip.file.bind(zip);
                        zip.file=function(path){
                          const obj=realFile(path);
                          if(!obj||typeof path!=='string')return obj;
                          return new Proxy(obj,{
                            get(target,prop){
                              if(prop!=='async')return Reflect.get(target,prop,target);
                              return async function(type,...args){
                                const t0=performance.now();
                                const value=await target.async(type,...args);
                                const t1=performance.now();
                                const event={load:id,path,type,category:category(path),start:t0,end:t1,duration:t1-t0};
                                parts.push(event);
                                if(id===2&&type==='text')textPaths.set(value,path);
                                return value;
                              };
                            }
                          });
                        };
                        return zip;
                      };

                      globalThis.DOMParser=class TimedDOMParser{
                        parseFromString(text,type){
                          const path=textPaths.get(text)||'';
                          const t0=performance.now();
                          const value=new RealDOMParser().parseFromString(text,type);
                          const t1=performance.now();
                          parses.push({path,category:category(path),start:t0,end:t1,duration:t1-t0});
                          return value;
                        }
                      };

                      const start=performance.now();
                      let decoded;
                      try{
                        decoded=await NS.PptxOpenController.decodePptx(bytes,'context-diag-44.pptx');
                      }finally{
                        JSZip.loadAsync=realLoad;
                        globalThis.DOMParser=RealDOMParser;
                      }
                      const end=performance.now();

                      const decoderParts=parts.filter(x=>x.load===2&&x.type==='text');
                      const decoderParses=parses.filter(x=>x.path);
                      const immutable=new Set(['layout_xml','layout_rels','master_xml','master_rels','theme_xml']);

                      function grouped(events){
                        const out={};
                        for(const e of events){
                          const k=e.category;
                          const row=out[k]||(out[k]={calls:0,unique:new Set(),duration:0});
                          row.calls++;
                          row.unique.add(e.path);
                          row.duration+=e.duration;
                        }
                        return Object.fromEntries(Object.entries(out).map(([k,v])=>[
                          k,{calls:v.calls,unique:v.unique.size,durationMs:v.duration}
                        ]));
                      }

                      function repeatedLowerBound(events){
                        const byPath=new Map();
                        for(const e of events){
                          if(!immutable.has(e.category))continue;
                          const list=byPath.get(e.path)||[];
                          list.push(e);
                          byPath.set(e.path,list);
                        }
                        let repeated=0,total=0,necessary=0;
                        for(const list of byPath.values()){
                          list.sort((a,b)=>a.start-b.start);
                          total+=list.reduce((s,e)=>s+e.duration,0);
                          if(list.length){
                            necessary+=list[0].duration;
                            repeated+=list.slice(1).reduce((s,e)=>s+e.duration,0);
                          }
                        }
                        return {totalMs:total,necessaryFirstUseMs:necessary,repeatedMs:repeated};
                      }

                      const partRepeat=repeatedLowerBound(decoderParts);
                      const parseRepeat=repeatedLowerBound(decoderParses);
                      const decoderStart=loadStarts[2]??start;
                      const decoderMs=end-decoderStart;
                      const securityMs=Math.max(0,decoderStart-start);

                      const slideStarts=decoderParts
                        .filter(x=>x.category==='slide_xml')
                        .sort((a,b)=>a.start-b.start);
                      const slideWindows=[];
                      for(let i=0;i<slideStarts.length;i++){
                        const a=slideStarts[i].start;
                        const b=i+1<slideStarts.length?slideStarts[i+1].start:end;
                        slideWindows.push(b-a);
                      }

                      return {
                        slides:decoded?.slides?.length||0,
                        totalSecureDecodeMs:end-start,
                        securityBeforeDecoderMs:securityMs,
                        decoderMs,
                        zipLoads:loads,
                        partGroups:grouped(decoderParts),
                        parseGroups:grouped(decoderParses),
                        immutablePartRepeat:partRepeat,
                        immutableParseRepeat:parseRepeat,
                        repeatedImmutableLowerBoundMs:partRepeat.repeatedMs+parseRepeat.repeatedMs,
                        repeatedImmutableLowerBoundSharePct:decoderMs>0?(partRepeat.repeatedMs+parseRepeat.repeatedMs)/decoderMs*100:0,
                        slidePostXmlWindowTotalMs:slideWindows.reduce((a,b)=>a+b,0),
                        slidePostXmlWindowMedianMs:slideWindows.length?[...slideWindows].sort((a,b)=>a-b)[Math.floor(slideWindows.length/2)]:0
                      };
                    }""",
                    {"b64": fixture["b64"]},
                )
                samples.append(sample)

            browser.close()

            if errors:
                raise AssertionError({"browser": BROWSER_NAME, "errors": errors})

        keys = [
            "totalSecureDecodeMs",
            "securityBeforeDecoderMs",
            "decoderMs",
            "repeatedImmutableLowerBoundMs",
            "repeatedImmutableLowerBoundSharePct",
            "slidePostXmlWindowTotalMs",
            "slidePostXmlWindowMedianMs",
        ]
        summary = {
            key: {
                "median": median([s[key] for s in samples]),
                "p95": p95([s[key] for s in samples]),
            }
            for key in keys
        }
        summary["counts"] = {
            "partGroups": samples[0]["partGroups"],
            "parseGroups": samples[0]["parseGroups"],
            "slides": samples[0]["slides"],
            "fixtureBytes": fixture["size"],
        }
        report = {
            "browser": BROWSER_NAME,
            "iterations": ITERATIONS,
            "fixture": "presentations-pptx-44",
            "summary": summary,
            "samples": samples,
            "notes": [
                "Timing instrumentation is diagnostic overhead and is not the A/B product benchmark.",
                "Repeated immutable lower bound includes repeated ZIP text inflation/read plus DOMParser time for layout/master/theme and their rels.",
                "Relationship-map loop work, parseTheme, parseClrMap and placeholder-map CPU are not included in the lower-bound figure.",
                "The second JSZip load is the current decoder load; the first is the security gate."
            ],
        }
        (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"
RUNS = ["Anticonvulsi\u00advantes ", "e antipsicóticos ", "no transtorno bipolar"]


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None,
            )
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session")
            page.click("#startNew")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.active && "
                "!!globalThis.InkDOS2Presentations?.PptxWriter"
            )

            synthetic = page.evaluate(
                """async runs => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const slide=app.session.currentSlide;
                    const title=slide.objects.find(o=>o.type==='text');
                    const full=runs.join('');
                    slide.widthEmu=18288000;
                    slide.heightEmu=10287000;
                    title.x=1047750; title.y=3070225; title.w=16678275; title.h=2667000;
                    title.marginLeftEmu=25400; title.marginRightEmu=25400;
                    title.marginTopEmu=25400; title.marginBottomEmu=25400;
                    title.fontSizePt=112.5; title.bold=true; title.fontFamily='Arial';
                    title.text=full;
                    title.paragraphs=[{
                        align:'left',level:0,bullet:null,lineSpacing:0.92,lineSpacingPt:null,
                        spaceBeforePt:0,spaceAfterPt:0,
                        runs:runs.map(text=>({text,fontSizePt:112.5,bold:true,italic:false,underline:false,color:'#F3EEE4',fontFamily:'Arial'}))
                    }];
                    const base=await NS.PptxWriter.build(app.session);
                    const zip=await JSZip.loadAsync(base,{checkCRC32:true});
                    let xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    const doc=new DOMParser().parseFromString(xml,'application/xml');
                    const a='http://schemas.openxmlformats.org/drawingml/2006/main';
                    const xmlRuns=Array.from(doc.getElementsByTagNameNS(a,'r')).filter(r=>
                        Array.from(r.getElementsByTagNameNS(a,'t')).some(t=>runs.includes(t.textContent||''))
                    );
                    if(xmlRuns.length!==runs.length)throw new Error(`Expected ${runs.length} synthetic title runs, found ${xmlRuns.length}`);
                    for(const run of xmlRuns){
                        let rPr=Array.from(run.children).find(n=>n.localName==='rPr');
                        if(!rPr){rPr=doc.createElementNS(a,'a:rPr');run.insertBefore(rPr,run.firstChild);}
                        rPr.setAttribute('sz','11250');
                        rPr.setAttribute('b','1');
                        rPr.setAttribute('spc','-337');
                    }
                    const bodies=Array.from(doc.getElementsByTagNameNS(a,'bodyPr'));
                    if(bodies.length){
                        bodies[0].setAttribute('lIns','25400');bodies[0].setAttribute('rIns','25400');
                        bodies[0].setAttribute('tIns','25400');bodies[0].setAttribute('bIns','25400');
                        bodies[0].setAttribute('wrap','square');
                        if(!Array.from(bodies[0].children).some(n=>n.localName==='normAutofit')){
                            bodies[0].appendChild(doc.createElementNS(a,'a:normAutofit'));
                        }
                    }
                    zip.file('ppt/slides/slide1.xml',new XMLSerializer().serializeToString(doc),{createFolders:false});
                    return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}));
                }""",
                RUNS,
            )
            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'real-title-geometry.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                synthetic,
            )
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.sourceKind === 'pptx'")

            geometry = page.evaluate(
                """runs => {
                    const full=runs.join('');
                    const object=globalThis.__inkdosPresentations.session.currentSlide.objects.find(
                        o=>o.type==='text' && String(o.text||'')===full
                    );
                    if(!object)throw new Error('Synthetic real-title object missing after import');
                    const box=Array.from(document.querySelectorAll('.slide-textbox')).find(el=>
                        el.querySelector('.rich-text-content')?.innerText===full
                    );
                    if(!box)throw new Error('Synthetic real-title DOM box missing');
                    const content=box.querySelector('.rich-text-content');
                    const spans=Array.from(content.querySelectorAll('span'));
                    const rects=[];
                    for(const span of spans){
                        const node=span.firstChild;
                        if(!node)continue;
                        const range=document.createRange();
                        range.selectNodeContents(span);
                        for(const rect of range.getClientRects()){
                            if(rect.width>0&&rect.height>0)rects.push({left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom});
                        }
                    }
                    const tops=[];
                    for(const rect of rects){
                        if(!tops.some(top=>Math.abs(top-rect.top)<2))tops.push(rect.top);
                    }
                    tops.sort((a,b)=>a-b);
                    const boxRect=box.getBoundingClientRect();
                    const contentRect=content.getBoundingClientRect();
                    return {
                        runCount:object.paragraphs?.[0]?.runs?.length||0,
                        softHyphenPreserved:object.text.includes('\\u00ad'),
                        charSpacings:(object.paragraphs?.[0]?.runs||[]).map(r=>r.charSpacingPt??null),
                        lineSpacing:object.paragraphs?.[0]?.lineSpacing??null,
                        lineCount:tops.length,
                        box:{left:boxRect.left,right:boxRect.right,top:boxRect.top,bottom:boxRect.bottom},
                        content:{left:contentRect.left,right:contentRect.right,top:contentRect.top,bottom:contentRect.bottom},
                        glyph:{
                            left:Math.min(...rects.map(r=>r.left)),right:Math.max(...rects.map(r=>r.right)),
                            top:Math.min(...rects.map(r=>r.top)),bottom:Math.max(...rects.map(r=>r.bottom))
                        },
                        inlineTracking:spans.map(s=>s.style.letterSpacing),
                        text:object.text
                    };
                }""",
                RUNS,
            )
            assert geometry["runCount"] == 3, geometry
            assert geometry["softHyphenPreserved"] is True, geometry
            assert geometry["charSpacings"] == [-3.37, -3.37, -3.37], geometry
            assert abs(float(geometry["lineSpacing"]) - 0.92) < 0.001, geometry
            assert geometry["inlineTracking"] == ["-3.37px", "-3.37px", "-3.37px"], geometry
            assert geometry["lineCount"] == 2, geometry
            assert geometry["glyph"]["left"] >= geometry["box"]["left"] - 1, geometry
            assert geometry["glyph"]["right"] <= geometry["box"]["right"] + 1, geometry
            assert geometry["glyph"]["top"] >= geometry["box"]["top"] - 1, geometry
            assert geometry["glyph"]["bottom"] <= geometry["box"]["bottom"] + 1, geometry
            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPTX real-title multi-run geometry regression passed on {browser_name}: {geometry}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

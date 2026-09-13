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
PORT = 8802
BASE = f"http://127.0.0.1:{PORT}"
RUNS = ["Anticonvulsi\u00advantes ", "& ", "antipsicóticos"]


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
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session")
            page.click("#startNew")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.active && !!globalThis.InkDOS2Presentations?.PptxWriter")

            synthetic = page.evaluate(
                """async runs => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const slide=app.session.currentSlide;
                    const title=slide.objects.find(o=>o.type==='text');
                    const full=runs.join('');
                    slide.widthEmu=18288000; slide.heightEmu=10287000;
                    title.x=1047750; title.y=3070225; title.w=16678275; title.h=2667000;
                    title.marginLeftEmu=25400; title.marginRightEmu=25400;
                    title.marginTopEmu=25400; title.marginBottomEmu=25400;
                    title.fontSizePt=112.5; title.bold=true; title.fontFamily='Arial';
                    title.text=full;
                    title.paragraphs=[{align:'left',level:0,bullet:null,lineSpacing:1,lineSpacingPt:null,spaceBeforePt:0,spaceAfterPt:0,runs:[{text:full,fontSizePt:112.5,bold:true,italic:false,underline:false,color:'#F3EEE4',fontFamily:'Arial'}]}];
                    const zip=await JSZip.loadAsync(await NS.PptxWriter.build(app.session),{checkCRC32:true});
                    const path='ppt/slides/slide1.xml';
                    const doc=new DOMParser().parseFromString(await zip.file(path).async('text'),'application/xml');
                    const a='http://schemas.openxmlformats.org/drawingml/2006/main';
                    const target=Array.from(doc.getElementsByTagNameNS(a,'r')).find(r=>Array.from(r.getElementsByTagNameNS(a,'t')).some(t=>t.textContent===full));
                    if(!target)throw new Error('Synthetic source title run not found');
                    const p=target.parentNode;
                    let pPr=Array.from(p.children).find(n=>n.localName==='pPr');
                    if(!pPr){pPr=doc.createElementNS(a,'a:pPr');p.insertBefore(pPr,p.firstChild);}
                    for(const child of Array.from(pPr.children))if(child.localName==='lnSpc')child.remove();
                    const lnSpc=doc.createElementNS(a,'a:lnSpc');
                    const spcPct=doc.createElementNS(a,'a:spcPct');
                    spcPct.setAttribute('val','92000');
                    lnSpc.appendChild(spcPct);pPr.appendChild(lnSpc);
                    for(const text of runs){
                        const run=target.cloneNode(true);
                        let rPr=Array.from(run.children).find(n=>n.localName==='rPr');
                        if(!rPr){rPr=doc.createElementNS(a,'a:rPr');run.insertBefore(rPr,run.firstChild);}
                        rPr.setAttribute('sz','11250');rPr.setAttribute('b','1');rPr.setAttribute('spc','-337');
                        const textNode=Array.from(run.children).find(n=>n.localName==='t');
                        if(!textNode)throw new Error('Synthetic cloned text node missing');
                        textNode.textContent=text;
                        p.insertBefore(run,target);
                    }
                    p.removeChild(target);
                    const txBody=p.parentNode;
                    const bodyPr=Array.from(txBody.children).find(n=>n.localName==='bodyPr');
                    if(!bodyPr)throw new Error('Synthetic title body properties missing');
                    bodyPr.setAttribute('lIns','25400');bodyPr.setAttribute('rIns','25400');
                    bodyPr.setAttribute('tIns','25400');bodyPr.setAttribute('bIns','25400');bodyPr.setAttribute('wrap','square');
                    for(const child of Array.from(bodyPr.children))if(['spAutoFit','noAutofit','normAutofit'].includes(child.localName))child.remove();
                    bodyPr.appendChild(doc.createElementNS(a,'a:normAutofit'));
                    zip.file(path,new XMLSerializer().serializeToString(doc),{createFolders:false});
                    return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}));
                }""",
                RUNS,
            )
            page.evaluate(
                """async bytes => {await globalThis.__inkdosPresentations.open(new File([new Uint8Array(bytes)],'real-title-fidelity.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'}));}""",
                synthetic,
            )
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.sourceKind === 'pptx'")

            geometry = page.evaluate(
                """runs => {
                    const full=runs.join('');
                    const object=globalThis.__inkdosPresentations.session.currentSlide.objects.find(o=>o.type==='text'&&String(o.text||'')===full);
                    if(!object)throw new Error('Synthetic real-title object missing after import');
                    const box=Array.from(document.querySelectorAll('.slide-textbox')).find(el=>el.querySelector('.rich-text-content')?.innerText===full);
                    if(!box)throw new Error('Synthetic real-title DOM box missing');
                    const content=box.querySelector('.rich-text-content');
                    const spans=Array.from(content.querySelectorAll('span'));
                    const rects=[];
                    for(const span of spans){const range=document.createRange();range.selectNodeContents(span);for(const rect of range.getClientRects())if(rect.width>0&&rect.height>0)rects.push({left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom});}
                    if(!rects.length)throw new Error('Synthetic title produced no glyph rectangles');
                    const lineTops=[];for(const rect of rects)if(!lineTops.some(top=>Math.abs(top-rect.top)<2))lineTops.push(rect.top);lineTops.sort((a,b)=>a-b);
                    const boxRect=box.getBoundingClientRect();
                    return {runCount:object.paragraphs?.[0]?.runs?.length||0,renderedRuns:spans.map(s=>s.textContent),softHyphenPreserved:object.text.includes('\\u00ad'),charSpacings:(object.paragraphs?.[0]?.runs||[]).map(r=>r.charSpacingPt??null),lineSpacing:object.paragraphs?.[0]?.lineSpacing??null,autoFit:object.autoFit,autoFitScale:object.autoFitScale,lineCount:lineTops.length,lineTops,box:{left:boxRect.left,right:boxRect.right,top:boxRect.top,bottom:boxRect.bottom},glyph:{left:Math.min(...rects.map(r=>r.left)),right:Math.max(...rects.map(r=>r.right)),top:Math.min(...rects.map(r=>r.top)),bottom:Math.max(...rects.map(r=>r.bottom))},inlineTracking:spans.map(s=>s.style.letterSpacing)};
                }""",
                RUNS,
            )
            assert geometry["runCount"] == 3, geometry
            assert geometry["renderedRuns"] == RUNS, geometry
            assert geometry["softHyphenPreserved"] is True, geometry
            assert geometry["charSpacings"] == [-3.37, -3.37, -3.37], geometry
            assert abs(float(geometry["lineSpacing"]) - 0.92) < 0.001, geometry
            assert geometry["autoFit"] == "normal", geometry
            assert abs(float(geometry["autoFitScale"]) - 1.0) < 0.0001, geometry
            assert geometry["inlineTracking"] == ["-3.37px", "-3.37px", "-3.37px"], geometry
            assert geometry["lineCount"] == 2, geometry
            assert geometry["glyph"]["left"] >= geometry["box"]["left"] - 1, geometry
            assert geometry["glyph"]["right"] <= geometry["box"]["right"] + 1, geometry
            vertical_overhang = max(
                geometry["box"]["top"] - geometry["glyph"]["top"],
                geometry["glyph"]["bottom"] - geometry["box"]["bottom"],
                0,
            )
            assert vertical_overhang <= 12, geometry
            browser.close()
        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPTX real-title fidelity regression passed on {browser_name}: {geometry}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

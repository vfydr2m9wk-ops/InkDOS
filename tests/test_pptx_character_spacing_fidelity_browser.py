#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8797
BASE = f"http://127.0.0.1:{PORT}"
MARKER = "Tracking regression title"


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
            page = browser.new_page(viewport={"width": 1360, "height": 900})
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
                """async marker => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const slide=app.session.currentSlide;
                    const title=slide.objects.find(o=>o.type==='text');
                    slide.widthEmu=18288000;
                    slide.heightEmu=10287000;
                    title.x=1047750; title.y=3070225; title.w=16678275; title.h=2667000;
                    title.marginLeftEmu=25400; title.marginRightEmu=25400;
                    title.marginTopEmu=25400; title.marginBottomEmu=25400;
                    title.fontSizePt=112.5; title.bold=true; title.fontFamily='Arial';
                    title.text=marker;
                    title.paragraphs=[{
                        align:'left',level:0,bullet:null,lineSpacing:0.92,lineSpacingPt:null,
                        spaceBeforePt:0,spaceAfterPt:0,
                        runs:[{text:marker,fontSizePt:112.5,bold:true,italic:false,underline:false,color:'#F3EEE4',fontFamily:'Arial'}]
                    }];
                    const base=await NS.PptxWriter.build(app.session);
                    const zip=await JSZip.loadAsync(base,{checkCRC32:true});
                    let xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    const doc=new DOMParser().parseFromString(xml,'application/xml');
                    const runs=Array.from(doc.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','r'));
                    const target=runs.find(r=>Array.from(r.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','t')).some(t=>t.textContent===marker));
                    if(!target)throw new Error('Synthetic title run not found in generated PPTX');
                    let rPr=Array.from(target.children).find(n=>n.localName==='rPr');
                    if(!rPr){
                        rPr=doc.createElementNS('http://schemas.openxmlformats.org/drawingml/2006/main','a:rPr');
                        target.insertBefore(rPr,target.firstChild);
                    }
                    rPr.setAttribute('sz','11250');
                    rPr.setAttribute('b','1');
                    rPr.setAttribute('spc','-337');
                    xml=new XMLSerializer().serializeToString(doc);
                    zip.file('ppt/slides/slide1.xml',xml,{createFolders:false});
                    const out=await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                    return Array.from(out);
                }""",
                MARKER,
            )

            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'tracking-regression.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                synthetic,
            )
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.sourceKind === 'pptx'"
            )

            imported = page.evaluate(
                """marker => {
                    const slide=globalThis.__inkdosPresentations.session.currentSlide;
                    const object=slide.objects.find(o=>o.type==='text' && String(o.text||'').includes(marker));
                    const run=object?.paragraphs?.flatMap(p=>p.runs||[]).find(r=>r.text===marker)||null;
                    const span=Array.from(document.querySelectorAll('.slide-textbox .rich-text-content span')).find(el=>el.textContent===marker)||null;
                    return {
                        fontSizePt:run?.fontSizePt??null,
                        charSpacingPt:run?.charSpacingPt??null,
                        inlineLetterSpacing:span?.style?.letterSpacing||'',
                        computedLetterSpacing:span?getComputedStyle(span).letterSpacing:null
                    };
                }""",
                MARKER,
            )

            assert math.isclose(float(imported["fontSizePt"]), 112.5, abs_tol=0.001), imported
            assert math.isclose(float(imported["charSpacingPt"]), -3.37, abs_tol=0.001), imported
            # InkDOS maps one internal point to one CSS pixel for slide geometry and text.
            # Tracking must use the same coordinate mapping; CSS pt would introduce a 4/3 scale error.
            assert imported["inlineLetterSpacing"] == "-3.37px", imported
            assert imported["computedLetterSpacing"] == "-3.37px", imported

            preserved = page.evaluate(
                """async marker => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const object=app.session.currentSlide.objects.find(o=>o.type==='text' && String(o.text||'').includes(marker));
                    const run=object?.paragraphs?.flatMap(p=>p.runs||[]).find(r=>r.text===marker)||null;
                    if(!object||!run)throw new Error('Imported title run missing before preservation save');
                    const edited=marker+'!';
                    run.text=edited;
                    object.text=object.paragraphs.map(p=>(p.runs||[]).map(r=>r.text||'').join('')).join('\n');
                    const result=await NS.PptxPreservationWriter.build(app.session);
                    const zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    const doc=new DOMParser().parseFromString(xml,'application/xml');
                    const runs=Array.from(doc.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','r'));
                    const target=runs.find(r=>Array.from(r.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','t')).some(t=>t.textContent===edited));
                    const rPr=target?Array.from(target.children).find(n=>n.localName==='rPr'):null;
                    return {textFound:!!target,spc:rPr?.getAttribute('spc')??null};
                }""",
                MARKER,
            )
            assert preserved == {"textFound": True, "spc": "-337"}, preserved

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPTX character-spacing fidelity regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

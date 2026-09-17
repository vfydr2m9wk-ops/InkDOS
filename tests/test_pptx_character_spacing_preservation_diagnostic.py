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
PORT = 8798
BASE = f"http://127.0.0.1:{PORT}"
MARKER = "Tracking preservation diagnostic"


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
    phase = os.environ.get("PPTX_PRESERVE_DIAGNOSTIC", "spc").strip().lower()
    if phase not in {"model", "build", "text", "spc"}:
        raise RuntimeError(f"Unsupported PPTX_PRESERVE_DIAGNOSTIC={phase}")

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1360, "height": 900})
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session")
            page.click("#startNew")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.active && "
                "!!globalThis.InkDOS2Presentations?.PptxWriter && "
                "!!globalThis.InkDOS2Presentations?.PptxPreservationWriter"
            )

            synthetic = page.evaluate(
                """async marker => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const slide=app.session.currentSlide;
                    const title=slide.objects.find(o=>o.type==='text');
                    title.text=marker;
                    title.paragraphs=[{align:'left',level:0,bullet:null,lineSpacing:1,lineSpacingPt:null,spaceBeforePt:0,spaceAfterPt:0,runs:[{text:marker,fontSizePt:112.5,bold:true,italic:false,underline:false,color:'#F3EEE4',fontFamily:'Arial'}]}];
                    const base=await NS.PptxWriter.build(app.session);
                    const zip=await JSZip.loadAsync(base,{checkCRC32:true});
                    let xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    const doc=new DOMParser().parseFromString(xml,'application/xml');
                    const runs=Array.from(doc.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','r'));
                    const target=runs.find(r=>Array.from(r.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','t')).some(t=>t.textContent===marker));
                    if(!target)throw new Error('Synthetic title run not found');
                    const rPr=Array.from(target.children).find(n=>n.localName==='rPr');
                    if(!rPr)throw new Error('Synthetic title run properties not found');
                    rPr.setAttribute('sz','11250');
                    rPr.setAttribute('spc','-337');
                    zip.file('ppt/slides/slide1.xml',new XMLSerializer().serializeToString(doc),{createFolders:false});
                    return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}));
                }""",
                MARKER,
            )
            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'tracking-preserve.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                synthetic,
            )
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.sourceKind === 'pptx'")

            state = page.evaluate(
                """marker => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const object=app.session.currentSlide.objects.find(o=>o.type==='text' && String(o.text||'').includes(marker));
                    const run=object?.paragraphs?.flatMap(p=>p.runs||[]).find(r=>r.text===marker)||null;
                    if(!object||!run)throw new Error('Imported title run missing');
                    const before=object.sourceSignature;
                    const edited=marker+'!';
                    run.text=edited;
                    object.text=object.paragraphs.map(p=>(p.runs||[]).map(r=>r.text||'').join('')).join('\n');
                    return {charSpacingPt:run.charSpacingPt??null,sourceChanged:before!==NS.PresentationModel.textSignature(object),edited};
                }""",
                MARKER,
            )
            assert math.isclose(float(state["charSpacingPt"]), -3.37, abs_tol=0.001), state
            assert state["sourceChanged"] is True, state
            if phase == "model":
                print("PPTX tracking preservation model checkpoint passed.")
                browser.close()
                return

            built = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session);
                    globalThis.__trackingDiagnosticBytes=Array.from(result.bytes);
                    return {byteLength:result.bytes.length,modifiedObjects:result.receipt?.modifiedObjects||[]};
                }"""
            )
            assert int(built["byteLength"]) > 0, built
            assert any(x.get("kind") == "existing-text" for x in built["modifiedObjects"]), built
            if phase == "build":
                print("PPTX tracking preservation build checkpoint passed.")
                browser.close()
                return

            output = page.evaluate(
                """async edited => {
                    const zip=await JSZip.loadAsync(new Uint8Array(globalThis.__trackingDiagnosticBytes),{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    const doc=new DOMParser().parseFromString(xml,'application/xml');
                    const runs=Array.from(doc.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','r'));
                    const target=runs.find(r=>Array.from(r.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main','t')).some(t=>t.textContent===edited));
                    const rPr=target?Array.from(target.children).find(n=>n.localName==='rPr'):null;
                    return {textFound:!!target,spc:rPr?.getAttribute('spc')??null};
                }""",
                state["edited"],
            )
            assert output["textFound"] is True, output
            if phase == "text":
                print("PPTX tracking preservation text checkpoint passed.")
                browser.close()
                return

            assert output["spc"] == "-337", output
            print("PPTX tracking preservation spc checkpoint passed.")
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

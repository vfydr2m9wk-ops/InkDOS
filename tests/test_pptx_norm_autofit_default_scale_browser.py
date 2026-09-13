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
PORT = 8801
BASE = f"http://127.0.0.1:{PORT}"
MARKER = "Autofit default scale regression"


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
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1360, "height": 900})
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session")
            page.click("#startNew")
            page.wait_for_function("() => !!globalThis.InkDOS2Presentations?.PptxWriter")
            data = page.evaluate(
                """async marker => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const title=app.session.currentSlide.objects.find(o=>o.type==='text');
                    title.text=marker;
                    title.paragraphs=[{align:'left',level:0,bullet:null,lineSpacing:1,lineSpacingPt:null,spaceBeforePt:0,spaceAfterPt:0,runs:[{text:marker,fontSizePt:112.5,bold:true,italic:false,underline:false,color:'#000000',fontFamily:'Arial'}]}];
                    const zip=await JSZip.loadAsync(await NS.PptxWriter.build(app.session),{checkCRC32:true});
                    const path='ppt/slides/slide1.xml';
                    const doc=new DOMParser().parseFromString(await zip.file(path).async('text'),'application/xml');
                    const a='http://schemas.openxmlformats.org/drawingml/2006/main';
                    const run=Array.from(doc.getElementsByTagNameNS(a,'r')).find(r=>Array.from(r.getElementsByTagNameNS(a,'t')).some(t=>t.textContent===marker));
                    if(!run)throw new Error('marker run missing');
                    const rPr=Array.from(run.children).find(n=>n.localName==='rPr');
                    rPr.setAttribute('spc','-337');
                    const txBody=run.parentNode.parentNode;
                    const bodyPr=Array.from(txBody.children).find(n=>n.localName==='bodyPr');
                    for(const child of Array.from(bodyPr.children))if(['spAutoFit','noAutofit','normAutofit'].includes(child.localName))child.remove();
                    bodyPr.appendChild(doc.createElementNS(a,'a:normAutofit'));
                    zip.file(path,new XMLSerializer().serializeToString(doc),{createFolders:false});
                    return Array.from(await zip.generateAsync({type:'uint8array'}));
                }""",
                MARKER,
            )
            page.evaluate(
                """async bytes => {
                    await globalThis.__inkdosPresentations.open(new File([new Uint8Array(bytes)],'autofit-default.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'}));
                }""",
                data,
            )
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.sourceKind === 'pptx'")
            state = page.evaluate(
                """marker => {
                    const object=globalThis.__inkdosPresentations.session.currentSlide.objects.find(o=>o.type==='text'&&String(o.text||'')===marker);
                    const run=object?.paragraphs?.[0]?.runs?.[0];
                    const span=Array.from(document.querySelectorAll('.slide-textbox span')).find(s=>s.textContent===marker);
                    return {autoFit:object?.autoFit,autoFitScale:object?.autoFitScale,charSpacingPt:run?.charSpacingPt,letterSpacing:span?.style?.letterSpacing};
                }""",
                MARKER,
            )
            assert state["autoFit"] == "normal", state
            assert abs(float(state["autoFitScale"]) - 1.0) < 0.0001, state
            assert abs(float(state["charSpacingPt"]) - (-3.37)) < 0.0001, state
            assert state["letterSpacing"] == "-3.37px", state
            browser.close()
            print(f"PPTX normAutofit default-scale regression passed on {browser_name}: {state}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

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
PORT = 8803
BASE = f"http://127.0.0.1:{PORT}"
MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local preview test server did not start")


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
                lambda msg: errors.append(f"console.error: {msg.text}")
                if msg.type == "error" and "XML Parsing Error:" not in msg.text
                else None,
            )
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function(
                "() => !!globalThis.__inkdosPresentations?.session && "
                "!!globalThis.InkDOS2Presentations?.PptxWriter && "
                "!!globalThis.InkDOS2Presentations?.PptxOpenController"
            )

            result = page.evaluate(
                r"""async mime => {
                  const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
                  const app=globalThis.__inkdosPresentations;
                  const waitFor=async(fn,timeout=8000)=>{
                    const end=performance.now()+timeout;
                    while(performance.now()<end){
                      if(fn())return true;
                      await new Promise(r=>setTimeout(r,5));
                    }
                    throw new Error('preview test wait timed out');
                  };
                  const canvas=()=>document.getElementById('slideCanvas');
                  const hideError=()=>{const p=document.getElementById('openErrorPanel');if(p)p.hidden=true};
                  const observePreview=()=>{
                    let seen=document.body.dataset.presentationOpeningPreview==='true';
                    const mo=new MutationObserver(()=>{if(document.body.dataset.presentationOpeningPreview==='true')seen=true});
                    mo.observe(document.body,{attributes:true,attributeFilter:['data-presentation-opening-preview']});
                    return {seen:()=>seen,stop:()=>mo.disconnect()};
                  };
                  const setTitle=(slide,text)=>{
                    const o=slide.objects.find(x=>x.type==='text');
                    o.text=text;o.paragraphs=M.normalizeParagraphs(null,text,o);
                    o.color='#F4E04D';o.fontFamily='Aptos';
                    for(const p of o.paragraphs||[])for(const r of p.runs||[]){r.color='#F4E04D';r.fontFamily='Aptos'}
                  };
                  const makeDeck=async(count,prefix)=>{
                    const s=new NS.PresentationSession();s.resetNew();
                    s.currentSlide.background='#123456';
                    setTitle(s.currentSlide,prefix+' 1');
                    const shape=s.addShape('ellipse');shape.fill='#22AA88';shape.x=4200000;shape.y=3300000;
                    s.setCurrentByIndex(0);
                    const png='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLQGQAAAABJRU5ErkJggg==';
                    const image=s.addImage({src:png,mime:'image/png',widthEmu:700000,heightEmu:700000});
                    image.x=9500000;image.y=5000000;
                    for(let i=2;i<=count;i++){s.addSlide();setTitle(s.currentSlide,prefix+' '+i)}
                    s.setCurrentByIndex(0);
                    return NS.PptxWriter.build(s);
                  };
                  const fileOf=(bytes,name)=>new File([bytes],name,{type:mime});
                  const gateSecondDecoderSlide=()=>{
                    const real=JSZip.loadAsync;
                    let seq=0,release;
                    const gate=new Promise(r=>release=r);
                    JSZip.loadAsync=async function(input,options){
                      const zip=await real.call(this,input,options),id=++seq;
                      if(id===2){
                        const realFile=zip.file.bind(zip),wrapped=new WeakSet();
                        zip.file=function(name,...rest){
                          const obj=realFile(name,...rest);
                          if(name==='ppt/slides/slide2.xml'&&obj&&typeof obj.async==='function'&&!wrapped.has(obj)){
                            wrapped.add(obj);
                            const realAsync=obj.async.bind(obj);
                            obj.async=async function(...args){await gate;return realAsync(...args)};
                          }
                          return obj;
                        };
                      }
                      return zip;
                    };
                    return {
                      release:()=>release?.(),
                      restore:()=>{JSZip.loadAsync=real},
                      loads:()=>seq
                    };
                  };
                  const domSignature=()=>({
                    html:canvas().innerHTML,
                    background:canvas().style.background,
                    backgroundImage:canvas().style.backgroundImage,
                    width:canvas().style.width,
                    height:canvas().style.height,
                    text:canvas().innerText,
                    preview:canvas().dataset.transientPreview==='true'
                  });

                  // Establish a dirty, undoable old document. It must remain untouched
                  // while the new file is only a transient preview.
                  await app.newPresentation();
                  app.history.transact('Old document marker',()=>{
                    const o=app.session.currentSlide.objects[0];
                    o.text='OLD COMMITTED DOCUMENT';
                    o.paragraphs=M.normalizeParagraphs(null,o.text,o);
                  });
                  const oldSnapshot=JSON.stringify(app.session.snapshot());
                  const oldUndo=app.history.undoStack.length;
                  const oldRedo=app.history.redoStack.length;

                  const deck44=await makeDeck(44,'PREVIEW44');
                  const gate=gateSecondDecoderSlide();
                  const openPromise=app.open(fileOf(deck44,'preview-44.pptx'));
                  await waitFor(()=>document.body.dataset.presentationOpeningPreview==='true');
                  const mid={
                    snapshot:JSON.stringify(app.session.snapshot()),
                    undo:app.history.undoStack.length,
                    redo:app.history.redoStack.length,
                    dirty:app.session.dirty,
                    sourceKind:app.session.sourceKind,
                    slideCount:app.session.slides.length,
                    addResult:app.executeCommand('slide.add'),
                    saveResult:app.executeCommand('file.save'),
                    status:document.getElementById('statusText')?.textContent||'',
                    signature:domSignature(),
                    panelVisibility:document.getElementById('slidePanel')?.style.visibility||'',
                    ariaBusy:document.getElementById('workspace')?.getAttribute('aria-busy')
                  };
                  gate.restore();
                  gate.release();
                  const opened44=await openPromise;
                  await waitFor(()=>!app.openingPreview);
                  const final44={
                    snapshot:JSON.stringify(app.session.snapshot()),
                    signature:domSignature(),
                    sourceKind:app.session.sourceKind,
                    slideCount:app.session.slides.length,
                    firstText:app.session.slides[0].objects.filter(o=>o.type==='text').map(o=>o.text).join(' | '),
                    status:document.getElementById('statusText')?.textContent||''
                  };

                  // Decoder failure after slide 1: preview is allowed (security already
                  // passed), but it must disappear and the committed document must survive.
                  const errorBase=await makeDeck(3,'ERROR');
                  const errorZip=await JSZip.loadAsync(errorBase);
                  errorZip.file('ppt/slides/slide2.xml','<p:sld><broken>');
                  const errorBytes=await errorZip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                  const beforeError=JSON.stringify(app.session.snapshot());
                  const errorObserver=observePreview();
                  const errorOpened=await app.open(fileOf(errorBytes,'error-after-preview.pptx'));
                  errorObserver.stop();
                  const afterError={
                    previewSeen:errorObserver.seen(),
                    snapshot:JSON.stringify(app.session.snapshot()),
                    previewActive:!!app.openingPreview,
                    canvasPreview:canvas().dataset.transientPreview==='true'
                  };
                  hideError();

                  // Hostile XML is rejected by the security wrapper before the inner
                  // decoder can emit any preview.
                  const hostileBase=await makeDeck(2,'HOSTILE');
                  const hostileZip=await JSZip.loadAsync(hostileBase);
                  const slide1Path='ppt/slides/slide1.xml';
                  let hostileXml=await hostileZip.file(slide1Path).async('text');
                  hostileXml=hostileXml.replace(/^(<\?xml[^>]*\?>)?/,m=>m+'<!DOCTYPE p:sld [<!ENTITY x "boom">]>');
                  hostileZip.file(slide1Path,hostileXml);
                  const hostileBytes=await hostileZip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                  const beforeHostile=JSON.stringify(app.session.snapshot());
                  const hostileObserver=observePreview();
                  const hostileOpened=await app.open(fileOf(hostileBytes,'hostile-preview.pptx'));
                  hostileObserver.stop();
                  const afterHostile={
                    previewSeen:hostileObserver.seen(),
                    snapshot:JSON.stringify(app.session.snapshot()),
                    previewActive:!!app.openingPreview
                  };
                  hideError();

                  // A -> B: B supersedes the operation. A's preview must disappear,
                  // B commits, and A can never overwrite B after its delayed slide resumes.
                  const deckA=await makeDeck(100,'DECK-A');
                  const deckB=await makeDeck(3,'DECK-B');
                  const gateA=gateSecondDecoderSlide();
                  const promiseA=app.open(fileOf(deckA,'deck-a.pptx'));
                  await waitFor(()=>app.openingPreview&&canvas().innerText.includes('DECK-A 1'));
                  gateA.restore();
                  const promiseB=app.open(fileOf(deckB,'deck-b.pptx'));
                  const openedB=await promiseB;
                  await waitFor(()=>openedB&&app.session.slides[0].objects.some(o=>o.type==='text'&&o.text.includes('DECK-B 1')));
                  const afterBCommit={
                    previewActive:!!app.openingPreview,
                    sourceKind:app.session.sourceKind,
                    slideCount:app.session.slides.length,
                    firstText:app.session.slides[0].objects.filter(o=>o.type==='text').map(o=>o.text).join(' | ')
                  };
                  gateA.release();
                  const openedA=await promiseA;
                  const afterAStale={
                    previewActive:!!app.openingPreview,
                    slideCount:app.session.slides.length,
                    firstText:app.session.slides[0].objects.filter(o=>o.type==='text').map(o=>o.text).join(' | ')
                  };

                  // New during preview: authorization happens first, then preview is
                  // cancelled and resetNew increments operationId. Delayed A stays stale.
                  const deckNewCancel=await makeDeck(100,'CANCEL-A');
                  const gateNew=gateSecondDecoderSlide();
                  const stalePromise=app.open(fileOf(deckNewCancel,'cancel-a.pptx'));
                  await waitFor(()=>app.openingPreview&&canvas().innerText.includes('CANCEL-A 1'));
                  gateNew.restore();
                  const newAccepted=await app.newPresentation();
                  const newMid={
                    accepted:newAccepted,
                    previewActive:!!app.openingPreview,
                    sourceKind:app.session.sourceKind,
                    slideCount:app.session.slides.length
                  };
                  gateNew.release();
                  const staleOpened=await stalePromise;
                  const newFinal={
                    previewActive:!!app.openingPreview,
                    sourceKind:app.session.sourceKind,
                    slideCount:app.session.slides.length
                  };

                  // Normal committed result remains round-trippable.
                  const roundtrip=await NS.PptxWriter.build(app.session);
                  const reopened=await NS.PptxOpenController.decodePptx(roundtrip,'new-roundtrip.pptx');

                  return {
                    old:{snapshot:oldSnapshot,undo:oldUndo,redo:oldRedo},
                    success:{mid,opened44,final44},
                    error:{before:errorOpened?null:beforeError,opened:errorOpened,after:afterError},
                    hostile:{before:beforeHostile,opened:hostileOpened,after:afterHostile},
                    replacement:{openedA,openedB,afterBCommit,afterAStale},
                    cancelNew:{newAccepted,staleOpened,newMid,newFinal,reopenedSlides:reopened.slides.length}
                  };
                }""",
                MIME,
            )
            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})

        success = result["success"]
        mid = success["mid"]
        assert mid["snapshot"] == result["old"]["snapshot"], result
        assert mid["undo"] == result["old"]["undo"], result
        assert mid["redo"] == result["old"]["redo"], result
        assert mid["dirty"] is True, result
        assert mid["addResult"] is False, result
        assert mid["saveResult"] is False, result
        assert "Opening presentation" in mid["status"], result
        assert mid["signature"]["preview"] is True, result
        assert "PREVIEW44 1" in mid["signature"]["text"], result
        assert mid["panelVisibility"] == "hidden", result
        assert mid["ariaBusy"] == "true", result
        assert success["opened44"] is True, result
        assert success["final44"]["slideCount"] == 44, result
        assert success["final44"]["sourceKind"] == "pptx", result
        assert "PREVIEW44 1" in success["final44"]["firstText"], result
        assert success["final44"]["signature"]["preview"] is False, result
        # The exact same renderer is used for preview and committed slide.
        assert mid["signature"]["html"] == success["final44"]["signature"]["html"], result
        assert mid["signature"]["background"] == success["final44"]["signature"]["background"], result
        assert mid["signature"]["backgroundImage"] == success["final44"]["signature"]["backgroundImage"], result
        assert mid["signature"]["width"] == success["final44"]["signature"]["width"], result
        assert mid["signature"]["height"] == success["final44"]["signature"]["height"], result

        error = result["error"]
        assert error["opened"] is False, result
        assert error["after"]["previewSeen"] is True, result
        assert error["after"]["snapshot"] == error["before"], result
        assert error["after"]["previewActive"] is False, result
        assert error["after"]["canvasPreview"] is False, result

        hostile = result["hostile"]
        assert hostile["opened"] is False, result
        assert hostile["after"]["previewSeen"] is False, result
        assert hostile["after"]["snapshot"] == hostile["before"], result
        assert hostile["after"]["previewActive"] is False, result

        replacement = result["replacement"]
        assert replacement["openedB"] is True, result
        assert replacement["openedA"] is False, result
        assert replacement["afterBCommit"]["slideCount"] == 3, result
        assert "DECK-B 1" in replacement["afterBCommit"]["firstText"], result
        assert "DECK-B 1" in replacement["afterAStale"]["firstText"], result
        assert replacement["afterAStale"]["slideCount"] == 3, result
        assert replacement["afterAStale"]["previewActive"] is False, result

        cancel = result["cancelNew"]
        assert cancel["newAccepted"] is True, result
        assert cancel["staleOpened"] is False, result
        assert cancel["newMid"]["sourceKind"] == "new", result
        assert cancel["newMid"]["slideCount"] == 1, result
        assert cancel["newMid"]["previewActive"] is False, result
        assert cancel["newFinal"]["sourceKind"] == "new" and cancel["newFinal"]["slideCount"] == 1, result
        assert cancel["newFinal"]["previewActive"] is False, result
        assert cancel["reopenedSlides"] == 1, result

        print(
            f"PPTX early-preview regression passed on {browser_name}: "
            "transient slide is faithful, transactional, security-gated and stale-safe."
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()

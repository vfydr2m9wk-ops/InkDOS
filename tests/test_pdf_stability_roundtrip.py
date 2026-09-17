#!/usr/bin/env python3
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=8780;BASE=f"http://127.0.0.1:{PORT}"
def wait_port(port,timeout=10.0):
    deadline=time.time()+timeout
    while time.time()<deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1",port))==0:return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")
def force_download_delivery(page):
    page.evaluate(r"""() => {for(const[target,key]of[[window,'showSaveFilePicker'],[navigator,'share'],[navigator,'canShare']]){try{Object.defineProperty(target,key,{value:undefined,configurable:true})}catch(_){}}window.confirm=()=>true;}""")
def save_download(page,target):
    with page.expect_download(timeout=30000) as info:page.click("#saveToolbarBtn")
    download=info.value;download.save_as(str(target));return download.suggested_filename
def main():
    browser_name=os.environ.get("BROWSER","chromium").strip().lower()
    if browser_name not in {"chromium","firefox","webkit"}:raise RuntimeError(f"Unsupported BROWSER={browser_name}")
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);errors=[]
    try:
        wait_port(PORT)
        with tempfile.TemporaryDirectory() as td,sync_playwright() as pw:
            browser=getattr(pw,browser_name).launch(headless=True);page=browser.new_page(viewport={"width":1280,"height":900})
            page.on("pageerror",lambda exc:errors.append(f"pageerror: {exc}"));page.on("console",lambda msg:errors.append(f"console.error: {msg.text}") if msg.type=="error" else None)
            page.goto(BASE+"/apps/pdf/",wait_until="load");page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug");force_download_delivery(page)
            opened=page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create();for(let i=1;i<=3;i++){const p=pdf.addPage([612,792]);p.drawText(`Roundtrip structural page ${i}`,{x:48,y:730,size:20})}const bytes=new Uint8Array(await pdf.save());return await d.fileOpen.openFile(new File([bytes],'roundtrip-structural.pdf',{type:'application/pdf'}));}""");assert opened is True
            page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 3");page.evaluate("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.goToPage(2)");page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.currentPage === 2")
            deleted=page.evaluate("async()=>await globalThis.InkDOS2PdfP4.PdfStabilityDebug.registry.execute('pdf.pages.delete')");assert deleted is not False;page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount === 2",timeout=15000)
            structural_path=Path(td)/"roundtrip-structural-saved.pdf";suggested=save_download(page,structural_path);assert suggested.endswith("-edited.pdf");assert structural_path.stat().st_size>100
            page.locator("#fileInput").set_input_files(str(structural_path));page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.fileName === 'roundtrip-structural-saved.pdf'",timeout=15000)
            structural=page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,doc=d.fileOpen.pdfDocument,out=[];for(let n=1;n<=doc.numPages;n++){const p=await doc.getPage(n),tc=await p.getTextContent();out.push((tc.items||[]).map(x=>x.str||'').join(' '))}return{pages:doc.numPages,text:out,dirty:d.session.dirty};}""");assert structural["pages"]==2;assert "Roundtrip structural page 1" in structural["text"][0];assert "Roundtrip structural page 3" in structural["text"][1];assert structural["dirty"] is False
            opened=page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create(),p=pdf.addPage([612,792]);p.drawText('Roundtrip comment page',{x:48,y:730,size:20});const bytes=new Uint8Array(await pdf.save());return await d.fileOpen.openFile(new File([bytes],'roundtrip-comment.pdf',{type:'application/pdf'}));}""");assert opened is True
            page.click('[data-pdf-mode="annotate"]');page.wait_for_function("() => document.documentElement.dataset.pdfMode === 'annotate'");page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug;d.extensions.pending={pageNumber:1,rects:[{x:.25,y:.25,w:.002,h:.002}],text:''};await d.registry.execute('pdf.comment.open')}""");page.locator("#commentText").fill("Round-trip persisted comment");page.locator('#commentDialog button[type="submit"]').click();page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.extensions.inspect().count === 1")
            comment_path=Path(td)/"roundtrip-comment-saved.pdf";save_download(page,comment_path);assert comment_path.stat().st_size>100;page.locator("#fileInput").set_input_files(str(comment_path));page.wait_for_function("() => globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.fileName === 'roundtrip-comment-saved.pdf'",timeout=15000)
            annotations=page.evaluate(r"""async()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,p=await d.fileOpen.pdfDocument.getPage(1),items=await p.getAnnotations({intent:'display'});return items.map(a=>({subtype:a.subtype||'',contents:a.contents||a.contentsObj?.str||'',title:a.title||a.titleObj?.str||'',annotationType:a.annotationType??null}))}""");assert any("Round-trip persisted comment" in (a["contents"] or "") for a in annotations),annotations
            if errors:raise AssertionError({"browser":browser_name,"errors":errors});browser.close()
        print(f"PDF save/reopen round-trip regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()
if __name__=="__main__":main()

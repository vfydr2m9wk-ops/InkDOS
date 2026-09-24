#!/usr/bin/env python3
from __future__ import annotations
import json, os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8773
BASE=f"http://127.0.0.1:{PORT}"

def wait_port():
    end=time.time()+10
    while time.time()<end:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1",PORT))==0:return
        time.sleep(.1)
    raise RuntimeError("server did not start")

def move_probe(page):
    page.click("#startNew")
    page.wait_for_function("()=>globalThis.__inkdosPresentations?.session?.active")
    page.click("#addSlideBtn");page.click("#addSlideBtn")
    page.wait_for_function("()=>globalThis.__inkdosPresentations.session.slides.length===3")
    page.evaluate("()=>globalThis.__inkdosPresentations.executeCommand('navigation.to',1)")
    page.wait_for_function("()=>globalThis.__inkdosPresentations.session.currentIndex===1")
    return page.evaluate("""()=>['moveSlideUpBtn','moveSlideDownBtn','deleteSlideBtn','addSlideBtn'].map(id=>{
      const el=document.getElementById(id),s=getComputedStyle(el),r=el.getBoundingClientRect(),p=el.parentElement,ps=p?getComputedStyle(p):null,pr=p?p.getBoundingClientRect():null;
      return {id,disabled:el.disabled,hidden:el.hidden,display:s.display,visibility:s.visibility,opacity:s.opacity,
        rect:{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom},
        offsetParent:el.offsetParent?.id||el.offsetParent?.className||null,
        parent:{id:p?.id||null,className:p?.className||null,display:ps?.display||null,visibility:ps?.visibility||null,overflowX:ps?.overflowX||null,rect:pr?{x:pr.x,y:pr.y,width:pr.width,height:pr.height}:null},
        inEditbar:!!el.closest('#editbar'),inRail:!!el.closest('.inkdos-toolbar-rail'),
        ariaHidden:el.getAttribute('aria-hidden'),
      };
    })""")

def make_table(page):
    fixture=page.evaluate("""async()=>{const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;base=await NS.PptxWriter.build(app.session),zip=await JSZip.loadAsync(base,{checkCRC32:true});let slide=await zip.file('ppt/slides/slide1.xml').async('text');const cell=t=>'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1600"/><a:t>'+t+'</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr/></a:tc>';const table='<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="90" name="Table 1"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="7315200" cy="2743200"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"><a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId></a:tblPr><a:tblGrid><a:gridCol w="3657600"/><a:gridCol w="3657600"/></a:tblGrid><a:tr h="1371600">'+cell('A')+cell('B')+'</a:tr><a:tr h="1371600">'+cell('C')+cell('D')+'</a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>';slide=slide.replace('</p:spTree>',table+'</p:spTree>');zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE'}))}""")
    page.evaluate("""async bytes=>{const f=new File([new Uint8Array(bytes)],'diag.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});await globalThis.__inkdosPresentations.open(f)}""",fixture)
    page.wait_for_selector(".slide-table")
    page.locator('[data-table-row="0"][data-table-col="0"] .table-cell-content').dispatch_event("pointerdown")
    page.wait_for_function("()=>!document.getElementById('pptP2TableToolsBtn').disabled")
    page.click("#pptP2TableToolsBtn")
    page.wait_for_selector("#pptP2TableToolsPanel",state="visible")

def merge_probe(page):
    page.click("#startNew");page.wait_for_function("()=>globalThis.__inkdosPresentations?.session?.active")
    make_table(page)
    page.locator("#pptP2MergeRow").fill("1")
    page.locator("#pptP2MergeCol").fill("2")
    before=page.evaluate("""()=>({row:document.getElementById('pptP2MergeRow').value,col:document.getElementById('pptP2MergeCol').value,active:InkDOS2Presentations.PptP2TableToolsUi.activeCell,disabled:document.getElementById('pptP2Merge').disabled})""")
    page.locator("#pptP2Merge").hover()
    after_hover=page.evaluate("""()=>({row:document.getElementById('pptP2MergeRow').value,col:document.getElementById('pptP2MergeCol').value,active:InkDOS2Presentations.PptP2TableToolsUi.activeCell})""")
    page.click("#pptP2Merge")
    page.wait_for_timeout(400)
    after=page.evaluate("""()=>{const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table'),c=t.rows[0].cells[0];return {row:document.getElementById('pptP2MergeRow').value,col:document.getElementById('pptP2MergeCol').value,active:InkDOS2Presentations.PptP2TableToolsUi.activeCell,leader:{colSpan:c.colSpan,rowSpan:c.rowSpan,hMerge:c.hMerge,vMerge:c.vMerge,text:c.text},splitDisabled:document.getElementById('pptP2Split').disabled,mergeDisabled:document.getElementById('pptP2Merge').disabled};}""")
    return {"before":before,"afterHover":after_hover,"afterClick":after}

def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
      wait_port()
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        p=browser.new_page(viewport={"width":1360,"height":900})
        p.goto(BASE+"/apps/presentations/",wait_until="load")
        p.wait_for_function("()=>!!globalThis.__inkdosPresentations?.p2Tools")
        moves=move_probe(p)
        p.close()
        p=browser.new_page(viewport={"width":1360,"height":900})
        p.goto(BASE+"/apps/presentations/",wait_until="load")
        p.wait_for_function("()=>!!globalThis.__inkdosPresentations?.p2Tools")
        merge=merge_probe(p)
        p.close();browser.close()
      out={"moves":moves,"merge":merge}
      Path("artifacts").mkdir(exist_ok=True)
      Path("artifacts/presentations-button-diagnostic.json").write_text(json.dumps(out,indent=2)+"\n")
      print(json.dumps(out,indent=2))
    finally:
      srv.terminate()
      try:srv.wait(timeout=3)
      except subprocess.TimeoutExpired:srv.kill()

if __name__=="__main__":main()

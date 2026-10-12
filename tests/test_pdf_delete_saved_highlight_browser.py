#!/usr/bin/env python3
"""Regression (PDF workspace, edit mode): one trash button deletes highlights, including those saved in the file.

- the toolbar has a single trash button (it was doubled by a separate "Delete mode" button);
- a highlight over several lines is stored as one rect per line (repeated client rects painted a darker band);
- the text PDF.js puts in a saved highlight for screen readers (<mark class="overlaidText">) stays invisible;
- selecting the text of a highlight saved in the file and pressing the trash removes it from the page at once and from
  the saved file; undo brings it back, redo deletes it again."""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8837
BASE = f"http://127.0.0.1:{PORT}"
BROWSER = os.environ.get("BROWSER", "chromium").strip().lower()
LINES = ["Sleep is crucial for emotional, cognitive, and physical well-being. Most psychiatric",
         "conditions are associated with sleep disorders; additionally, sleep disturbances",
         "are risk factors for the development of mood, anxiety, and substance use disorders",
         "and suicidal behaviors. Insufficient or disrupted sleep in children and"]


def yellow(p, clip):
    """Share of clearly yellow pixels in the clip."""
    px = list(Image.open(io.BytesIO(p.screenshot(clip=clip))).convert("RGB").getdata())
    return sum(1 for r, g, b in px if r > 230 and g > 190 and b < 200) / len(px)


def main() -> None:
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        with sync_playwright() as pw, tempfile.TemporaryDirectory() as td:
            b=getattr(pw,BROWSER).launch(headless=True);p=b.new_page(viewport={'width':1280,'height':900},accept_downloads=True)
            errs=[];p.on('pageerror',lambda e:errs.append(str(e)));p.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
            p.goto(BASE+'/apps/pdf/',wait_until='load');p.wait_for_function("()=>!!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            p.add_script_tag(url=BASE+'/apps/pdf/vendor/pdf-lib/pdf-lib.min.js');p.wait_for_function("()=>!!globalThis.PDFLib")
            p.evaluate(r"""()=>{for(const[t,k]of[[window,'showSaveFilePicker'],[navigator,'share'],[navigator,'canShare']]){try{Object.defineProperty(t,k,{value:undefined,configurable:true})}catch(_){}}window.confirm=()=>true;new MutationObserver(()=>document.querySelector('#pdfConfirmDialog [data-choice="confirm"]')?.click()).observe(document.body,{childList:true});}""")
            p.evaluate("""async(lines)=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create(),f=await pdf.embedFont(PDFLib.StandardFonts.TimesRoman),pg=pdf.addPage([612,792]);
              lines.forEach((t,i)=>pg.drawText(t,{x:60,y:700-i*22,size:15,font:f}));return d.fileOpen.openFile(new File([await pdf.save()],'s.pdf',{type:'application/pdf'}))}""",LINES)
            p.wait_for_function("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount===1")
            p.click('#editModeBtn');p.wait_for_function("()=>document.documentElement.dataset.pdfMode==='annotate'");p.wait_for_timeout(800)
            toolbar=lambda:p.evaluate("()=>[...document.querySelectorAll('#pdfAnnotationTools button, .pdf-annotation-tools button')].filter(b=>!b.hidden&&b.offsetParent).map(b=>b.id+(b.disabled?'(off)':''))")
            tools=toolbar()
            assert tools.count('deleteAnnotationBtn')==1 and not any(t.startswith('persistentDeleteBtn') for t in tools), tools  # one trash button
            p.evaluate("""async()=>{const sp=document.querySelectorAll('.pdf-select-text-layer span'),r=document.createRange(),a=sp[1].firstChild,b=sp[3].firstChild;r.setStart(a,Math.floor(a.length*0.75));r.setEnd(b,Math.floor(b.length/3));const sel=getSelection();sel.removeAllRanges();sel.addRange(r);return await globalThis.InkDOS2PdfP4.PdfStabilityDebug.extensions.addMark('highlight')}""")
            rects=p.evaluate("()=>[...globalThis.InkDOS2PdfP4.PdfStabilityDebug.extensions.items.values()][0].rects.length")
            assert rects==3, ('one rect per highlighted line', rects)
            saved=Path(td)/'saved.pdf'
            with p.expect_download(timeout=30000) as info: p.click('#saveToolbarBtn')
            info.value.save_as(str(saved));p.locator('#fileInput').set_input_files(str(saved))
            p.wait_for_function("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.fileName==='saved.pdf'",timeout=15000);p.wait_for_timeout(1000)
            p.click('#editModeBtn');p.wait_for_function("()=>document.documentElement.dataset.pdfMode==='annotate'");p.wait_for_timeout(1200)
            spans=p.evaluate("()=>[...document.querySelectorAll('.pdf-select-text-layer span')].map(s=>{const r=s.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]})")
            clip={'x':spans[0][0]-10,'y':spans[0][1]-10,'width':spans[0][2]-spans[0][0]+60,'height':spans[3][3]-spans[0][1]+20}
            marks=p.evaluate("()=>[...document.querySelectorAll('.annotationLayer .overlaidText')].map(m=>getComputedStyle(m).opacity)")
            assert marks and set(marks)=={'0'}, ('the text of a saved highlight must not show over the page', marks)
            assert yellow(p,clip)>0.1, 'saved highlight not shown'
            # select highlighted text on line 3, then the trash button
            p.evaluate("()=>{const s=document.querySelectorAll('.pdf-select-text-layer span')[2],r=document.createRange();r.selectNodeContents(s);const sel=getSelection();sel.removeAllRanges();sel.addRange(r)}")
            assert p.evaluate("()=>!document.getElementById('deleteAnnotationBtn').disabled"), 'trash disabled'
            p.click('#deleteAnnotationBtn');p.wait_for_timeout(1500)
            assert yellow(p,clip)<0.01, 'deleted saved highlight still painted'
            p.click('#undoBtn');p.wait_for_timeout(1500);assert yellow(p,clip)>0.1, 'undo did not bring the highlight back'
            p.click('#redoBtn');p.wait_for_timeout(1500);assert yellow(p,clip)<0.01, 'redo did not delete again'
            saved2=Path(td)/'saved2.pdf'
            with p.expect_download(timeout=30000) as info: p.click('#saveToolbarBtn')
            info.value.save_as(str(saved2));p.locator('#fileInput').set_input_files(str(saved2))
            p.wait_for_function("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.fileName==='saved2.pdf'",timeout=15000);p.wait_for_timeout(1200)
            left=p.evaluate("async()=>{const pg=await globalThis.InkDOS2PdfP4.PdfStabilityDebug.fileOpen.pdfDocument.getPage(1);return (await pg.getAnnotations()).map(a=>a.subtype)}")
            assert left==[], ('the deleted highlight is still in the saved file', left)
            assert yellow(p,clip)<0.01
            assert not errs, errs
            b.close()
    finally:
        srv.terminate()
    print(f"PDF single trash deletes saved highlights ({BROWSER}): OK")


if __name__ == "__main__":
    main()

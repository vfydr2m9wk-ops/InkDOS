#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE=os.environ.get("INKDOS_ONLINE_BASE","http://127.0.0.1:8766/").rstrip("/")+"/"
APP=os.environ.get("INKDOS_BUTTON_TARGET_APP","").strip().lower()
OUT=Path(os.environ.get("INKDOS_BUTTON_TARGET_OUT",f"artifacts/button-target-{APP or 'all'}"))
OUT.mkdir(parents=True,exist_ok=True)
APPS=("documents","spreadsheets","presentations","pdf","txt","epub")
if APP and APP not in APPS: raise RuntimeError(f"Unknown app {APP}")

def build_epub(path:Path):
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("mimetype","application/epub+zip",compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",'<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf",'<?xml version="1.0" encoding="UTF-8"?><package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">button-audit</dc:identifier><dc:title>Button Audit</dc:title><dc:language>en</dc:language></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/><item id="c2" href="ch2.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/><itemref idref="c2"/></spine></package>')
        z.writestr("OEBPS/nav.xhtml",'<!doctype html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body><nav epub:type="toc"><ol><li><a href="ch1.xhtml#one">Chapter One</a></li><li><a href="ch2.xhtml#two">Chapter Two</a></li></ol></nav></body></html>')
        z.writestr("OEBPS/ch1.xhtml",'<!doctype html><html xmlns="http://www.w3.org/1999/xhtml"><body><h1 id="one">Chapter One</h1><p>Alpha beta gamma button audit text.</p></body></html>')
        z.writestr("OEBPS/ch2.xhtml",'<!doctype html><html xmlns="http://www.w3.org/1999/xhtml"><body><h1 id="two">Chapter Two</h1><p>Delta epsilon zeta button audit text.</p></body></html>')

class Audit:
    def __init__(self,browser,app,epub_path):
        self.browser=browser; self.app=app; self.epub_path=epub_path
        self.checks=[]; self.hidden=[]

    def context(self,width=1360,height=900):
        c=self.browser.new_context(viewport={"width":width,"height":height},service_workers="block",accept_downloads=True)
        c.add_init_script("""(()=>{try{localStorage.setItem('inkdos2:appearance','light');localStorage.setItem('inkdos2:ui-density','desktop')}catch(_){}})();""")
        return c

    def page(self,width=1360,height=900):
        c=self.context(width,height); p=c.new_page(); errors=[]
        p.on("pageerror",lambda exc: errors.append("pageerror: "+str(exc)))
        p.on("console",lambda msg: errors.append("console-error: "+msg.text) if msg.type=="error" else None)
        p.goto(urljoin(BASE,f"apps/{self.app}/index.html"),wait_until="load",timeout=30000)
        p.wait_for_timeout(180)
        return c,p,errors

    def record(self,label,status="clicked",selector=None,effect=None,error=None):
        self.checks.append({"label":label,"selector":selector,"status":status,"effect":effect,"error":error})

    def click(self,p,errors,selector,label,timeout=4000):
        try:
            loc=p.locator(selector).first
            loc.wait_for(state="visible",timeout=timeout)
            if not loc.is_enabled():
                self.record(label,"disabled",selector); return False
            before=len(errors); loc.click(timeout=timeout,no_wait_after=True); p.wait_for_timeout(150)
            new=errors[before:]
            if new:
                self.record(label,"clicked-with-error",selector,error=" | ".join(new)); return False
            self.record(label,"clicked",selector); return True
        except Exception as exc:
            self.record(label,"click-exception",selector,error=repr(exc)); return False

    def hidden_redundant(self,p):
        rows=p.evaluate("""()=>[...document.querySelectorAll('[data-inkdos-settings-redundant] button')].map(b=>({id:b.id||null,text:(b.textContent||'').trim().replace(/\\s+/g,' '),visible:!!(b.offsetWidth||b.offsetHeight||b.getClientRects().length)}))""")
        for row in rows:
            self.hidden.append({**row,"reason":"settings-strip replacement: data-inkdos-settings-redundant"})

    def help_close(self):
        c,p,e=self.page()
        try:
            self.hidden_redundant(p)
            p.locator("#menuBtn").click()
            entry=p.locator('[data-inkdos-help-entry]')
            entry.wait_for(state="visible")
            entry.click()
            p.locator('[data-inkdos-help-dialog]').wait_for(state="visible")
            self.click(p,e,'[data-inkdos-help-close]',"Close Help")
        finally:c.close()

    def documents(self):
        self.help_close()
        c,p,e=self.page()
        try:
            p.wait_for_function("()=>!!globalThis.InkDOS2Documents?.DocumentsApp")
            p.evaluate("async()=>globalThis.InkDOS2Documents.DocumentsApp.newDocument()")
            p.locator("#contextBtn").click(); p.wait_for_timeout(300)
            pages=p.get_by_role("button",name="Pages",exact=True)
            if pages.count() and pages.first.is_visible(): pages.first.click()
            p.wait_for_selector(".page-thumb",state="visible")
            p.wait_for_timeout(900)
            ok=False; last=None
            for _ in range(3):
                try:
                    p.locator(".page-thumb").first.click(timeout=4000,no_wait_after=True)
                    p.wait_for_timeout(120); ok=True; break
                except PlaywrightTimeoutError as exc:
                    last=exc; p.wait_for_timeout(250)
            if ok:self.record("Page 1","clicked",".page-thumb:first")
            else:self.record("Page 1","click-exception",".page-thumb:first",error=repr(last))
        finally:c.close()

    def spreadsheets(self):
        self.help_close()
        c,p,e=self.page()
        try:
            p.wait_for_function("()=>!!globalThis.__inkdosSpreadsheetsS1")
            p.evaluate("""async()=>{const a=globalThis.__inkdosSpreadsheetsS1;await a.openController.newWorkbook();a.editor.editor.commitValue('dirty',0,0);globalThis.__buttonAuditPending=a.openController.newWorkbook()}""")
            p.locator("#sessionReplacePanel").wait_for(state="visible")
            self.click(p,e,"#sessionReplaceDiscard","sessionReplaceDiscard")
            result=p.evaluate("async()=>await globalThis.__buttonAuditPending")
            self.checks[-1]["effect"]={"replacementResult":result}
        finally:c.close()

    def presentation_base(self,p):
        p.wait_for_function("()=>!!globalThis.__inkdosPresentations?.p2Tools")
        p.locator("#startNew").click()
        p.wait_for_function("()=>globalThis.__inkdosPresentations.session.active")

    def presentation_table(self,p):
        self.presentation_base(p)
        fixture=p.evaluate("""async()=>{const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;base=await NS.PptxWriter.build(app.session),zip=await JSZip.loadAsync(base,{checkCRC32:true});let slide=await zip.file('ppt/slides/slide1.xml').async('text');const cell=t=>'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1600"/><a:t>'+t+'</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr/></a:tc>';const table='<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="90" name="Table 1"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="7315200" cy="2743200"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"><a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId></a:tblPr><a:tblGrid><a:gridCol w="3657600"/><a:gridCol w="3657600"/></a:tblGrid><a:tr h="1371600">'+cell('A')+cell('B')+'</a:tr><a:tr h="1371600">'+cell('C')+cell('D')+'</a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>';slide=slide.replace('</p:spTree>',table+'</p:spTree>');zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}))}""")
        p.evaluate("""async bytes=>{const f=new File([new Uint8Array(bytes)],'table-audit.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});await globalThis.__inkdosPresentations.open(f)}""",fixture)
        p.wait_for_selector(".slide-table")
        p.locator('[data-table-row="0"][data-table-col="0"] .table-cell-content').dispatch_event("pointerdown")
        p.wait_for_function("()=>!document.getElementById('pptP2TableToolsBtn').disabled")
        p.locator("#pptP2TableToolsBtn").click()
        p.locator("#pptP2TableToolsPanel").wait_for(state="visible")

    def presentations(self):
        self.help_close()
        c,p,e=self.page()
        try:
            self.presentation_base(p)
            p.locator("#addSlideBtn").click(); p.locator("#addSlideBtn").click()
            p.wait_for_function("()=>globalThis.__inkdosPresentations.session.slides.length===3")
            self.click(p,e,"#moveSlideUpBtn","moveSlideUpBtn")
            self.click(p,e,"#moveSlideDownBtn","moveSlideDownBtn")
        finally:c.close()

        for sel in ("#pptP2ApplyBorder","#pptP2InsertRow","#pptP2DeleteRow","#pptP2InsertCol","#pptP2DeleteCol"):
            c,p,e=self.page()
            try:
                self.presentation_table(p)
                self.click(p,e,sel,sel[1:])
            finally:c.close()

        c,p,e=self.page()
        try:
            self.presentation_table(p)
            p.locator("#pptP2MergeRow").fill("1");p.locator("#pptP2MergeCol").fill("2")
            self.click(p,e,"#pptP2Merge","pptP2Merge")
            p.wait_for_timeout(300)
            cell=p.locator('[data-table-row="0"][data-table-col="0"] .table-cell-content')
            cell.wait_for(state="visible")
            cell.dispatch_event("pointerdown")
            p.wait_for_timeout(180)
            if p.locator("#pptP2TableToolsPanel").is_hidden():
                p.locator("#pptP2TableToolsBtn").click()
                p.locator("#pptP2TableToolsPanel").wait_for(state="visible")
            p.wait_for_function("()=>!document.getElementById('pptP2Split').disabled",timeout=5000)
            self.click(p,e,"#pptP2Split","pptP2Split")
        finally:c.close()

        c,p,e=self.page()
        try:
            self.presentation_table(p)
            self.click(p,e,'.ppt-p2-table-close',"Close table tools")
        finally:c.close()

        c,p,e=self.page()
        try:
            self.presentation_base(p); p.locator("#addSlideBtn").click()
            p.evaluate("()=>{const a=globalThis.__inkdosPresentations;a.session.sourceKind='ppt';a.executeCommand('navigation.to',0)}")
            p.locator("#legacyPptNotice").wait_for(state="visible")
            btn=p.get_by_role("button",name="Save editable PPTX copy",exact=True)
            downloads=[]
            p.on("download",lambda d:(downloads.append(d.suggested_filename),d.cancel()))
            try:
                btn.click(timeout=4000,no_wait_after=True);p.wait_for_timeout(250)
                self.record("Save editable PPTX copy","clicked","text=Save editable PPTX copy",effect={"downloads":downloads})
            except Exception as exc:self.record("Save editable PPTX copy","click-exception","text=Save editable PPTX copy",error=repr(exc))
        finally:c.close()

    def open_pdf(self,p,count=5):
        p.wait_for_function("()=>!!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
        ok=p.evaluate("""async count=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,pdf=await PDFLib.PDFDocument.create();for(let i=0;i<count;i++){const pg=pdf.addPage([612,792]);pg.drawText('Button audit page '+(i+1),{x:48,y:730,size:20})}const bytes=new Uint8Array(await pdf.save());return await d.fileOpen.openFile(new File([bytes],'button-audit.pdf',{type:'application/pdf'}))}""",count)
        if ok is not True: raise RuntimeError("PDF fixture failed")
        p.wait_for_function(f"()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.pageCount==={count}",timeout=20000)

    def pdf(self):
        self.help_close()

        c,p,e=self.page()
        try:
            self.open_pdf(p,5)
            p.evaluate("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.goToPage(3)")
            p.wait_for_function("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.currentPage===3")
            self.click(p,e,"#nextPageBtn","nextPageBtn")
            p.wait_for_function("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.currentPage===4")
            self.click(p,e,"#prevPageBtn","prevPageBtn")
        finally:c.close()

        c,p,e=self.page()
        try:
            self.open_pdf(p,5)
            p.locator("#pdfSearchBtn").click();p.locator("#pdfSearchInput").fill("Button audit page")
            p.wait_for_function("()=>document.querySelectorAll('.pdf-search-result').length===5",timeout=10000)
            self.click(p,e,"#pdfSearchNext","pdfSearchNext")
            self.click(p,e,"#pdfSearchPrev","pdfSearchPrev")
        finally:c.close()

        for sel,label in (("#pageMoveBtn","pageMoveBtn"),("#pageDeleteBtn","pageDeleteBtn"),("#pageSplitBtn","pageSplitBtn")):
            c,p,e=self.page()
            try:
                self.open_pdf(p,5)
                p.evaluate("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.layout.goToPage(2)")
                p.locator("#pageToolsBtn").click(); p.locator("#pageToolsPanel").wait_for(state="visible")
                if sel=="#pageMoveBtn": p.locator("#pageMoveTarget").fill("1")
                if sel=="#pageDeleteBtn": p.once("dialog",lambda d:d.accept())
                downloads=[]; p.on("download",lambda d:(downloads.append(d.suggested_filename),d.cancel()))
                self.click(p,e,sel,label)
                self.checks[-1]["effect"]={"downloads":downloads}
            finally:c.close()

        c,p,e=self.page()
        try:
            self.open_pdf(p,30)
            p.locator("#navPanelBtn").click(); p.locator("#pagesTab").click()
            p.wait_for_function("()=>document.querySelectorAll('#thumbGrid .thumb-card').length===24")
            self.click(p,e,"#thumbNextBlock","thumbNextBlock")
            p.wait_for_function("()=>document.getElementById('thumbRange').textContent.startsWith('25')")
            self.click(p,e,"#thumbPrevBlock","thumbPrevBlock")
        finally:c.close()

        c,p,e=self.page()
        try:
            self.open_pdf(p,1)
            p.evaluate("""()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug;window.__buttonAuditFlag=0;d.editor.addCommand({cmd:()=>{window.__buttonAuditFlag=1},undo:()=>{window.__buttonAuditFlag=0},mustExec:true})}""")
            p.wait_for_function("()=>!document.getElementById('undoBtn').disabled")
            self.click(p,e,"#undoBtn","undoBtn"); p.wait_for_function("()=>!document.getElementById('redoBtn').disabled")
            self.click(p,e,"#redoBtn","redoBtn")
            p.evaluate("""()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug;d.editor.deleteSelected=()=>{window.__buttonAuditDelete=1};d.editor.eventBus.dispatch('editingstateschanged',{source:d.editor,details:{hasSelectedEditor:true}})}""")
            p.wait_for_function("()=>!document.getElementById('deleteAnnotationBtn').disabled")
            self.click(p,e,"#deleteAnnotationBtn","deleteAnnotationBtn")
        finally:c.close()

        for action in ("cancel","save"):
            c,p,e=self.page()
            try:
                self.open_pdf(p,1)
                p.wait_for_selector(".pdf-page-shell")
                opened=p.evaluate("""()=>{const d=globalThis.InkDOS2PdfP4.PdfStabilityDebug,s=document.querySelector('.pdf-page-shell'),r=s.getBoundingClientRect();d.extensions.pointSelection({target:s,clientX:r.left+20,clientY:r.top+20});return d.annotationModes.openComment()}""")
                if not opened: raise RuntimeError("comment dialog did not open")
                p.locator("#commentDialog").wait_for(state="visible")
                if action=="save":
                    p.locator("#commentText").fill("button audit comment")
                    self.click(p,e,'#commentDialog button[type="submit"]',"Save comment")
                else:self.click(p,e,"#cancelComment","cancelComment")
            finally:c.close()

        c,p,e=self.page(width=390,height=850)
        try:
            self.open_pdf(p,1);p.wait_for_timeout(300)
            right=p.get_by_role("button",name="Scroll toolbar right")
            left=p.get_by_role("button",name="Scroll toolbar left")
            if right.is_enabled():
                self.click(p,e,'button[aria-label="Scroll toolbar right"]',"Scroll toolbar right")
                p.wait_for_timeout(250)
                self.click(p,e,'button[aria-label="Scroll toolbar left"]',"Scroll toolbar left")
            else:
                self.record("Scroll toolbar right","disabled-no-overflow",'button[aria-label="Scroll toolbar right"]')
                self.record("Scroll toolbar left","disabled-no-overflow",'button[aria-label="Scroll toolbar left"]')
        finally:c.close()

        c,p,e=self.page()
        try:
            self.hidden_redundant(p)
            for sel,reason in (("#highlightToolBtn","replaced by persistentHighlightBtn"),("#commentToolBtn","replaced by persistentNoteBtn")):
                row=p.locator(sel)
                self.hidden.append({"id":sel[1:],"text":None,"visible":row.is_visible(),"reason":reason})
        finally:c.close()

    def txt_dirty(self,p,text="changed"):
        p.locator("#startNew").click(); p.wait_for_function("()=>document.getElementById('startState').hidden===true")
        p.locator("#editor").fill(text); p.locator("#editor").dispatch_event("input"); p.wait_for_timeout(100)

    def txt(self):
        self.help_close()
        c,p,e=self.page()
        try:
            self.txt_dirty(p)
            p.wait_for_function("()=>!document.getElementById('undoBtn').disabled")
            self.click(p,e,"#undoBtn","undoBtn")
            p.wait_for_function("()=>!document.getElementById('redoBtn').disabled")
            self.click(p,e,"#redoBtn","redoBtn")
        finally:c.close()

        for sel,label,expected in (("#discardCancel","discardCancel",False),("#discardContinue","discardContinue",True),("#discardSave","discardSave",True)):
            c,p,e=self.page()
            try:
                self.txt_dirty(p,label)
                if sel=="#discardSave":
                    p.evaluate("""()=>{globalThis.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{},close:async()=>{}})})}""")
                p.evaluate("""()=>{globalThis.__buttonAuditPending=InkDOS2.TxtAppDebug.authorizeReplacement('button audit replacement?')}""")
                p.locator("#discardDialog").wait_for(state="visible")
                self.click(p,e,sel,label)
                result=p.evaluate("async()=>await globalThis.__buttonAuditPending")
                self.checks[-1]["effect"]={"authorizeResult":result}
            finally:c.close()

        for sel,label in (("#xmlToolsBtn","xmlToolsBtn"),("text=Validate XML","Validate XML"),("text=Pretty-print XML","Pretty-print XML"),("text=Syntax preview","Syntax preview"),("text=Structure tree","Structure tree")):
            c,p,e=self.page()
            try:
                p.wait_for_function("()=>!!globalThis.InkDOS2?.TxtAppDebug")
                p.evaluate("""async()=>await InkDOS2.TxtAppDebug.openBytes('audit.xml',new TextEncoder().encode('<?xml version="1.0"?><root><item>audit</item></root>'))""")
                p.wait_for_function("()=>!document.getElementById('xmlToolsBtn').hidden")
                if sel!="#xmlToolsBtn":p.locator("#xmlToolsBtn").click();p.locator("#xmlToolsMenu").wait_for(state="visible")
                self.click(p,e,sel,label)
            finally:c.close()

        c,p,e=self.page(width=390,height=850)
        try:
            p.locator("#startNew").click();p.wait_for_timeout(250)
            right=p.get_by_role("button",name="Scroll toolbar right");left=p.get_by_role("button",name="Scroll toolbar left")
            if right.is_enabled():
                self.click(p,e,'button[aria-label="Scroll toolbar right"]',"Scroll toolbar right");p.wait_for_timeout(250);self.click(p,e,'button[aria-label="Scroll toolbar left"]',"Scroll toolbar left")
            else:
                self.record("Scroll toolbar right","disabled-no-overflow",'button[aria-label="Scroll toolbar right"]');self.record("Scroll toolbar left","disabled-no-overflow",'button[aria-label="Scroll toolbar left"]')
        finally:c.close()

    def epub_open(self,p):
        p.locator("#fileInput").set_input_files(str(self.epub_path))
        p.wait_for_function("()=>globalThis.__InkEpubR4?.state()?.book?.chapters?.length===2",timeout=15000)

    def epub_bookmark_library(self,p):
        self.epub_open(p);p.locator("#bookmarkBtn").click();p.locator("#tocBtn").click()
        lib=p.locator('[data-nav-tab="library"]');lib.wait_for(state="visible");lib.click()
        p.locator('[data-nav-panel="library"]').wait_for(state="visible")

    def epub(self):
        self.help_close()
        c,p,e=self.page()
        try:
            self.epub_open(p)
            self.click(p,e,"#nextBtn","nextBtn");self.click(p,e,"#prevBtn","prevBtn")
        finally:c.close()

        c,p,e=self.page()
        try:
            self.epub_open(p);p.locator("#searchBtn").click();p.locator("#bookSearchInput").fill("Chapter")
            p.wait_for_function("()=>document.querySelectorAll('#searchResults button').length>=2",timeout=10000)
            self.click(p,e,"#searchNext","searchNext");self.click(p,e,"#searchPrev","searchPrev")
            p.locator("#searchResults button").first.click();p.wait_for_timeout(150)
            self.click(p,e,"#readingBackBtn","readingBackBtn")
        finally:c.close()

        for action in ("open","add-note","remove","library-save","library-cancel"):
            c,p,e=self.page()
            try:
                self.epub_bookmark_library(p)
                if action=="open":self.click(p,e,".epub-nav-open","Open bookmark")
                elif action=="remove":self.click(p,e,".epub-nav-delete","Remove bookmark")
                else:
                    note=p.locator('[aria-label="Add note to bookmark"]')
                    note.scroll_into_view_if_needed()
                    p.wait_for_timeout(120)
                    note.click(timeout=5000)
                    p.locator("#libraryCompose").wait_for(state="visible")
                    if action=="add-note":self.record("Add note to bookmark","clicked",'[aria-label="Add note to bookmark"]')
                    elif action=="library-cancel":self.click(p,e,"#libraryCancelNote","libraryCancelNote")
                    else:
                        p.locator("#libraryDraft").fill("button audit bookmark note");self.click(p,e,"#librarySaveNote","librarySaveNote")
            finally:c.close()

        for action in ("cancel","save"):
            c,p,e=self.page()
            try:
                self.epub_open(p);p.locator("#noteModeBtn").click()
                p.evaluate("""()=>{const p=document.querySelector('#readerSurface p');const w=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);const n=w.nextNode();const r=document.createRange();r.setStart(n,0);r.setEnd(n,Math.min(8,n.nodeValue.length));const s=getSelection();s.removeAllRanges();s.addRange(r);document.dispatchEvent(new Event('selectionchange'))}""")
                p.locator(".epub-note-backdrop").wait_for(state="visible",timeout=5000)
                if action=="cancel":self.click(p,e,"[data-note-cancel]","Cancel note")
                else:
                    p.locator(".epub-note-dialog textarea").fill("button audit passage note")
                    self.click(p,e,'.epub-note-dialog button[type="submit"]',"Save note")
            finally:c.close()

        c,p,e=self.page(width=390,height=850)
        try:
            self.epub_open(p);p.wait_for_timeout(300)
            right=p.get_by_role("button",name="Scroll toolbar right");left=p.get_by_role("button",name="Scroll toolbar left")
            if right.is_enabled():
                self.click(p,e,'button[aria-label="Scroll toolbar right"]',"Scroll toolbar right");p.wait_for_timeout(250);self.click(p,e,'button[aria-label="Scroll toolbar left"]',"Scroll toolbar left")
            else:
                self.record("Scroll toolbar right","disabled-no-overflow",'button[aria-label="Scroll toolbar right"]');self.record("Scroll toolbar left","disabled-no-overflow",'button[aria-label="Scroll toolbar left"]')
        finally:c.close()

        c,p,e=self.page()
        try:
            self.hidden_redundant(p)
            for sel,reason in (("#highlightClear","hidden by persistent EPUB annotation-mode CSS"),("#highlightClose","hidden inside compact color popover header")):
                row=p.locator(sel)
                self.hidden.append({"id":sel[1:],"text":None,"visible":row.is_visible(),"reason":reason})
        finally:c.close()

    def run(self):
        getattr(self,self.app)()
        failures=[x for x in self.checks if x["status"] in ("click-exception","clicked-with-error","disabled")]
        report={"app":self.app,"checks":self.checks,"intentionallyHidden":self.hidden,"summary":{"checks":len(self.checks),"clicked":sum(1 for x in self.checks if x["status"]=="clicked"),"disabledNoOverflow":sum(1 for x in self.checks if x["status"]=="disabled-no-overflow"),"failures":len(failures),"hiddenByDesign":len(self.hidden)}}
        (OUT/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(report["summary"],indent=2))
        if failures: raise SystemExit("Conditional button audit failures: "+json.dumps(failures,ensure_ascii=False))

def main():
    apps=(APP,) if APP else APPS
    with tempfile.TemporaryDirectory() as td:
        ep=Path(td)/"button-audit.epub";build_epub(ep)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            all_reports=[]
            for app in apps:
                a=Audit(browser,app,ep);a.run();all_reports.append(app)
            browser.close()
    print("Conditional button audits passed:",", ".join(all_reports))

if __name__=="__main__":main()

#!/usr/bin/env python3
from __future__ import annotations
import os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8769
BASE=f'http://127.0.0.1:{PORT}'

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

def main():
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            args={'headless':True}
            if os.environ.get('CHROMIUM_PATH'):args['executable_path']=os.environ['CHROMIUM_PATH']
            browser=pw.chromium.launch(**args)
            page=browser.new_page(viewport={'width':1280,'height':900})
            page.goto(BASE+'/apps/presentations/',wait_until='load')
            page.wait_for_function('() => !!globalThis.InkDOS2Presentations?.PresentationsApp')
            result=page.evaluate(r"""async()=>{
              const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel,app=NS.PresentationsApp;
              const src=new NS.PresentationSession();src.resetNew();
              const setTitle=(slide,text)=>{const o=slide.objects[0];o.text=text;o.paragraphs=M.normalizeParagraphs(null,text,o)};
              setTitle(src.slides[0],'Alpha');src.addSlide();setTitle(src.currentSlide,'Beta');src.addSlide();setTitle(src.currentSlide,'Gamma');src.setCurrentByIndex(0);
              const sourceBytes=await NS.PptxWriter.build(src),opened=await app.open(new File([sourceBytes],'Structure.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'}));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
              const controls={add:document.getElementById('addSlideBtn').disabled,dup:document.getElementById('duplicateSlideBtn').disabled,del:document.getElementById('deleteSlideBtn').disabled,moveUp:!!document.getElementById('moveSlideUpBtn'),moveDown:!!document.getElementById('moveSlideDownBtn')};
              const originalParts=app.session.slides.map(s=>s.sourcePart);
              app.session.setCurrentByIndex(0);const dup=app.session.duplicateCurrent();setTitle(dup,'Alpha Copy');app.session.moveCurrent(1);
              const added=app.session.addSlide();setTitle(added,'Added');
              app.session.setCurrentByIndex(0);app.session.deleteCurrent();
              app.session.setCurrentByIndex(app.session.slides.length-1);app.session.moveCurrent(-2);app.session.markDirty();
              const modelTitles=app.session.slides.map(s=>s.objects.filter(o=>o.type==='text').map(o=>o.text).join(' | '));
              await new Promise((resolve,reject)=>{if(NS.PptP1StructureWriter)return resolve();const s=document.createElement('script');s.src='io/ppt-p1-structure-writer.js';s.onload=resolve;s.onerror=reject;document.head.appendChild(s)});
              const built=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(built.bytes,{checkCRC32:true}),pres=await zip.file('ppt/presentation.xml').async('text'),rels=await zip.file('ppt/_rels/presentation.xml.rels').async('text');
              const pd=new DOMParser().parseFromString(pres,'application/xml'),rd=new DOMParser().parseFromString(rels,'application/xml'),ids=[...pd.getElementsByTagNameNS('*','sldId')],relMap=new Map([...rd.getElementsByTagNameNS('*','Relationship')].filter(x=>(x.getAttribute('Type')||'').endsWith('/slide')).map(x=>[x.getAttribute('Id'),x.getAttribute('Target')]));
              const order=ids.map(x=>{const a=[...x.attributes].find(a=>a.localName==='id'&&a.prefix==='r');return relMap.get(a?.value||x.getAttribute('r:id'))||''});
              const parts=built.receipt.slideMappings.map(x=>x.slidePart),decoded=await NS.PptxOpenController.decodePptx(built.bytes,'Roundtrip.pptx'),decodedTitles=decoded.slides.map(s=>s.objects.filter(o=>o.type==='text').map(o=>o.text).join(' | '));
              const reopened=await app.open(new File([built.bytes],'Roundtrip.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'}));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
              const reopenedTitles=app.session.slides.map(s=>s.objects.filter(o=>o.type==='text').map(o=>o.text).join(' | '));
              return{opened:!!opened,controls,originalParts,modelTitles,receipt:built.receipt,parts,order,decodedTitles,reopened:!!reopened,reopenedCount:app.session.slides.length,reopenedTitles,allParts:Object.keys(zip.files)};
            }""")
            browser.close()
        assert result['opened'] is True,result
        assert result['controls']['add'] is False and result['controls']['dup'] is False and result['controls']['del'] is False,result
        assert result['controls']['moveUp'] and result['controls']['moveDown'],result
        assert result['receipt']['mode']=='package-preserving-pptx-structure',result
        assert result['receipt']['slideCount']==4,result
        assert len(result['receipt']['slideMappings'])==4,result
        assert len(set(result['parts']))==4,result
        assert len(result['order'])==4,result
        assert all(('ppt/'+x) in result['allParts'] for x in result['order']),result
        assert not any(t=='Alpha' or t.startswith('Alpha |') for t in result['modelTitles']),result
        for titles in [result['decodedTitles'],result['reopenedTitles']]:
            joined='\n'.join(titles)
            assert 'Alpha Copy' in joined and 'Added' in joined and 'Beta' in joined and 'Gamma' in joined,result
            assert not any(t=='Alpha' or t.startswith('Alpha |') for t in titles),result
        assert result['reopened'] is True and result['reopenedCount']==4,result
        print('PPT-P1 imported slide add/duplicate/delete/reorder roundtrip passed.')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

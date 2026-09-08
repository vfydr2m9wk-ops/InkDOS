#!/usr/bin/env python3
from __future__ import annotations
import os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8767
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
            page.goto(BASE+'/apps/documents/',wait_until='load')
            page.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsApp?.d2Sections')
            result=page.evaluate(r"""async()=>{
              const NS=globalThis.InkDOS2Documents,app=NS.DocumentsApp;
              await app.newDocument();
              const host=document.getElementById('pagesHost'),pc=host.querySelector('.page-content');
              pc.innerHTML='<p>Section one alpha.</p><p>Section one beta.</p><p>Section two gamma.</p><p>Section two delta.</p>';
              const caret=el=>{const r=document.createRange();r.selectNodeContents(el);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r);app.d1?.inspect?.();};
              caret(pc.querySelectorAll('p')[0]);
              document.getElementById('d2Columns').value='2';document.getElementById('d2ColumnGap').value='28';
              await app.d2Sections.applyColumns();
              let paragraphs=[...host.querySelectorAll('.page-content p')];
              caret(paragraphs.find(p=>p.textContent.includes('beta')));
              await app.d2Sections.insertBreak();
              paragraphs=[...host.querySelectorAll('.page-content p')];
              caret(paragraphs.find(p=>p.textContent.includes('gamma')));
              document.getElementById('d2Columns').value='1';document.getElementById('d2ColumnGap').value='36';
              await app.d2Sections.applyColumns();
              const before=app.d2Sections.inspect();
              const rendered=[...host.querySelectorAll('.doc-page')].map(p=>({columns:p._pageSpec?.columns||1,css:p.querySelector('.page-content')?.style.columnCount||'',text:p.querySelector('.page-content')?.innerText||''}));
              const saved=await NS.DocxWriter.save(host,'D2-Sections.docx',null,null),bytes=new Uint8Array(await saved.blob.arrayBuffer()),zip=await JSZip.loadAsync(bytes),docXml=await zip.file('word/document.xml').async('string');
              const xml=new DOMParser().parseFromString(docXml,'application/xml'),local=n=>[...xml.getElementsByTagNameNS('*',n)],aval=(e,n)=>{if(!e)return'';for(const a of [...e.attributes])if(a.localName===n)return a.value;return''};
              const sects=local('sectPr'),cols=sects.map(s=>{const c=[...s.children].find(x=>x.localName==='cols');return{num:Number(aval(c,'num')||1),space:Number(aval(c,'space')||0),type:aval([...s.children].find(x=>x.localName==='type'),'val')}});
              const parsed=await NS.DocxParser.parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
              const parsedSections=(parsed.blocks||[]).map((b,i)=>({i,columns:b.pageSpec?.columns||1,start:!!b.sectionStart,html:b.html||''}));
              const f=new File([bytes],'D2-Sections.docx',{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}),reopened=await app.open(f,{authorized:true});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
              const after=app.d2Sections.inspect(),reopenedPages=[...host.querySelectorAll('.doc-page')].map(p=>({columns:p._pageSpec?.columns||1,css:p.querySelector('.page-content')?.style.columnCount||'',text:p.querySelector('.page-content')?.innerText||''}));
              return{before,rendered,docXml,cols,parsedSections,reopened:!!reopened,after,reopenedPages};
            }""")
            browser.close()
        assert result['before']['sections']>=2,result
        assert 2 in result['before']['columns'] and 1 in result['before']['columns'],result
        assert any(p['columns']==2 and p['css']=='2' for p in result['rendered']),result
        assert any(c['num']==2 and c['type']=='nextPage' for c in result['cols']),result
        assert result['cols'][-1]['num']==1,result
        assert any(x['columns']==2 for x in result['parsedSections']),result
        assert any(x['start'] and x['columns']==1 for x in result['parsedSections']),result
        assert 'data-d2-section-end="1"' in ''.join(x['html'] for x in result['parsedSections']),result
        assert result['reopened'] is True,result
        assert result['after']['sections']>=2,result
        assert any(p['columns']==2 and p['css']=='2' for p in result['reopenedPages']),result
        assert any(p['columns']==1 for p in result['reopenedPages']),result
        assert 'Section one alpha' in '\n'.join(p['text'] for p in result['reopenedPages']),result
        assert 'Section two delta' in '\n'.join(p['text'] for p in result['reopenedPages']),result
        print('DOC-D2 section/columns OOXML/reopen roundtrip passed.')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

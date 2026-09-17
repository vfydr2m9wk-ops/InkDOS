#!/usr/bin/env python3
from __future__ import annotations
import os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8766
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
            page.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsApp?.d2')
            result=page.evaluate(r"""async()=>{
              const NS=globalThis.InkDOS2Documents,app=NS.DocumentsApp;
              await app.newDocument();
              const host=document.getElementById('pagesHost'),pc=host.querySelector('.page-content');
              pc.innerHTML=`<h2>Clinical Heading</h2>
                <p data-d2-rich="1">Reviewed <span class="d2-comment" data-d2-comment-id="c1" data-d2-comment-text="Review note">important text</span> with evidence<sup class="d2-footnote-ref" contenteditable="false" data-d2-footnote-id="f1" data-d2-footnote-text="Footnote body">1</sup>.</p>
                <p class="d2-style-quote" data-d2-style="Quote">Quoted paragraph</p>
                <table data-d2-table-dirty="1"><tbody><tr><td colspan="2">Merged</td></tr><tr><td>A</td><td>B</td></tr></tbody></table>`;
              await app.d2.updateToc();
              const saved=await NS.DocxWriter.save(host,'D2-P1.docx',null,null),bytes=new Uint8Array(await saved.blob.arrayBuffer()),zip=await JSZip.loadAsync(bytes);
              const read=async p=>zip.file(p)?zip.file(p).async('string'):'';
              const docXml=await read('word/document.xml'),comments=await read('word/comments.xml'),footnotes=await read('word/footnotes.xml'),rels=await read('word/_rels/document.xml.rels'),types=await read('[Content_Types].xml'),styles=await read('word/styles.xml');
              const parsed=await NS.DocxParser.parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
              const parsedHtml=(parsed.blocks||[]).map(b=>b.html||'').join('\n');
              const f=new File([bytes],'D2-P1.docx',{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'});
              const reopened=await app.open(f,{authorized:true});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
              return {docXml,comments,footnotes,rels,types,styles,parsedHtml,reopened:!!reopened,html:[...host.querySelectorAll('.page-content')].map(x=>x.innerHTML).join('\n'),text:[...host.querySelectorAll('.page-content')].map(x=>x.innerText).join('\n'),inspect:app.d2.inspect(),colspan:host.querySelector('table td')?.colSpan||0};
            }""")
            browser.close()
        assert 'commentRangeStart' in result['docXml'] and 'commentReference' in result['docXml'],result
        assert 'footnoteReference' in result['docXml'],result
        assert 'w:pStyle' in result['docXml'] and 'TOCHeading' in result['docXml'] and 'TOC2' in result['docXml'] and 'Quote' in result['docXml'],result
        assert 'gridSpan' in result['docXml'] and 'w:val="2"' in result['docXml'],result
        assert 'Review note' in result['comments'],result
        assert 'Footnote body' in result['footnotes'],result
        assert '/comments' in result['rels'] and '/footnotes' in result['rels'],result
        assert '/word/comments.xml' in result['types'] and '/word/footnotes.xml' in result['types'],result
        assert 'TOCHeading' in result['styles'] and 'Heading3' in result['styles'] and 'Subtitle' in result['styles'] and 'Quote' in result['styles'],result
        assert 'data-d2-comment-text="Review note"' in result['parsedHtml'],result
        assert 'data-d2-footnote-text="Footnote body"' in result['parsedHtml'],result
        assert 'd2-style-quote' in result['parsedHtml'],result
        assert result['reopened'] is True,result
        assert 'Review note' in result['html'] and 'Footnote body' in result['html'],result
        assert 'Table of Contents' in result['text'] and 'Clinical Heading' in result['text'],result
        assert result['inspect']['comments']>=1 and result['inspect']['footnotes']>=1 and result['inspect']['tocEntries']>=1,result
        assert result['colspan']==2,result
        print('DOC-D2 P1 browser OOXML/reopen roundtrip passed.')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

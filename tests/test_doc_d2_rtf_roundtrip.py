#!/usr/bin/env python3
from __future__ import annotations
import os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8768
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
            page.wait_for_function('() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!globalThis.InkDOS2Documents?.RtfImporter')
            result=page.evaluate(r"""async()=>{
              const NS=globalThis.InkDOS2Documents,app=NS.DocumentsApp,host=document.getElementById('pagesHost');
              const rtf=String.raw`{\rtf1\ansi\ansicpg1252\deff0
{\fonttbl{\f0 Calibri;}{\f1 Times New Roman;}}
{\colortbl;\red33\green66\blue99;\red255\green255\blue0;}
\viewkind4\uc1
\pard\qc\f1\fs32\cf1\b InkDOS RTF Import\b0\par
\pard\ql\f0\fs22 Plain text with \i italic\i0, \ul underline\ulnone, \strike strike\strike0, \highlight2 highlight\highlight0.\par
Unicode: caf\'e9, em dash \emdash, snowman \u9731? and smart \lquote quotes\rquote.\par
Math H\sub 2\nosupersub O and x\super 2\nosupersub.\par
\page
\pard\qr Second page aligned right.\par
}`;
              const bytes=new TextEncoder().encode(rtf),file=new File([bytes],'Legacy Sample.rtf',{type:'application/rtf'});
              const opened=await app.open(file,{authorized:true});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
              const imported={opened:!!opened,kind:app.session.kind,name:app.session.fileName,sourceNull:app.session.sourceBuffer===null,text:[...host.querySelectorAll('.page-content')].map(x=>x.innerText).join('\n'),html:[...host.querySelectorAll('.page-content')].map(x=>x.innerHTML).join('\n'),pages:host.querySelectorAll('.doc-page').length,accept:document.getElementById('fileInput').accept};
              const last=host.querySelector('.page-content p:last-of-type')||host.querySelector('.page-content p');last.append(document.createTextNode(' Edited locally.'));app.session.markDirty();
              const saved=await NS.DocxWriter.save(host,app.session.fileName,app.session.sourceBuffer,app.session.sourceContext),out=new Uint8Array(await saved.blob.arrayBuffer()),zip=await JSZip.loadAsync(out),docXml=await zip.file('word/document.xml').async('string');
              const reopened=await app.open(new File([out],saved.fileName||app.session.fileName,{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}),{authorized:true});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
              return{imported,savedName:saved.fileName,docXml,reopened:!!reopened,reopenedKind:app.session.kind,reopenedSource:app.session.sourceBuffer instanceof ArrayBuffer,reopenedName:app.session.fileName,reopenedText:[...host.querySelectorAll('.page-content')].map(x=>x.innerText).join('\n')};
            }""")
            browser.close()
        imp=result['imported']
        assert imp['opened'] is True,result
        assert imp['kind']=='rtf' and imp['sourceNull'] is True,result
        assert imp['name']=='Legacy Sample.docx',result
        assert '.rtf' in imp['accept'],result
        for text in ['InkDOS RTF Import','Plain text with','italic','underline','strike','café','snowman ☃','H2O','x2','Second page aligned right']:
            assert text in imp['text'],(text,result)
        assert imp['pages']>=2,result
        assert 'font-weight:700' in imp['html'],result
        assert 'font-style:italic' in imp['html'],result
        assert 'text-decoration:underline' in imp['html'],result
        assert 'line-through' in imp['html'],result
        assert result['savedName'].endswith('.docx'),result
        assert '<w:document' in result['docXml'] and 'Edited locally.' in result['docXml'],result
        assert result['reopened'] is True,result
        assert result['reopenedKind']=='docx' and result['reopenedSource'] is True,result
        assert result['reopenedName'].endswith('.docx'),result
        assert 'InkDOS RTF Import' in result['reopenedText'] and 'Edited locally.' in result['reopenedText'],result
        print('DOC-D2 RTF import → edit → DOCX → reopen roundtrip passed.')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()

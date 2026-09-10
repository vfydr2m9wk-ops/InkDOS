#!/usr/bin/env python3
from __future__ import annotations
import os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8776
BASE=f'http://127.0.0.1:{PORT}'
PNG_B64='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nJsAAAAASUVORK5CYII='


def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')


def close_enough(a,b,tol=2):
    return abs(float(a)-float(b))<=tol


def main():
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            args={'headless':True}
            if os.environ.get('CHROMIUM_PATH'):args['executable_path']=os.environ['CHROMIUM_PATH']
            browser=pw.chromium.launch(**args)
            page=browser.new_page(viewport={'width':1400,'height':980})
            page.goto(BASE+'/apps/presentations/',wait_until='load')
            page.wait_for_function('() => !!globalThis.InkDOS2Presentations?.PresentationModel')
            results=page.evaluate(r"""async(pngB64)=>{
              const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
              async function load(src,test){if(test())return;await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.head.appendChild(s)});if(!test())throw new Error(src+' did not initialize')}
              await load('io/ppt-p1-object-writer.js',()=>!!NS.PptP1ObjectWriter);
              const cases=[
                {name:'4:3',w:9144000,h:6858000},
                {name:'16:9',w:12192000,h:6858000}
              ];
              const out=[];
              for(const c of cases){
                const s=new NS.PresentationSession();s.resetNew();s.sourceKind='ppt';s.fileName='Synthetic-'+c.name+'.ppt';
                const slide=s.slides[0];slide.widthEmu=c.w;slide.heightEmu=c.h;
                const text=M.textObject({id:'legacy-text',x:c.w*.081,y:c.h*.117,w:c.w*.537,h:c.h*.241,text:'Synthetic legacy text\nSecond line',fontSizePt:19,bold:true,italic:true,align:'center',color:'#234567',fontFamily:'Arial',rotation:7,verticalAlign:'middle',marginLeftEmu:57150,marginRightEmu:76200,marginTopEmu:38100,marginBottomEmu:50800,richSource:'ppt-legacy'});
                const shape=M.shapeObject({id:'legacy-shape',shapeType:'ellipse',x:c.w*.603,y:c.h*.182,w:c.w*.251,h:c.h*.296,fill:'#CDE2F4',line:{color:'#345678',widthEmu:19050},rotation:-11});
                const image=M.imageObject({id:'legacy-image',src:'data:image/png;base64,'+pngB64,mime:'image/png',x:c.w*.144,y:c.h*.558,w:c.w*.317,h:c.h*.263,rotation:5,line:{color:'#557799',widthEmu:12700}});
                slide.objects=[text,shape,image];s.currentSlideId=slide.id;
                const source={w:slide.widthEmu,h:slide.heightEmu,objects:slide.objects.map(o=>({id:o.id,type:o.type,x:o.x,y:o.y,w:o.w,h:o.h,rotation:o.rotation,fontSizePt:o.fontSizePt,align:o.align,verticalAlign:o.verticalAlign,color:o.color,fontFamily:o.fontFamily,marginLeftEmu:o.marginLeftEmu,marginRightEmu:o.marginRightEmu,marginTopEmu:o.marginTopEmu,marginBottomEmu:o.marginBottomEmu,text:o.text,shapeType:o.shapeType,fill:o.fill,line:o.line,mime:o.mime}))};
                const bytes=await NS.PptxWriter.build(s);
                const reopened=await NS.PptxOpenController.decodePptx(bytes,'Synthetic-'+c.name+'.pptx');
                const d=reopened.slides[0];
                out.push({name:c.name,source,reopened:{w:d.widthEmu,h:d.heightEmu,objects:d.objects.map(o=>({type:o.type,x:o.x,y:o.y,w:o.w,h:o.h,rotation:o.rotation,fontSizePt:o.fontSizePt,align:o.align,verticalAlign:o.verticalAlign,color:o.color,fontFamily:o.fontFamily,marginLeftEmu:o.marginLeftEmu,marginRightEmu:o.marginRightEmu,marginTopEmu:o.marginTopEmu,marginBottomEmu:o.marginBottomEmu,text:o.text,shapeType:o.shapeType,fill:o.fill,line:o.line,mime:o.mime}))}});
              }
              return out;
            }""",PNG_B64)
            browser.close()

        for case in results:
            src,got=case['source'],case['reopened']
            assert close_enough(src['w'],got['w']) and close_enough(src['h'],got['h']),case
            assert len(got['objects'])==3,case
            by_type={o['type']:o for o in got['objects']}
            for original in src['objects']:
                reopened=by_type[original['type']]
                for key in ('x','y','w','h'):
                    assert close_enough(original[key],reopened[key]),(case['name'],original['type'],key,original[key],reopened[key])
                assert abs(float(original.get('rotation') or 0)-float(reopened.get('rotation') or 0))<.2,(case['name'],original['type'],'rotation',original,reopened)
            text=by_type['text'];source_text=next(o for o in src['objects'] if o['type']=='text')
            assert text['text']==source_text['text'],case
            assert abs(float(text['fontSizePt'])-19)<.2,case
            assert text['align']=='center' and text['verticalAlign']=='middle',case
            assert (text['color'] or '').lower()=='#234567' and text['fontFamily']=='Arial',case
            for key in ('marginLeftEmu','marginRightEmu','marginTopEmu','marginBottomEmu'):
                assert close_enough(text[key],source_text[key]),(case['name'],key,source_text[key],text[key])
            shape=by_type['shape']
            assert shape['shapeType']=='ellipse' and (shape['fill'] or '').lower()=='#cde2f4',case
            image=by_type['image']
            assert image['mime']=='image/png',case
        print('Synthetic legacy PPT normalized model -> editable PPTX geometry/text fidelity passed for 4:3 and 16:9.')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()


if __name__=='__main__':main()

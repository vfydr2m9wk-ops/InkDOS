#!/usr/bin/env python3
from __future__ import annotations
import base64,os,socket,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8770
BASE=f'http://127.0.0.1:{PORT}'
PNG_B64='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nJsAAAAASUVORK5CYII='
PPTX_MIME='application/vnd.openxmlformats-officedocument.presentationml.presentation'

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

def hit_target(page,selector):
    box=page.locator(selector).bounding_box()
    assert box,selector
    x=box['x']+box['width']/2;y=box['y']+box['height']/2
    return page.evaluate("""p=>{const e=document.elementFromPoint(p.x,p.y);return e?{tag:e.tagName,cls:e.className||'',handle:e.dataset?.p1Handle||null,objectId:e.dataset?.objectId||null}:null}""",{'x':x,'y':y})

def drag(page,selector,dx,dy):
    box=page.locator(selector).bounding_box()
    assert box,selector
    x=box['x']+box['width']/2;y=box['y']+box['height']/2
    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+dx,y+dy,steps=6);page.mouse.up()

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
            page.wait_for_function('() => !!globalThis.InkDOS2Presentations?.PresentationsApp?.p1Tools')
            source_b64=page.evaluate(r"""async()=>{
              const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel,src=new NS.PresentationSession();src.resetNew();src.slides[0].objects[0].text='Imported Home Slide';src.slides[0].objects[0].paragraphs=M.normalizeParagraphs(null,'Imported Home Slide',src.slides[0].objects[0]);const bytes=await NS.PptxWriter.build(src);let s='',chunk=0x8000;for(let i=0;i<bytes.length;i+=chunk)s+=String.fromCharCode(...bytes.subarray(i,i+chunk));return btoa(s)
            }""")
            page.locator('#fileInput').set_input_files(files=[{'name':'Objects.pptx','mimeType':PPTX_MIME,'buffer':base64.b64decode(source_b64)}])
            page.wait_for_function("() => globalThis.__inkdosPresentations?.session?.sourceKind==='pptx' && document.getElementById('startState')?.hidden===true")
            setup=page.evaluate(r"""async()=>{
              const app=globalThis.__inkdosPresentations;const shape=document.getElementById('pptP1Shape');shape.value='ellipse';shape.dispatchEvent(new Event('change',{bubbles:true}));await new Promise(r=>requestAnimationFrame(r));const o=app.selection.getObject(app.session);app.p1Tools.applyFill('#336699');app.p1Tools.applyBorder('#993333');return{opened:app.session.sourceKind==='pptx',startHidden:document.getElementById('startState')?.hidden===true,shapeId:o?.id,overlay:!!document.querySelector('.ppt-p1-object-overlay'),handles:document.querySelectorAll('.ppt-p1-handle').length,before:{x:o?.x,y:o?.y,w:o?.w,h:o?.h,rotation:o?.rotation}};
            }""")
            assert setup['opened'] and setup['startHidden'] and setup['shapeId'] and setup['overlay'] and setup['handles']==3,setup
            setup['hitTargets']={s:hit_target(page,s) for s in ['.ppt-p1-handle.move','.ppt-p1-handle.resize','.ppt-p1-handle.rotate']}
            assert all(v and 'ppt-p1-handle' in str(v.get('cls','')) for v in setup['hitTargets'].values()),setup
            drag(page,'.ppt-p1-handle.move',36,24)
            drag(page,'.ppt-p1-handle.resize',42,30)
            drag(page,'.ppt-p1-handle.rotate',-34,48)
            result=page.evaluate(r"""async(pngB64)=>{
              const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel,app=NS.PresentationsApp;
              const shape=app.session.currentSlide.objects.find(o=>o.id===document.querySelector('.ppt-p1-object-overlay')?.dataset.objectId);
              const afterShape={id:shape.id,x:shape.x,y:shape.y,w:shape.w,h:shape.h,rotation:shape.rotation,fill:shape.fill,line:shape.line};
              document.getElementById('insertTextBtn').click();let text=app.selection.getObject(app.session);app.history.transact('Test text',()=>{text.text='Home bullet item';text.paragraphs=M.normalizeParagraphs(null,text.text,text)});app.p1Tools.toggleBullets();app.p1Tools.applyTextColor('#2244AA');
              const textState={id:text.id,color:text.color,bullet:text.paragraphs[0]?.bullet,text:text.text};
              const layout=document.getElementById('pptP1Layout');layout.value='twoContent';layout.dispatchEvent(new Event('change',{bubbles:true}));
              const bin=atob(pngB64),arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);const image=await app.p1Tools.insertImage(new File([arr],'pixel.png',{type:'image/png'}));app.p1Tools.applyBorder('#117744');const imageState={id:image.id,line:image.line,w:image.w,h:image.h};
              async function load(src,test){if(test())return;await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.head.appendChild(s)});if(!test())throw new Error(src+' did not initialize')}
              await load('io/ppt-p1-structure-writer.js',()=>!!NS.PptP1StructureWriter);await load('io/ppt-p1-object-writer.js',()=>!!NS.PptP1ObjectWriter);
              const built=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(built.bytes,{checkCRC32:true}),part=built.receipt.slideMappings[0].slidePart,slideXml=await zip.file(part).async('text'),rels=await zip.file(part.replace('/slides/','/slides/_rels/')+'.rels').async('text'),media=Object.keys(zip.files).filter(x=>x.startsWith('ppt/media/inkdos'));
              const decoded=await NS.PptxOpenController.decodePptx(built.bytes,'Objects-roundtrip.pptx'),d=decoded.slides[0],decodedState={count:d.objects.length,types:d.objects.map(o=>o.type),texts:d.objects.filter(o=>o.type==='text').map(o=>({text:o.text,color:o.color,bullet:o.paragraphs?.[0]?.bullet,x:o.x,y:o.y,w:o.w,h:o.h})),shapes:d.objects.filter(o=>o.type==='shape').map(o=>({shapeType:o.shapeType,fill:o.fill,line:o.line,x:o.x,y:o.y,w:o.w,h:o.h,rotation:o.rotation})),images:d.objects.filter(o=>o.type==='image').map(o=>({mime:o.mime,x:o.x,y:o.y,w:o.w,h:o.h}))};
              const reopened=await app.open(new File([built.bytes],'Objects-roundtrip.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'}));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const reopenedTypes=app.session.currentSlide.objects.map(o=>o.type);
              const fresh=new NS.PresentationSession();fresh.resetNew();const fs=fresh.addShape('roundRect');fs.fill='#445566';fs.rotation=17;fresh.addImage({src:'data:image/png;base64,'+pngB64,mime:'image/png',widthEmu:2400000,heightEmu:1600000});const ft=fresh.addText();ft.text='Fresh bullet';ft.paragraphs=M.normalizeParagraphs(null,ft.text,ft);ft.paragraphs[0].bullet='•';ft.color='#AA2244';for(const r of ft.paragraphs[0].runs)r.color=ft.color;const freshBytes=await NS.PptxWriter.build(fresh),freshDecoded=await NS.PptxOpenController.decodePptx(freshBytes,'Fresh.pptx');
              return{afterShape,textState,imageState,receipt:built.receipt,slideXml,rels,media,decodedState,reopened:!!reopened,reopenedTypes,fresh:{types:freshDecoded.slides[0].objects.map(o=>o.type),texts:freshDecoded.slides[0].objects.filter(o=>o.type==='text').map(o=>o.text),shapes:freshDecoded.slides[0].objects.filter(o=>o.type==='shape').map(o=>({shapeType:o.shapeType,rotation:o.rotation,fill:o.fill})),images:freshDecoded.slides[0].objects.filter(o=>o.type==='image').length}};
            }""",PNG_B64)
            browser.close()
        a=result['afterShape'];b=setup['before']
        assert a['x']!=b['x'] or a['y']!=b['y'],{'setup':setup,'result':result}
        assert a['w']>b['w'] and a['h']>b['h'],{'setup':setup,'result':result}
        assert abs(a['rotation'])>1,{'setup':setup,'result':result}
        assert a['fill'].lower()=='#336699' and a['line']['color'].lower()=='#993333',result
        assert result['textState']['bullet']=='•' and result['textState']['color'].lower()=='#2244aa',result
        assert result['imageState']['line']['color'].lower()=='#117744',result
        assert result['receipt']['mode']=='package-preserving-pptx-home-editing',result
        assert result['media'] and '/image' in result['rels'],result
        assert 'buChar' in result['slideXml'] and '336699' in result['slideXml'] and '993333' in result['slideXml'],result
        ds=result['decodedState']
        assert 'shape' in ds['types'] and 'image' in ds['types'] and 'text' in ds['types'],result
        assert any(s['shapeType']=='ellipse' and (s['fill'] or '').lower()=='#336699' and abs(s['rotation'])>1 for s in ds['shapes']),result
        assert ds['images'],result
        assert any(t['text']=='Home bullet item' and t['bullet']=='•' and (t['color'] or '').lower()=='#2244aa' for t in ds['texts']),result
        assert result['reopened'] is True and 'shape' in result['reopenedTypes'] and 'image' in result['reopenedTypes'],result
        fresh=result['fresh']
        assert 'shape' in fresh['types'] and 'image' in fresh['types'],result
        assert fresh['images']==1 and any(s['shapeType']=='roundRect' and abs(s['rotation']-17)<.2 for s in fresh['shapes']),result
        assert 'Fresh bullet' in fresh['texts'],result
        print('PPT-P1 objects/geometry/styles/layouts imported + new PPTX roundtrip passed.')
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()

if __name__=='__main__':main()
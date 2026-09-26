import sys,json; sys.path.insert(0,sys.argv[1]); from fw import *
APPS={'documents':('audit.docx','#startOpen'),'spreadsheets':('audit.xlsx','#startOpen'),'presentations':('audit.pptx','#startOpen'),'txt':('audit.txt','#startOpen'),'epub':('audit.epub','#openStartBtn'),'pdf':('small.pdf','#openStartBtn')}
out={}
FAKE=r"""(args)=>{const [name,type,text]=args;window.showOpenFilePicker=async()=>[{kind:'file',name,getFile:async()=>new File([text],name,{type})}]}"""
VISERR=r"""()=>{const t=document.body.innerText;const m=[...document.querySelectorAll('.error-overlay,.backdrop,[role=dialog],[role=alertdialog],.confirm-dialog,.toast,[class*=toast],[class*=notice]')].filter(e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>0&&r.height>0&&c.display!=='none'&&c.visibility!=='hidden'}).map(e=>e.innerText.slice(0,120));return {overlays:m,unsupportedText:/unsupported|not supported|cannot open|could not/i.test(document.querySelector('.statusbar')?.innerText||'')}}"""
with sync_playwright() as pw:
  br=pw.chromium.launch()
  # 1+2: native picker with unsupported type, and launchQueue consume
  for app,(fx,openSel) in APPS.items():
    ctx=br.new_context(viewport={'width':1366,'height':900}); pg=ctx.new_page(); errs=[]; pg.on('console',lambda m,e=errs: m.type=='error' and e.append(m.text[:160]))
    pg.goto(B+f'apps/{app}/'); pg.wait_for_timeout(900)
    pg.evaluate(FAKE,['notes.zip','application/zip','PK garbage'])
    pg.click(openSel); pg.wait_for_timeout(1500); v=pg.evaluate(VISERR)
    out[f'{app}|picker-unsupported']={'visibleError':bool(v['overlays'] or v['unsupportedText']),'ui':v,'console':errs[-1:] }
    # launchQueue consume with valid file
    data=open(f'{FX}/{fx}','rb').read()
    ok=pg.evaluate("""async([name,bytes])=>{const f=new File([new Uint8Array(bytes)],name);const h={kind:'file',name,getFile:async()=>f};try{await InkDOSFileLaunch.consume({files:[h]});return true}catch(e){return String(e)}}""",[fx,list(data)])
    pg.wait_for_timeout(2500); title=pg.title()
    out[f'{app}|launchQueue-valid']={'consume':ok,'title':title,'loaded':(fx.split('.')[0] in title) or (app in('epub','pdf') and pg.evaluate("()=>!!document.querySelector('canvas,#readerSurface p')"))}
    errs.clear(); ok2=pg.evaluate("""async()=>{const f=new File(['x'],'bad.zip');const h={kind:'file',name:'bad.zip',getFile:async()=>f};try{await InkDOSFileLaunch.consume({files:[h]});return 'resolved'}catch(e){return 'threw:'+e.message}}"""); pg.wait_for_timeout(800); v=pg.evaluate(VISERR)
    out[f'{app}|launchQueue-unsupported']={'consume':ok2,'visibleError':bool(v['overlays'] or v['unsupportedText']),'ui':v,'console':errs[-1:]}
    ctx.close()
  print(json.dumps(out,indent=1)[:6000])
  json.dump(out,open(S+'/cross1.json','w'),indent=1)

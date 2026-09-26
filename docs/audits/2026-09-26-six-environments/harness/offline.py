import sys,json,time; sys.path.insert(0,sys.argv[1]); from fw import *
APPS={'documents':('audit.docx',"()=>document.querySelector('.page-content')?.innerText.includes('Audit Heading One')"),'spreadsheets':('audit.xlsx',"()=>document.querySelector('#gridStage .cell[data-ref=\"B1\"]')?.innerText==='Item 1'"),'presentations':('audit.pptx',"()=>document.body.innerText.includes('Slide 1 Title')"),'txt':('audit.txt',"()=>document.getElementById('editor').value.includes('Line two')"),'epub':('audit.epub',"()=>document.getElementById('readerSurface').innerText.includes('Chapter One')"),'pdf':('small.pdf',"()=>/\\/ 3/.test(document.getElementById('pageCount').innerText)")}
out={}
with sync_playwright() as pw:
  br=pw.chromium.launch()
  for entry in ['home-first','pdf-direct-first']:
    ctx=br.new_context(viewport={'width':1366,'height':900}); pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    t=time.time(); pg.goto(B if entry=='home-first' else B+'apps/pdf/'); 
    pg.evaluate("()=>navigator.serviceWorker.ready.then(()=>true)")
    n=0
    for i in range(120):
      n=pg.evaluate("async()=>{const ks=await caches.keys();let n=0;for(const k of ks){n+=(await (await caches.open(k)).keys()).length}return n}")
      if n>=500: break
      pg.wait_for_timeout(500)
    ctl=pg.evaluate("()=>!!navigator.serviceWorker.controller")
    out[entry]={'cachedEntries':n,'installSeconds':round(time.time()-t,1),'controllerBeforeReload':ctl}
    ctx.set_offline(True)
    for app,(fx,chk) in APPS.items():
      e0=len(errs)
      try:
        pg.goto(B+f'apps/{app}/',timeout=15000); pg.wait_for_timeout(1200)
        pg.set_input_files('#fileInput',f'{FX}/{fx}'); pg.wait_for_timeout(2500); ok=pg.evaluate(chk)
        extra=None
        if app=='pdf':
          pg.click('#editModeBtn'); pg.wait_for_timeout(1500); pg.click('#pageToolsBtn'); pg.wait_for_timeout(1500); extra={'pageToolsVisible':pg.locator('#pageDeleteBtn').is_visible()}
        if app=='txt':
          pg.click('#menuBtn'); pg.wait_for_timeout(300); pg.locator('[data-settings-item="language"],button:has-text("Language")').first.click(); pg.wait_for_timeout(500); extra={'languagePopover':pg.evaluate("()=>[...document.querySelectorAll('.inkdos-settings-option')].map(b=>b.innerText).slice(0,8)")}
        out[entry][app]={'loaded':ok,'errors':errs[e0:]} | ({'extra':extra} if extra else {})
      except Exception as e: out[entry][app]={'error':repr(e)[:200]}
    # Home offline
    try: pg.goto(B,timeout=15000); out[entry]['home']=pg.evaluate("()=>document.querySelectorAll('a.workspace-card').length")
    except Exception as e: out[entry]['home']=repr(e)[:120]
    ctx.close()
  print(json.dumps(out,indent=1)); json.dump(out,open(S+'/offline.json','w'),indent=1)

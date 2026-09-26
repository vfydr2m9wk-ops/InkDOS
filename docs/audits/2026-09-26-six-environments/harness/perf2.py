import sys,json,time,statistics; sys.path.insert(0,sys.argv[1]); from fw import *
LT=r"""(()=>{window.__lt=[];try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt.push([Math.round(e.startTime),Math.round(e.duration)])}).observe({type:'longtask',buffered:true})}catch(_){}})();"""
VIS={'documents':("audit.docx","audit.rtf","()=>document.querySelector('.page-content')?.innerText.includes('RTF audit line one')"),
 'spreadsheets':("audit.xlsx","sheet_saved.xlsx","()=>document.querySelector('#gridStage .cell[data-ref=\"D1\"]')?.innerText==='hello'"),
 'presentations':("audit.pptx","ppt_saved.pptx","()=>document.body.innerText.includes('EDITED')"),
 'txt':("audit.txt","note.md","()=>document.getElementById('editor').value.includes('# Title')"),
 'epub':("audit.epub","audit2.epub","()=>document.getElementById('readerSurface').innerText.includes('Other Start')"),
 'pdf':("small.pdf","second.pdf","()=>/Second PDF|second/i.test(document.getElementById('titleText').innerText)&&/\\/ 2/.test(document.getElementById('pageCount').innerText)")}
EDIT={'documents':lambda pg:(pg.locator('.page-content').click(),pg.keyboard.type('Z')),
 'spreadsheets':lambda pg:(pg.locator('#gridStage .cell[data-ref="F1"]').click(),pg.keyboard.type('z'),pg.keyboard.press('Enter')),
 'presentations':lambda pg:pg.click('#addSlideBtn'),'txt':lambda pg:(pg.click('#editor'),pg.keyboard.type('Z')),'epub':lambda pg:None,
 'pdf':lambda pg:(pg.click('#editModeBtn'),pg.wait_for_timeout(1200),pg.click('#penToolBtn'),pg.mouse.move(500,400),pg.mouse.down(),pg.mouse.move(600,450,steps=5),pg.mouse.up(),pg.wait_for_timeout(300))}
SAVE={'documents':lambda r:(r.menu(),r.pg.click('#saveMenuBtn'),r.pg.wait_for_selector('#deliverCopy'),r.pg.click('#deliverCopy')),
 'spreadsheets':lambda r:(r.menu(),r.pg.click('#menuSave')),'presentations':lambda r:(r.menu(),r.pg.click('#saveMenuBtn')),
 'txt':lambda r:(r.menu(),r.pg.click('#saveBtn')),'epub':lambda r:(r.menu(),r.pg.click('#saveBtn')),'pdf':lambda r:r.pg.click('#saveToolbarBtn')}
res={}
with sync_playwright() as pw:
  for app,(a,b,chk) in VIS.items():
    sw=[];sv=[]
    for i in range(3):
      r=Run(app,'fs'); r.start(pw); pg=r.pg
      r.open_via_input(a); pg.wait_for_timeout(1500)
      t=time.time(); r.open_via_input(b); pg.wait_for_function(chk,timeout=20000,polling='raf'); sw.append((time.time()-t)*1000)
      EDIT[app](pg); pg.wait_for_timeout(300)
      n=len(r.saved()); t=time.time(); SAVE[app](r)
      try: pg.wait_for_function(f"()=>window.__saved.length>{n}",timeout=20000,polling='raf'); sv.append((time.time()-t)*1000)
      except Exception as e: sv.append(None)
      r.ctx.close(); r.br.close()
    res[app]={'switchMs':round(statistics.median(sw)),'saveMs':round(statistics.median([x for x in sv if x] or [0])),'saveRuns':[round(x) if x else None for x in sv]}
    print(app,res[app],flush=True)
  # EPUB page turn latency
  r=Run('epub','nofs'); r.start(pw); pg=r.pg; r.open_via_input('large.epub'); pg.wait_for_timeout(2000); lat=[]
  for i in range(6):
    s0=pg.evaluate("()=>document.querySelector('.statusbar').innerText"); t=time.time(); pg.click('#nextBtn'); pg.wait_for_function("(s)=>document.querySelector('.statusbar').innerText!==s",arg=s0,timeout=5000,polling='raf'); lat.append((time.time()-t)*1000)
  res['epub_pageTurnMs']=[round(x) for x in lat]; print('epub page turn',res['epub_pageTurnMs']); r.ctx.close(); r.br.close()
  # TXT large typing latency
  r=Run('txt','nofs'); r.start(pw); pg=r.pg; pg.add_init_script(LT); r.open_via_input('large.txt'); pg.wait_for_function("()=>document.getElementById('editor').value.length>1e6",timeout=60000); pg.wait_for_timeout(1500)
  pg.evaluate("()=>{window.__lt=[];new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt.push(Math.round(e.duration))}).observe({type:'longtask'})}")
  pg.click('#editor'); lat=[]
  for ch in 'abcdef':
    t=time.time(); pg.keyboard.type(ch); pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>r()))"); lat.append((time.time()-t)*1000)
  pg.wait_for_timeout(1500); res['txt_large_keystrokeMs']=[round(x) for x in lat]; res['txt_large_longtasksAfterTyping']=pg.evaluate("()=>window.__lt"); print('txt typing',res['txt_large_keystrokeMs'],res['txt_large_longtasksAfterTyping'][:10]); r.ctx.close(); r.br.close()
  # Spreadsheet large scroll
  r=Run('spreadsheets','nofs'); r.start(pw); pg=r.pg; r.open_via_input('large.xlsx'); pg.wait_for_function("()=>document.querySelector('#gridStage .cell[data-ref=\"B1\"]')",timeout=60000); pg.wait_for_timeout(1500)
  pg.evaluate("()=>{window.__lt=[];new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt.push(Math.round(e.duration))}).observe({type:'longtask'})}")
  pg.mouse.move(700,500); t=time.time()
  for i in range(20): pg.mouse.wheel(0,1500); pg.wait_for_timeout(50)
  pg.wait_for_timeout(1000); res['sheet_large_scroll_longtasks']=pg.evaluate("()=>window.__lt"); res['sheet_large_nameBoxAfter']=pg.evaluate("()=>[...document.querySelectorAll('#gridStage .cell')].slice(0,1).map(c=>c.dataset.ref)")
  print('sheet scroll',res['sheet_large_scroll_longtasks'][:15],res['sheet_large_nameBoxAfter']); r.ctx.close(); r.br.close()
json.dump(res,open(S+'/perf2.json','w'),indent=1)

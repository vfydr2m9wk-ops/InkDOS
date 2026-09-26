import sys,json; sys.path.insert(0,sys.argv[1]); from fw import *
APPS={'documents':'audit.docx','spreadsheets':'audit.xlsx','presentations':'audit.pptx','txt':'audit.txt','epub':'audit.epub','pdf':'small.pdf'}
DIRTY={'documents':lambda pg:(pg.locator('.page-content').click(),pg.keyboard.type('Z')),
 'spreadsheets':lambda pg:(pg.locator('#gridStage .cell[data-ref="F1"]').click(),pg.keyboard.type('z'),pg.keyboard.press('Enter')),
 'presentations':lambda pg:pg.click('#addSlideBtn'),
 'txt':lambda pg:(pg.click('#editor'),pg.keyboard.type('Z')),
 'epub':lambda pg:None,
 'pdf':lambda pg:(pg.click('#editModeBtn'),pg.wait_for_timeout(1200),pg.click('#penToolBtn'),pg.mouse.move(500,400),pg.mouse.down(),pg.mouse.move(600,450,steps=5),pg.mouse.up())}
out={}
with sync_playwright() as pw:
  br=pw.chromium.launch()
  for app,fx in APPS.items():
    ctx=br.new_context(viewport={'width':1366,'height':900}); pg=ctx.new_page(); dl=[]; pg.on('dialog',lambda d,dl=dl:(dl.append(d.type+':'+d.message[:60]),d.dismiss()))
    pg.goto(B); pg.click(f'a.workspace-card.{app}'); pg.wait_for_load_state('load'); pg.wait_for_timeout(900)
    pg.set_input_files('#fileInput',f'{FX}/{fx}'); pg.wait_for_timeout(2200)
    DIRTY[app](pg); pg.wait_for_timeout(500)
    home=pg.locator('a[aria-label="Home"]:visible').first
    url0=pg.url; home.click(); pg.wait_for_timeout(1200)
    r={'afterHomeClickUrl':pg.url.replace(B,''),'stayed':pg.url==url0,'nativeDialogs':list(dl)}
    m=pg.evaluate("()=>{const d=[...document.querySelectorAll('.error-overlay,.backdrop,[role=dialog],.confirm-dialog')].find(e=>e.getBoundingClientRect().height>0&&getComputedStyle(e).display!=='none'&&/unsaved|leave|discard/i.test(e.innerText));return d?d.innerText.replace(/\\s+/g,' ').slice(0,120):null}")
    r['leaveGuard']=m
    # choose discard if present, go home, re-enter
    if m:
      pg.get_by_role('button',name=re.compile('^Discard',re.I)).last.click(force=True); pg.wait_for_timeout(1500); r['afterDiscardUrl']=pg.url.replace(B,'')
    if 'apps/' in pg.url and not m and app!='epub': pass
    if pg.url.rstrip('/').endswith('InkDOS') or 'index.html' in pg.url and 'apps/' not in pg.url:
      pg.click(f'a.workspace-card.{app}'); pg.wait_for_load_state('load'); pg.wait_for_timeout(1200)
      r['reentry']={'title':pg.title(),'startVisible':pg.evaluate("()=>{const s=document.getElementById('startState')||document.querySelector('.start-state,[class*=start]');return !!s&&s.getBoundingClientRect().height>0&&!s.hidden}")}
    out[app]=r; ctx.close()
  # theme propagation
  ctx=br.new_context(viewport={'width':1366,'height':900},color_scheme='light'); pg=ctx.new_page(); pg.goto(B); pg.click('#appearanceButton'); pg.click('[data-home-appearance-mode="dark"]'); pg.wait_for_timeout(300)
  th={}
  for app in APPS:
    pg.goto(B); pg.click(f'a.workspace-card.{app}'); pg.wait_for_load_state('load'); pg.wait_for_timeout(600); th[app+'-first']=pg.evaluate("()=>document.documentElement.dataset.appearanceResolved")
  pg.goto(B); pg.click('#appearanceButton'); pg.click('[data-home-appearance-mode="light"]'); pg.wait_for_timeout(300)
  for app in APPS:
    pg.goto(B); pg.click(f'a.workspace-card.{app}'); pg.wait_for_load_state('load'); pg.wait_for_timeout(600); th[app+'-afterHomeLight']=pg.evaluate("()=>document.documentElement.dataset.appearanceResolved")
  out['theme']=th; ctx.close()
  json.dump(out,open(S+'/cross2.json','w'),indent=1); print(json.dumps(out,indent=1))

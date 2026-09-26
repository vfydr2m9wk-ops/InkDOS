import sys,io,shutil
sys.path.insert(0,sys.argv[1]); from fw import *
import pypdf
ST="()=>document.querySelector('.statusbar')?.innerText.replace(/\\s+/g,' ')"
TT="()=>document.getElementById('titleText').innerText"
PAGE="()=>document.getElementById('pageInput').value+'/'+document.getElementById('pageCount').innerText"
def run(profile):
  r=Run('pdf',profile); print('#### pdf',profile)
  with sync_playwright() as pw:
    r.start(pw); pg=r.pg
    pg.evaluate("()=>{window.__prints=0;window.print=()=>{window.__prints++}}")
    ok=r.open_via_chooser('#openStartBtn','small.pdf'); pg.wait_for_timeout(2500)
    r.rec('open PDF via start Open + picker','PASS' if ok and '/ 3' in pg.evaluate(PAGE) else 'FAIL',f'{pg.evaluate(PAGE)} {pg.evaluate(ST)} title={r.title()}')
    pg.click('#nextPageBtn'); pg.wait_for_timeout(700); a=pg.evaluate(PAGE); pg.click('#prevPageBtn'); pg.wait_for_timeout(700); b=pg.evaluate(PAGE)
    r.rec('next/previous page','PASS' if a.startswith('2/') and b.startswith('1/') else 'FAIL',(a,b))
    pg.fill('#pageInput','3'); pg.press('#pageInput','Enter'); pg.wait_for_timeout(800); c=pg.evaluate(PAGE); r.rec('go to page via page input','PASS' if c.startswith('3/') else 'FAIL',c)
    pg.fill('#pageInput','99'); pg.press('#pageInput','Enter'); pg.wait_for_timeout(500); c2=pg.evaluate(PAGE); r.rec('out-of-range page input clamps/rejects','PASS' if c2.startswith('3/') else 'WARNING',c2)
    w0=pg.evaluate("()=>document.querySelector('.pdf-page-host.is-current .pdf-page-shell')?.getBoundingClientRect().width"); pg.select_option('#zoomSelect','200'); pg.wait_for_timeout(1200); w1=pg.evaluate("()=>document.querySelector('.pdf-page-host.is-current .pdf-page-shell')?.getBoundingClientRect().width")
    r.rec('zoom 200%','PASS' if w1 and w0 and abs(w1-w0)>10 else 'FAIL',(w0,w1)); pg.select_option('#zoomSelect','fit-width'); pg.wait_for_timeout(800)
    pg.click('#pdfRotateViewBtn'); pg.wait_for_timeout(1000); rot=pg.evaluate("()=>{const p=document.querySelector('.pdf-page-shell');const r=p.getBoundingClientRect();return r.width>r.height}"); pg.click('#pdfRotateViewBtn'); pg.click('#pdfRotateViewBtn'); pg.click('#pdfRotateViewBtn'); pg.wait_for_timeout(800)
    r.rec('rotate view (landscape after 90°)','PASS' if rot else 'FAIL',rot)
    pg.click('#navPanelBtn'); pg.wait_for_timeout(500); tab=pg.evaluate("()=>document.querySelector('#outlineTab')?.getAttribute('aria-selected')")
    r.rec('navigation panel default tab when PDF has no outline','WARNING' if tab=='true' else 'PASS',f'outline selected={tab} (shows "No document outline")')
    pg.click('#pagesTab'); pg.wait_for_timeout(1500); th=pg.evaluate("()=>[...document.querySelectorAll('.thumb, [class*=thumb] canvas, [class*=thumbnail] img, [class*=thumbnail] canvas, [data-thumb-page]')].filter(e=>e.getBoundingClientRect().width>0).length")
    r.rec('thumbnails rendered','PASS' if th>=3 else 'FAIL',th); r.shot('thumbs')
    t2=pg.locator('[data-page],[data-thumb-page],[class*=thumb]').filter(has_text='2').first
    try: t2.click(); pg.wait_for_timeout(800); r.rec('click thumbnail 2 navigates','PASS' if pg.evaluate(PAGE).startswith('2/') else 'FAIL',pg.evaluate(PAGE))
    except Exception as e: r.rec('click thumbnail','FAIL',repr(e)[:120])
    try: pg.click('#closeNavigation',timeout=1500)
    except Exception: pg.keyboard.press('Escape')
    pg.click('#pdfSearchBtn'); pg.wait_for_timeout(500); si=pg.locator('input[type=search]:visible,#pdfSearchInput:visible,input[placeholder*=ind]:visible').first
    try: si.fill('Line 7 of page 3'); si.press('Enter'); pg.wait_for_timeout(1500); r.rec('find text navigates to match','PASS' if pg.evaluate(PAGE).startswith('3/') else 'FAIL',f'{pg.evaluate(PAGE)} {pg.evaluate(ST)}')
    except Exception as e: r.rec('find text','FAIL',repr(e)[:150])
    pg.keyboard.press('Escape'); r.clear()
    pg.click('#pdfPrintBtn'); pg.wait_for_timeout(1500); m=r.modal(); pr=pg.evaluate("()=>window.__prints")
    r.rec('Print triggers print path','PASS' if pr or m else 'WARNING',f'window.print calls={pr} modal={m and m["text"][:80]}'); r.clear()
    # edit mode
    t=time.time(); pg.click('#editModeBtn'); pg.wait_for_function("()=>!document.getElementById('undoBtn').closest('[hidden]')&&document.getElementById('textToolBtn').getBoundingClientRect().width>0",timeout=15000); te=time.time()-t
    r.rec('enter Edit mode','PASS',f'{te:.2f}s')
    pg.fill('#pageInput','1'); pg.press('#pageInput','Enter'); pg.wait_for_timeout(600)
    pg.click('#penToolBtn'); page1=pg.locator('.pdf-page-shell').first; bb=page1.bounding_box()
    pg.mouse.move(bb['x']+200,bb['y']+200); pg.mouse.down(); pg.mouse.move(bb['x']+300,bb['y']+260,steps=8); pg.mouse.move(bb['x']+380,bb['y']+220,steps=8); pg.mouse.up(); pg.wait_for_timeout(800)
    r.rec('Pen stroke → dirty + Undo enabled','PASS' if r.dirty() and not pg.locator('#undoBtn').is_disabled() else 'FAIL',f'dirty={r.dirty()} undoDisabled={pg.locator("#undoBtn").is_disabled()}')
    pg.click('#undoBtn'); pg.wait_for_timeout(500); u=pg.locator('#redoBtn').is_disabled(); pg.click('#redoBtn'); pg.wait_for_timeout(500)
    r.rec('annotation Undo/Redo','PASS' if not u else 'FAIL',f'redo enabled after undo={not u}')
    pg.click('#textToolBtn'); pg.mouse.click(bb['x']+150,bb['y']+500); pg.wait_for_timeout(500); pg.keyboard.type('AUDIT NOTE'); pg.wait_for_timeout(300); pg.mouse.click(bb['x']+600,bb['y']+700); pg.wait_for_timeout(500)
    r.rec('Text annotation typed','INFO',pg.evaluate("()=>[...document.querySelectorAll('.annotationEditorLayer [contenteditable], .freeTextEditor, [class*=freeText]')].map(e=>e.innerText).join('|').slice(0,60)"))
    # page tools
    pg.click('#pageToolsBtn'); pg.wait_for_timeout(1500)
    pg.click('#pageRotateBtn'); pg.wait_for_timeout(1500); m=r.modal()
    if m: r.rec('rotate page confirmation','INFO',m['text'][:120]); r.click_modal(r'rotate|apply|ok|continue|confirm')
    pg.wait_for_timeout(800); r.rec('Page Tools: rotate page','INFO',f'{pg.evaluate(ST)} dirty={r.dirty()}')
    pg.fill('#pageInput','3'); pg.press('#pageInput','Enter'); pg.wait_for_timeout(600)
    r.rec('Page Tools panel stays open after an operation','INFO',pg.locator('#pageDeleteBtn').is_visible())
    if not pg.locator('#pageDeleteBtn').is_visible(): pg.click('#pageToolsBtn'); pg.wait_for_timeout(1000)
    nd=len(r.dialogs); r.dialog_policy='dismiss'; pg.click('#pageDeleteBtn'); pg.wait_for_timeout(800); m=r.modal(); c=[d['type']+':'+d['msg'][:50] for d in r.dialogs[nd:]]; pg.wait_for_timeout(500)
    r.rec('Page Tools: Delete page → Cancel keeps page','PASS' if '/ 3' in pg.evaluate(PAGE) else 'FAIL',f'modal={m and m["text"][:100]} cancel={c} {pg.evaluate(PAGE)}')
    if not pg.locator('#pageDeleteBtn').is_visible(): pg.click('#pageToolsBtn'); pg.wait_for_timeout(1000)
    r.dialog_policy='accept'; pg.click('#pageDeleteBtn'); pg.wait_for_timeout(1500); r.dialog_policy='dismiss'; m=r.modal()
    if m: r.click_modal(r'delete|ok|confirm|continue')
    pg.wait_for_timeout(2000); r.rec('Page Tools: Delete page → confirm','PASS' if '/ 2' in pg.evaluate(PAGE) else 'FAIL',f'{pg.evaluate(PAGE)} {pg.evaluate(ST)}')
    try: pg.click('#closePageTools',timeout=1500)
    except Exception: pass
    r.clear()
    def do_save():
      pg.click('#saveToolbarBtn'); pg.wait_for_timeout(1500); m=r.modal()
      if m and not re.search('could not|fail',m['text'],re.I): r.click_modal(r'save|copy|continue'); pg.wait_for_timeout(2000)
    if profile=='fs':
      r.setmode('abort'); do_save(); r.rec('Save → picker cancelled keeps dirty','PASS' if r.dirty() and not r.saved() else 'FAIL',f'dirty={r.dirty()} {pg.evaluate(ST)}'); r.clear()
      r.setmode('writefail'); do_save(); m=r.modal(); r.rec('Save → write error surfaced, stays dirty','PASS' if r.dirty() and ((m and re.search('could not|fail|error',m['text'],re.I)) or re.search('could not|fail|error',pg.evaluate(ST) or '',re.I)) else 'FAIL',f'modal={m and m["text"][:160]} status={pg.evaluate(ST)}'); r.shot('writefail'); r.clear()
      r.setmode('ok'); t=time.time(); do_save(); sv=r.saved()
      if sv:
        data=r.saved_bytes(); open(f'{FX}/pdf_saved.pdf','wb').write(data)
        try:
          R=pypdf.PdfReader(io.BytesIO(data)); ann=sum(len(p.get('/Annots') or []) for p in R.pages); rot=[p.get('/Rotate',0) for p in R.pages]
          r.rec('Save copy → valid PDF, pages/rotation/annotations kept','PASS' if len(R.pages)==2 and ann>=1 and rot[0]==90 else 'FAIL',f'pages={len(R.pages)} annots={ann} rotate={rot} name={sv[-1]["name"]} {sv[-1]["size"]}B')
        except Exception as e: r.rec('Saved PDF parses','FAIL',repr(e)[:200])
      else: r.rec('Save copy → written','FAIL',f'{pg.evaluate(ST)}')
      r.rec('dirty cleared after save','PASS' if not r.dirty() else 'WARNING',r.dirty()); r.clear()
    else:
      do_save(); pg.wait_for_timeout(800); r.rec('Save (no FS API) → download fallback','PASS' if r.downloads else 'FAIL',[d['name'] for d in r.downloads]); r.clear()
    r.menu(); sh=pg.locator('#generalMenu button',has_text='Share').first; r.rec('Share availability (desktop Chromium, no Web Share files)','INFO',f'disabled={sh.is_disabled()}'); pg.keyboard.press('Escape'); r.clear()
    # dirty guard
    pg.click('#penToolBtn'); pg.mouse.move(bb['x']+220,bb['y']+300); pg.mouse.down(); pg.mouse.move(bb['x']+320,bb['y']+340,steps=6); pg.mouse.up(); pg.wait_for_timeout(500)
    r.menu(); pg.click('#openMenuBtn'); pg.wait_for_timeout(600); m=r.modal(); r.rec('Open while dirty → guard','PASS' if m else 'FAIL',m and m['text'][:160])
    if m:
      r.click_modal(r'^cancel'); r.rec('Guard → Cancel keeps PDF','PASS' if r.dirty() else 'FAIL',r.dirty())
      r.menu()
      try:
        with pg.expect_file_chooser(timeout=4000) as fc:
          pg.click('#openMenuBtn'); pg.wait_for_timeout(500); r.click_modal(r'^discard|don')
        fc.value.set_files(f'{FX}/second.pdf'); pg.wait_for_timeout(2500); m=r.modal()
        if m: r.rec('modal after 2nd PDF chosen','INFO',m['text'][:150]); r.clear()
        r.rec('Guard → Discard → open another PDF','PASS' if '/ 2' in pg.evaluate(PAGE) and 'second' in pg.evaluate(TT).lower() else 'FAIL',pg.evaluate(PAGE)+' '+pg.evaluate(TT))
      except Exception as e: r.rec('Guard → Discard → open another PDF','FAIL',repr(e)[:200])
    r.rec('PDF app is still in Edit mode after replacing document?','INFO',pg.locator('#editModeBtn').get_attribute('aria-pressed'))
    # large
    t=time.time(); r.open_via_input('large.pdf'); pg.wait_for_function("()=>/\\/ 400/.test(document.getElementById('pageCount').innerText)",timeout=30000); r.rec('open large PDF (400 pages, 7.5 MB)','PASS',f'{time.time()-t:.2f}s to page count')
    pg.fill('#pageInput','350'); pg.press('#pageInput','Enter'); pg.wait_for_timeout(2500); r.rec('jump to page 350 of large PDF','PASS' if pg.evaluate(PAGE).startswith('350/') else 'FAIL',pg.evaluate(PAGE)); r.shot('large350')
    for bad in ['invalid.pdf','empty.pdf','wrongext.pdf']:
      r.open_via_input(bad); pg.wait_for_timeout(2000); m=r.modal()
      if m and re.search('unsaved|discard',m['text'],re.I): r.click_modal(r'^discard'); pg.wait_for_timeout(1500); m=r.modal()
      r.rec(f'Open {bad} → error, previous PDF kept','PASS' if ((m and re.search('could not|invalid|error|not|empty',m['text'],re.I)) or re.search('could not|invalid|failed|empty',pg.evaluate(ST) or '',re.I)) and '/ 400' in pg.evaluate(PAGE) else 'FAIL',f'modal={m and m["text"][:160]} status={pg.evaluate(ST)} {pg.evaluate(PAGE)}'); r.clear()
    r.finish()
for prof in sys.argv[2:]: run(prof)

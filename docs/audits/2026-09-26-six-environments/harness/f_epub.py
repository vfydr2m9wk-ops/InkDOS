import sys,shutil,zipfile,io
sys.path.insert(0,sys.argv[1]); from fw import *
ST="()=>document.querySelector('.statusbar')?.innerText.replace(/\\s+/g,' ')"
TX="()=>document.getElementById('readerSurface')?.innerText||''"
VIS="()=>{const s=document.getElementById('readerStage')||document.getElementById('readerSurface');const r=s.getBoundingClientRect();const pts=[];for(const y of [0.2,0.4,0.6]){const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height*y);pts.push(e?e.innerText?.slice(0,30):null)}return pts.join('|')}"
def run(profile):
  r=Run('epub',profile); print('#### epub',profile)
  with sync_playwright() as pw:
    r.start(pw); pg=r.pg
    ok=r.open_via_chooser('#openStartBtn','audit.epub'); pg.wait_for_timeout(2000)
    r.rec('open EPUB via start Open + picker','PASS' if ok and 'Chapter One' in pg.evaluate(TX) else 'FAIL',f'{ok} status={pg.evaluate(ST)} title={r.title()}')
    s0=pg.evaluate(ST); v0=pg.evaluate(VIS); pg.click('#nextBtn'); pg.wait_for_timeout(1500); s1=pg.evaluate(ST); v1=pg.evaluate(VIS)
    r.rec('Next page (paginated) changes visible content/position','PASS' if (s0!=s1 and v0!=v1) else 'FAIL',f'{s0} -> {s1} | {v0} -> {v1}')
    pg.click('#prevBtn'); pg.wait_for_timeout(1500); s2=pg.evaluate(ST); r.rec('Previous page returns','PASS' if s2==s0 else 'WARNING',f'{s2}')
    pg.locator('#readerStage').click(position={'x':50,'y':300}); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(1500); s3=pg.evaluate(ST); r.rec('keyboard ArrowRight pages','PASS' if s3!=s0 else 'WARNING',s3); pg.keyboard.press('ArrowLeft')
    pg.click('#tocBtn'); pg.wait_for_timeout(400); toc=pg.evaluate("()=>[...document.querySelectorAll('#tocList a,#tocList button,#tocList li')].map(e=>e.innerText.trim()).filter(Boolean)")
    r.rec('Table of contents lists chapters','PASS' if any('Chapter Two' in t for t in toc) else 'FAIL',toc[:6])
    pg.locator('#tocList').get_by_text('Chapter Three').first.click(); pg.wait_for_timeout(900)
    r.rec('TOC jump to chapter','PASS' if 'Chapter Three' in pg.evaluate(VIS) or 'Gamma' in pg.evaluate(VIS) else 'FAIL',f'{pg.evaluate(VIS)} {pg.evaluate(ST)}')
    try: pg.click('#tocClose',timeout=1000)
    except Exception: pg.keyboard.press('Escape')
    pg.click('#searchBtn'); pg.wait_for_timeout(300); si=pg.locator('input[type=search]:visible, #searchInput:visible').first
    try:
      si.fill('Beta paragraph 3'); si.press('Enter'); pg.wait_for_timeout(800); res=pg.evaluate("()=>document.getElementById('searchResults')?.innerText.slice(0,120)")
      r.rec('Search in book','PASS' if res and 'Beta' in res else 'FAIL',res)
    except Exception as e: r.rec('Search in book','FAIL',repr(e)[:150])
    pg.keyboard.press('Escape'); r.clear()
    pg.click('#appearanceBtn'); pg.wait_for_timeout(300); f0=pg.locator('#fontValue').input_value(); pg.click('#fontUp'); pg.wait_for_timeout(400); f1=pg.locator('#fontValue').input_value()
    r.rec('reader font size (zoom) +','PASS' if f0!=f1 else 'FAIL',(f0,f1)); pg.click('#fontDown')
    try: pg.click('#appearanceClose',timeout=1000)
    except Exception: pg.keyboard.press('Escape')
    pg.click('#scrollBtn'); pg.wait_for_timeout(600); mode=pg.evaluate("()=>document.documentElement.dataset.readingMode||document.body.dataset.mode||document.getElementById('readerStage')?.className"); pg.mouse.wheel(0,800); pg.wait_for_timeout(300)
    r.rec('switch to Scroll mode','PASS' if pg.locator('#scrollBtn').get_attribute('aria-pressed') in ('true',None) else 'WARNING',f'{mode} pressed={pg.locator("#scrollBtn").get_attribute("aria-pressed")}')
    pg.click('#pagesBtn'); pg.wait_for_timeout(500)
    pg.click('#bookmarkBtn'); pg.wait_for_timeout(400); r.rec('Add bookmark','PASS' if pg.locator('#bookmarkBtn').get_attribute('aria-pressed')=='true' or 'bookmark' in (pg.evaluate(ST) or '').lower() else 'WARNING',f'{pg.locator("#bookmarkBtn").get_attribute("aria-pressed")} {pg.evaluate(ST)}')
    pr=pg.locator('#progressRange'); mx=pr.get_attribute('max'); pr.evaluate("(e)=>{e.value=e.max;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}"); pg.wait_for_timeout(700)
    r.rec('progress slider jumps to end','PASS' if 'Gamma' in pg.evaluate(VIS) or 'Chapter 3' in (pg.evaluate(ST) or '') else 'WARNING',f'max={mx} {pg.evaluate(ST)}')
    # highlight
    pg.click('#highlightBtn'); pg.wait_for_timeout(300); p=pg.locator('#readerSurface p').filter(has_text='paragraph').first
    try:
      bb=p.bounding_box(); pg.mouse.move(bb['x']+5,bb['y']+bb['height']/2); pg.mouse.down(); pg.mouse.move(bb['x']+120,bb['y']+bb['height']/2); pg.mouse.up(); pg.wait_for_timeout(600)
      hl=pg.evaluate("()=>document.querySelectorAll('#readerSurface mark,[class*=highlight]').length"); r.rec('Highlight mode: drag creates highlight','PASS' if hl else 'WARNING',f'marks={hl} status={pg.evaluate(ST)}')
    except Exception as e: r.rec('Highlight mode','WARNING',repr(e)[:150])
    pg.click('#highlightBtn'); r.clear()
    # save copy (annotations) + share
    r.menu(); sd=pg.locator('#saveBtn').is_disabled(); shd=pg.locator('#shareBtn').is_disabled(); r.rec('Save copy/Share enabled with book open','INFO',f'save disabled={sd} share disabled={shd}')
    if not sd:
      if profile=='fs':
        pg.click('#saveBtn'); pg.wait_for_timeout(1500); m=r.modal()
        if m and not re.search('could not',m['text'],re.I): r.click_modal(r'save|copy|continue'); pg.wait_for_timeout(1200)
        sv=r.saved()
        if sv:
          z=zipfile.ZipFile(io.BytesIO(r.saved_bytes())); names=z.namelist(); r.rec('Save copy → valid EPUB zip (mimetype first, stored)','PASS' if names[0]=='mimetype' and z.getinfo('mimetype').compress_type==0 and z.testzip() is None else 'FAIL',f'{sv[-1]} first={names[0]} n={len(names)}')
        else: r.rec('Save copy → EPUB written','FAIL',f'modal={m}')
      else:
        pg.click('#saveBtn'); pg.wait_for_timeout(1500); r.clear(); r.rec('Save copy (no FS API) → download','PASS' if r.downloads else 'FAIL',[d['name'] for d in r.downloads])
    else: pg.keyboard.press('Escape')
    r.clear()
    # open another EPUB
    r.menu(); ok=r.open_via_chooser('#openBtn','audit2.epub'); pg.wait_for_timeout(2000); m=r.modal()
    if m: r.rec('modal on 2nd open','INFO',m['text'][:150]); r.click_modal(r'discard|continue|open')
    r.rec('Open a second EPUB replaces book','PASS' if 'Other Start' in pg.evaluate(TX) and 'Chapter One' not in pg.evaluate(TX) else 'FAIL',f'{r.title()} {pg.evaluate(ST)}')
    pg.click('#tocBtn'); pg.wait_for_timeout(300); toc=pg.evaluate("()=>[...document.querySelectorAll('#tocList a,#tocList button,#tocList li')].map(e=>e.innerText.trim()).filter(Boolean)")
    r.rec('TOC updated for second book','PASS' if any('Other End' in t for t in toc) and not any('Chapter Two' in t for t in toc) else 'FAIL',toc[:5])
    try: pg.click('#tocClose',timeout=1000)
    except Exception: pg.keyboard.press('Escape')
    # reopen first: reading position remembered?
    r.open_via_input('audit.epub'); pg.wait_for_timeout(2000); r.clear()
    r.rec('reopen first EPUB restores reading position','INFO',f'{pg.evaluate(ST)} visible={pg.evaluate(VIS)[:60]}')
    for bad in ['invalid.epub']:
      r.open_via_input(bad); pg.wait_for_timeout(1500); m=r.modal(); body=pg.evaluate("()=>document.body.innerText")
      r.rec('Open invalid.epub → error, current book kept','PASS' if (m and re.search('could not|invalid|error|not',m['text'],re.I) or re.search('could not|invalid|not a valid',pg.evaluate(ST) or '',re.I)) and 'Chapter One' in pg.evaluate(TX) else 'FAIL',f'modal={m and m["text"][:160]} status={pg.evaluate(ST)}'); r.clear()
    shutil.copy(f'{FX}/empty.txt',f'{FX}/empty.epub'); r.open_via_input('empty.epub'); pg.wait_for_timeout(1500); m=r.modal()
    r.rec('Open empty.epub → error','PASS' if (m and re.search('could not|invalid|error|empty|not',m['text'],re.I)) or re.search('could not|empty|invalid',pg.evaluate(ST) or '',re.I) else 'FAIL',f'modal={m and m["text"][:160]} status={pg.evaluate(ST)}'); r.clear()
    r.rec('beforeunload guard (reader, no unsaved doc)','INFO','guard fired' if r.before_unload_guard() else 'no guard (expected for reader)')
    r.finish()
for prof in sys.argv[2:]: run(prof)

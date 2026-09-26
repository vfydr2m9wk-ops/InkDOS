import sys,shutil
sys.path.insert(0,sys.argv[1]); from fw import *
STATUS="()=>document.querySelector('.statusbar')?.innerText"
def ed(pg): return pg.evaluate("()=>{const e=document.getElementById('editor');return e.value!==undefined?e.value:e.innerText}")
def run(profile):
  r=Run('txt',profile); print('#### txt',profile)
  with sync_playwright() as pw:
    r.start(pw); pg=r.pg
    ok=r.open_via_chooser('#startOpen','audit.txt'); pg.wait_for_timeout(1200)
    r.rec('open TXT via start Open + picker','PASS' if ok and 'ümlaut and 中文' in ed(pg) else 'FAIL',f'{ok} {ed(pg)[:60]!r}')
    r.rec('dirty after open','PASS' if r.dirty() is False else 'FAIL',r.dirty())
    pg.click('#editor'); pg.keyboard.press('Control+End'); pg.keyboard.type('Added line'); pg.wait_for_timeout(300)
    r.rec('type text','PASS' if ed(pg).rstrip().endswith('Added line') else 'FAIL',repr(ed(pg)[-30:]))
    r.rec('dirty after edit','PASS' if r.dirty() else 'FAIL',r.dirty())
    pg.click('#undoBtn'); pg.wait_for_timeout(300); u=ed(pg); pg.click('#redoBtn'); pg.wait_for_timeout(300); rd=ed(pg)
    r.rec('Undo / Redo','PASS' if 'Added line' not in u and 'Added line' in rd else 'FAIL',f'undo={u[-20:]!r} redo={rd[-20:]!r}')
    pg.click('#selectAllBtn'); pg.wait_for_timeout(200); sl=pg.evaluate("()=>{const e=document.getElementById('editor');return e.selectionEnd!==undefined?e.selectionEnd-e.selectionStart:String(getSelection()).length}")
    r.rec('Select all','PASS' if sl>=len(ed(pg))-2 else 'FAIL',sl)
    fs0=pg.locator('#fontSize').input_value(); pg.click('#fontUpBtn'); pg.wait_for_timeout(200); fs1=pg.locator('#fontSize').input_value(); pg.click('#fontDownBtn'); fs2=pg.locator('#fontSize').input_value()
    r.rec('editor text size +/-','PASS' if fs1!=fs0 and fs2==fs0 else 'FAIL',(fs0,fs1,fs2))
    w0=pg.evaluate("()=>getComputedStyle(document.getElementById('editor')).whiteSpace"); pg.click('#wrapBtn'); pg.wait_for_timeout(200); w1=pg.evaluate("()=>getComputedStyle(document.getElementById('editor')).whiteSpace"); pg.click('#wrapBtn')
    r.rec('wrap toggle changes wrapping','PASS' if w0!=w1 else 'FAIL',(w0,w1))
    pg.click('#findBtn'); pg.wait_for_timeout(300); vis=pg.locator('#findInput').is_visible()
    if vis: pg.fill('#findInput','two'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    fsel=pg.evaluate("()=>{const e=document.getElementById('editor');return e.value!==undefined?e.value.slice(e.selectionStart,e.selectionEnd):String(getSelection())}")
    r.rec('Find locates text','PASS' if vis and fsel=='two' else 'FAIL',f'visible={vis} selected={fsel!r}'); pg.keyboard.press('Escape')
    try: pg.click('#findClose',timeout=1500)
    except Exception: pass
    pg.click('#textToolsBtn'); pg.wait_for_timeout(300); r.shot('texttools'); tt=pg.evaluate("()=>[...document.querySelectorAll('[role=menu] button,[class*=popover] button,[class*=menu] button')].filter(b=>b.getBoundingClientRect().width>0).map(b=>b.innerText.trim()).filter(Boolean).slice(0,15)")
    r.rec('Text tools menu opens','PASS' if tt else 'FAIL',tt); pg.keyboard.press('Escape'); r.clear()
    def do_save():
      r.menu(); pg.click('#saveBtn'); pg.wait_for_timeout(900); m=r.modal()
      if m and re.search('save|copy',m['text'],re.I) and not re.search('could not|fail',m['text'],re.I): r.click_modal(r'save|copy|continue'); pg.wait_for_timeout(900)
    if profile=='fs':
      r.setmode('abort'); do_save(); r.rec('Save → picker cancelled keeps dirty','PASS' if r.dirty() and not r.saved() else 'FAIL',r.dirty()); r.clear()
      r.setmode('writefail'); do_save(); m=r.modal(); st=pg.evaluate("()=>document.querySelector('.statusbar')?.innerText")
      r.rec('Save → write error surfaced, stays dirty','PASS' if r.dirty() and ((m and re.search('could not|fail|error',m['text'],re.I)) or re.search('could not|fail|error',st or '',re.I)) else 'FAIL',f'modal={m and m["text"][:160]} status={st}'); r.shot('writefail'); r.clear()
      r.setmode('ok'); do_save(); sv=r.saved()
      if sv:
        data=r.saved_bytes(); t=data.decode('utf-8'); r.rec('Save → UTF-8 bytes, LF, edit preserved','PASS' if 'Added line' in t and '中文' in t and '\r\n' not in t else 'FAIL',repr(t[-50:])+f' {len(data)}B name={sv[-1]["name"]}')
        open(f'{FX}/txt_saved.txt','wb').write(data)
      else: r.rec('Save → written','FAIL',sv)
      r.rec('dirty cleared after save','PASS' if not r.dirty() else 'WARNING',r.dirty())
    else:
      do_save(); pg.wait_for_timeout(800); r.rec('Save (no FS API) → download/share fallback','PASS' if r.downloads else 'FAIL',[d['name'] for d in r.downloads]); m=r.modal(); r.rec('post-save','INFO',f'dirty={r.dirty()} modal={m and m["text"][:120]}'); r.clear()
    # dirty guard
    pg.click('#editor'); pg.keyboard.type('Q'); pg.wait_for_timeout(200)
    r.menu(); pg.click('#openBtn'); pg.wait_for_timeout(500); m=r.modal(); r.rec('Open while dirty → guard','PASS' if m else 'FAIL',m and m['text'][:160])
    if m:
      r.click_modal(r'^cancel'); r.rec('Guard → Cancel keeps text','PASS' if 'Q' in ed(pg) and r.dirty() else 'FAIL',r.dirty())
      r.menu()
      try:
        with pg.expect_file_chooser(timeout=4000) as fc:
          pg.click('#openBtn'); pg.wait_for_timeout(400); r.click_modal(r'discard|continue|don')
        fc.value.set_files(f'{FX}/note.md'); pg.wait_for_timeout(1200)
        r.rec('Guard → Discard → open .md','PASS' if '# Title' in ed(pg) else 'FAIL',f'{ed(pg)[:30]!r} title={r.title()}')
      except Exception as e: r.rec('Guard → Discard → open .md','FAIL',repr(e)[:200])
    for f,expect in [('data.json','"a"'),('empty.txt',''),('binary.txt',None)]:
      r.open_via_input(f); pg.wait_for_timeout(1200); m=r.modal()
      if m and re.search('unsaved|discard',m['text'],re.I): r.click_modal(r'discard|continue|don'); pg.wait_for_timeout(1000); m=r.modal()
      if expect is None: r.rec('Open random binary as .txt → rejected or warned','PASS' if m or re.search('binary|not.*text|encoding|could not',pg.evaluate("()=>document.body.innerText"),re.I) else 'WARNING','modal='+str(m and m['text'][:160])+' title='+r.title()+' status='+str(pg.evaluate(STATUS)))
      else: r.rec(f'Open {f}','PASS' if (expect in ed(pg)) and (expect or ed(pg).strip()=='') else 'FAIL',f'title={r.title()} modal={m and m["text"][:100]}')
      r.clear()
    # recovery: edit and reload without saving
    r.open_via_input('audit.txt'); pg.wait_for_timeout(800); r.clear(); m=r.modal()
    if m: r.click_modal(r'discard|continue')
    pg.click('#editor'); pg.keyboard.press('Control+End'); pg.keyboard.type('RECOVERME'); pg.wait_for_timeout(1500)
    r.dialog_policy='accept'; pg.reload(); pg.wait_for_timeout(2500); r.dialog_policy='dismiss'
    m=r.modal(); body=pg.evaluate("()=>document.body.innerText"); rec=('RECOVERME' in ed(pg)) or (m and re.search('recover|restore',m['text'],re.I))
    r.rec('Crash/reload recovery of unsaved text','PASS' if rec else 'FAIL',f'modal={m and m["text"][:160]} editor={ed(pg)[-20:]!r}'); r.shot('recovery')
    if m: r.click_modal(r'restore|recover|open'); pg.wait_for_timeout(800); r.rec('restore action','INFO',f'editor={ed(pg)[-20:]!r}')
    r.menu(); pg.click('#newBtn'); pg.wait_for_timeout(500); m=r.modal()
    if m: r.click_modal(r'discard|continue|don'); pg.wait_for_timeout(500)
    r.rec('New text file','PASS' if 'Untitled' in r.title() and ed(pg).strip()=='' else 'FAIL',r.title())
    pg.click('#editor'); pg.keyboard.type('unsaved')
    r.rec('beforeunload guard when dirty','PASS' if r.before_unload_guard() else 'FAIL','')
    r.finish()
for prof in sys.argv[2:]: run(prof)

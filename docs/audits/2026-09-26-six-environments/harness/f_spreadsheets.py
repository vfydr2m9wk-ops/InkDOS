import sys,io,shutil
sys.path.insert(0,sys.argv[1])
from fw import *
import openpyxl
CELL="(ref)=>{const e=document.querySelector('#gridStage .cell[data-ref=\"'+ref+'\"]');return e?e.innerText.trim():null}"
def cell(pg,ref): return pg.evaluate(CELL,ref)
def sel(pg,ref): pg.locator(f'#gridStage .cell[data-ref="{ref}"]').click(); pg.wait_for_timeout(150)
def run(profile):
  r=Run('spreadsheets',profile); print('#### spreadsheets',profile)
  with sync_playwright() as pw:
    r.start(pw); pg=r.pg
    ok=r.open_via_chooser('#startOpen','audit.xlsx'); pg.wait_for_function("()=>document.querySelector('#gridStage .cell[data-ref=\"B1\"]')?.innerText.includes('Item 1')",timeout=15000)
    r.rec('open XLSX via start Open + picker','PASS' if ok else 'FAIL',f'title={r.title()}')
    v={k:cell(pg,k) for k in ['A1','B1','C1','C10','E1','E2']}
    r.rec('formula cached values + numeric-text preserved','PASS' if v['C1']=='2' and v['C10']=='20' and v['E1']=='55' and v['E2']=='00123' else 'FAIL',v)
    r.rec('dirty after open','PASS' if r.dirty() is False else 'FAIL',r.dirty())
    sel(pg,'D1'); pg.keyboard.type('hello'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    r.rec('type into cell','PASS' if cell(pg,'D1')=='hello' else 'FAIL',cell(pg,'D1'))
    nb=pg.locator('#nameBox').input_value(); r.rec('Enter moves selection down','PASS' if nb=='D2' else 'WARNING',nb)
    pg.keyboard.type('=A2+E1'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    r.rec('enter formula in cell','PASS' if cell(pg,'D2')=='57' else 'FAIL',cell(pg,'D2'))
    r.rec('dirty after edit','PASS' if r.dirty() else 'FAIL',r.dirty())
    sel(pg,'A1'); pg.fill('#formulaInput','10'); pg.press('#formulaInput','Enter'); pg.wait_for_timeout(400)
    r.rec('formula bar edit + dependent recalculation','PASS' if cell(pg,'A1')=='10' and cell(pg,'C1')=='20' and cell(pg,'E1')=='64' and cell(pg,'D2')=='66' else 'FAIL',{k:cell(pg,k) for k in ['A1','C1','E1','D2']})
    sel(pg,'A1'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowDown'); nb=pg.locator('#nameBox').input_value(); r.rec('arrow-key navigation','PASS' if nb=='B2' else 'FAIL',nb)
    pg.fill('#nameBox','C5'); pg.press('#nameBox','Enter'); pg.wait_for_timeout(200); act=pg.evaluate("()=>document.querySelector('#gridStage .cell.selected')?.dataset.ref"); r.rec('Name box jump','PASS' if act=='C5' else 'FAIL',act)
    sel(pg,'A1'); pg.locator('#gridStage .cell[data-ref="B3"]').click(modifiers=['Shift']); pg.wait_for_timeout(200)
    rng=pg.evaluate("()=>[...document.querySelectorAll('#gridStage .cell.in-range')].map(e=>e.dataset.ref)"); r.rec('multi-cell range selection','PASS' if set(['A1','A2','A3','B1','B2','B3'])<=set(rng) else 'FAIL',rng)
    pg.click('#boldBtn'); pg.wait_for_timeout(300); fw=pg.evaluate("()=>getComputedStyle(document.querySelector('#gridStage .cell[data-ref=\"B2\"]')).fontWeight"); r.rec('Bold on range','PASS' if int(fw)>=600 else 'FAIL',fw)
    pg.click('#undoBtn'); pg.wait_for_timeout(300); fw2=pg.evaluate("()=>getComputedStyle(document.querySelector('#gridStage .cell[data-ref=\"B2\"]')).fontWeight")
    pg.click('#redoBtn'); pg.wait_for_timeout(300); fw3=pg.evaluate("()=>getComputedStyle(document.querySelector('#gridStage .cell[data-ref=\"B2\"]')).fontWeight")
    r.rec('Undo/Redo','PASS' if int(fw2)<600 and int(fw3)>=600 else 'FAIL',f'{fw}->{fw2}->{fw3}')
    # delete row destructive + undo
    sel(pg,'A5'); before=cell(pg,'B5'); pg.click('#deleteRowBtn'); pg.wait_for_timeout(400); m=r.modal()
    if m: r.rec('delete row confirmation','INFO',m['text'][:120]); r.click_modal(r'delete|ok|confirm')
    after=cell(pg,'B5'); pg.click('#undoBtn'); pg.wait_for_timeout(400); und=cell(pg,'B5')
    r.rec('Delete row (destructive) then Undo restores','PASS' if after!=before and und==before else 'FAIL',f'{before} -> {after} -> undo {und}')
    # sheet tabs
    tabs=pg.evaluate("()=>[...document.querySelectorAll('#sheetTabs button,#sheetTabs [role=tab]')].map(b=>b.innerText.trim())"); r.rec('sheet tabs listed','PASS' if 'Second' in ' '.join(tabs) else 'FAIL',tabs)
    pg.locator('#sheetTabs').get_by_text('Second',exact=True).first.click(); pg.wait_for_timeout(400); a1=cell(pg,'A1'); pg.locator('#sheetTabs').get_by_text('Data',exact=True).first.click(); pg.wait_for_timeout(300)
    r.rec('switch worksheet and back','PASS' if a1=='sheet2' and cell(pg,'D1')=='hello' else 'FAIL',f'second A1={a1} back D1={cell(pg,"D1")}')
    # zoom
    pg.click('#zoomMenuBtn'); pg.wait_for_timeout(300); z=pg.evaluate("()=>[...document.querySelectorAll('button,[role=menuitemradio]')].filter(b=>/^\\d+%$/.test(b.innerText.trim())&&b.getBoundingClientRect().width>0).map(b=>b.innerText.trim())")
    r.rec('zoom menu','PASS' if z else 'FAIL',z)
    if z: pg.get_by_text(z[-1],exact=True).last.click(); pg.wait_for_timeout(300); r.rec('zoom applied','PASS' if z[-1] in pg.locator('#zoomMenuBtn').inner_text() else 'WARNING',pg.locator('#zoomMenuBtn').inner_text())
    pg.keyboard.press('Escape')
    # save
    def do_save():
      r.menu(); pg.click('#menuSave'); pg.wait_for_timeout(600); m=r.modal(); c=None
      if m: c=r.click_modal(r'save|xlsx|copy|continue'); pg.wait_for_timeout(1200)
      return m,c
    if profile=='fs':
      r.setmode('abort'); m,c=do_save(); r.rec('Save → picker cancelled','PASS' if r.dirty() and not r.saved() else 'FAIL',f'dialog={m and m["text"][:120]} dirty={r.dirty()}'); r.clear()
      r.setmode('writefail'); m,c=do_save(); m2=r.modal(); st=pg.evaluate("()=>document.body.innerText.match(/could not[^\\n]*|failed[^\\n]*/i)?.[0]")
      r.rec('Save → write error surfaced, stays dirty','PASS' if r.dirty() and (m2 or st) else 'FAIL',f'modal={m2 and m2["text"][:200]} msg={st}'); r.shot('writefail'); r.clear()
      r.setmode('ok'); m,c=do_save(); sv=r.saved()
      if sv:
        data=r.saved_bytes(); open(f'{S}/func/sheet_saved.xlsx','wb').write(data); import traceback
        try:
          wb=openpyxl.load_workbook(io.BytesIO(data)); ws=wb['Data']
        except Exception as e:
          r.rec('Saved XLSX loads in openpyxl (after prior cancelled + failed save attempts)','FAIL','IndexError: dangling cell style index (styles.xml not rewritten)'); wb=None
        if wb is None: vals={}
        else: vals={'A1':ws['A1'].value,'D1':ws['D1'].value,'D2':ws['D2'].value,'E2':ws['E2'].value,'C1':ws['C1'].value,'B2bold':ws['B2'].font.b,'sheets':wb.sheetnames}
        if vals: r.rec('Save → XLSX valid with edits/formulas/text preserved','PASS' if vals['A1']==10 and vals['D1']=='hello' and str(vals['D2']).upper()=='=A2+E1' and vals['E2']=='00123' and vals['C1']=='=A1*2' and vals['B2bold'] else 'FAIL',vals)
      else: r.rec('Save → XLSX written','FAIL',f'dialog={m} saved={sv}')
      r.rec('dirty cleared after save','PASS' if r.dirty() is False else 'WARNING',r.dirty())
      shutil.copy(f'{S}/func/sheet_saved.xlsx',f'{FX}/sheet_saved.xlsx'); r.clear()
      r.menu(); ok=r.open_via_chooser('#menuOpen','sheet_saved.xlsx'); pg.wait_for_timeout(1500); m=r.modal()
      if m: r.click_modal(r'discard|open|continue')
      r.rec('reopen saved XLSX','PASS' if cell(pg,'D1')=='hello' and cell(pg,'D2')=='66' else 'FAIL',f'D1={cell(pg,"D1")} D2={cell(pg,"D2")} title={r.title()}')
    else:
      m,c=do_save(); pg.wait_for_timeout(800); r.rec('Save (no FS API) → download fallback','PASS' if r.downloads else 'FAIL',f'{[d["name"] for d in r.downloads]} dialog={m and m["text"][:120]}'); r.clear()
    # dirty guard
    sel(pg,'F1'); pg.keyboard.type('x'); pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    r.menu(); pg.click('#menuOpen'); pg.wait_for_timeout(500); m=r.modal(); r.rec('Open while dirty → guard','PASS' if m else 'FAIL',m and m['text'][:200])
    if m:
      c=r.click_modal(r'^cancel|keep'); r.rec('Guard → Cancel','PASS' if c and cell(pg,'F1')=='x' else 'FAIL',c)
      r.menu()
      try:
        with pg.expect_file_chooser(timeout=4000) as fc:
          pg.click('#menuOpen'); pg.wait_for_timeout(400); r.click_modal(r'discard|don|continue|open')
        fc.value.set_files(f'{FX}/audit.xls'); pg.wait_for_timeout(2500); m=r.modal()
        if m: r.rec('XLS open notice','INFO',m['text'][:200]); r.clear()
        r.rec('Guard → Discard → open legacy XLS','PASS' if cell(pg,'B1')=='Item 1' and cell(pg,'C1') in('2','2.0') else 'FAIL',{k:cell(pg,k) for k in ['A1','B1','C1','E1','E2']})
      except Exception as e: r.rec('Guard → Discard → open XLS','FAIL',repr(e)[:200])
    for bad in ['invalid.xlsx','empty.docx']:
      if bad=='empty.docx': shutil.copy(f'{FX}/empty.txt',f'{FX}/empty.xlsx'); bad='empty.xlsx'
      r.open_via_input(bad); pg.wait_for_timeout(1500); m=r.modal()
      if m and re.search('unsaved|discard',m['text'],re.I): r.click_modal(r'discard|don'); pg.wait_for_timeout(1200); m=r.modal()
      r.rec(f'Open {bad} → error, previous workbook kept','PASS' if m and re.search('could not|invalid|error|not|empty|unsupported',m['text'],re.I) and cell(pg,'B1')=='Item 1' else 'FAIL',f'modal={m and m["text"][:200]} B1={cell(pg,"B1")}'); r.clear()
    r.menu(); pg.click('#menuNew'); pg.wait_for_timeout(500); m=r.modal()
    if m: r.click_modal(r'discard|don|new|continue'); pg.wait_for_timeout(500)
    r.rec('New workbook','PASS' if 'Untitled' in r.title() and not cell(pg,'B1') else 'FAIL',r.title())
    sel(pg,'A1'); pg.keyboard.type('u'); pg.keyboard.press('Enter')
    r.rec('beforeunload guard when dirty','PASS' if r.before_unload_guard() else 'FAIL','')
    r.finish()
for prof in sys.argv[2:]: run(prof)

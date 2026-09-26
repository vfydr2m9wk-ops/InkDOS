import sys; sys.path.insert(0,sys.argv[1]); from fw import *
JS="(r)=>{const e=document.querySelector('#gridStage .cell[data-ref=\"'+r+'\"]');return e?e.innerText:null}"
def case(second,dirty_first):
  r=Run('spreadsheets','nofs')
  with sync_playwright() as pw:
    r.start(pw); pg=r.pg; C=lambda ref: pg.evaluate(JS,ref)
    r.open_via_input('audit.xlsx'); pg.wait_for_timeout(1200)
    if dirty_first: pg.locator('#gridStage .cell[data-ref="F1"]').click(); pg.keyboard.type('x'); pg.keyboard.press('Enter')
    r.menu()
    with pg.expect_file_chooser(timeout=4000) as fc:
      pg.click('#menuOpen'); pg.wait_for_timeout(400); g1=r.modal(); r.click_modal(r'^discard')
    fc.value.set_files(f'{FX}/{second}'); pg.wait_for_timeout(2500); m=r.modal()
    print('dirtyFirst',dirty_first,'second',second,'| firstGuard',bool(g1),'| secondModal',m and m['text'][:50],'| F1',repr(C('F1')),'D1',repr(C('D1')),'dirty',r.dirty())
    if m:
      r.click_modal(r'^discard'); pg.wait_for_timeout(1500); print('    after 2nd Discard: modal',r.modal(),'title',r.title(),'F1',repr(C('F1')),'D1',repr(C('D1')))
    r.ctx.close(); r.br.close()

print('--- cancel on second prompt')
r=Run('spreadsheets','nofs')
with sync_playwright() as pw:
  r.start(pw); pg=r.pg; C=lambda ref: pg.evaluate(JS,ref)
  r.open_via_input('audit.xlsx'); pg.wait_for_timeout(1200)
  pg.locator('#gridStage .cell[data-ref="F1"]').click(); pg.keyboard.type('x'); pg.keyboard.press('Enter')
  r.menu()
  with pg.expect_file_chooser(timeout=4000) as fc:
    pg.click('#menuOpen'); pg.wait_for_timeout(400); r.click_modal(r'^discard')
  fc.value.set_files(f'{FX}/sheet_saved.xlsx'); pg.wait_for_timeout(2500)
  print('before cancel: F1',repr(C('F1')),'D1',repr(C('D1')),'title',r.title())
  r.click_modal(r'^cancel'); pg.wait_for_timeout(1200)
  print('after cancel: modal',r.modal(),'F1',repr(C('F1')),'D1',repr(C('D1')),'title',r.title(),'dirty',r.dirty())

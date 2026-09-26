import sys; sys.path.insert(0,sys.argv[1]); from fw import *
for entry in ['menu','toolbar-shortcut']:
  r=Run('presentations','nofs')
  with sync_playwright() as pw:
    r.start(pw); pg=r.pg; r.open_via_input('audit.pptx'); pg.wait_for_timeout(1500)
    pg.click('#addSlideBtn'); pg.wait_for_timeout(300)
    if entry=='menu': r.menu(); pg.click('#openMenuBtn')
    else: pg.keyboard.press('Control+o')
    pg.wait_for_timeout(600); r.shot('guard_'+entry)
    g=pg.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='Discard'&&b.getBoundingClientRect().width>0);if(!b)return null;const d=b.closest('[role=dialog],[role=alertdialog],.backdrop,div');const r=b.getBoundingClientRect();const top=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {btn:[r.x,r.y],hit:top?.id||top?.className||top?.tagName,covered:!b.contains(top),container:(b.parentElement?.parentElement?.id||'')+' '+(b.parentElement?.parentElement?.className||'')}}")
    print(entry,g)
    r.ctx.close(); r.br.close()

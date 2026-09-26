import sys,io,zipfile,re
sys.path.insert(0,sys.argv[1]); from fw import *
def save(r,mode):
  pg=r.pg; r.setmode(mode); r.menu(); pg.click('#menuSave'); pg.wait_for_timeout(1300); r.clear()
def go(name,steps):
  r=Run('spreadsheets','fs')
  with sync_playwright() as pw:
    r.start(pw); pg=r.pg; r.open_via_input('audit.xlsx'); pg.wait_for_timeout(1500)
    for s in steps:
      if s=='bold': pg.locator('#gridStage .cell[data-ref="A1"]').click(); pg.click('#boldBtn'); pg.wait_for_timeout(200)
      elif s=='undo': pg.click('#undoBtn'); pg.wait_for_timeout(200)
      elif s=='redo': pg.click('#redoBtn'); pg.wait_for_timeout(200)
      elif s=='edit': pg.locator('#gridStage .cell[data-ref="D1"]').click(); pg.keyboard.type('x'); pg.keyboard.press('Enter')
      else: save(r,s)
    data=r.saved_bytes(); r.ctx.close(); r.br.close()
  open(f'{S}/func/seq_'+name.replace(',','_')+'.xlsx','wb').write(data)
  z=zipfile.ZipFile(io.BytesIO(data)); sh=z.read('xl/worksheets/sheet1.xml').decode(); st=z.read('xl/styles.xml').decode()
  n=int(re.search(r'<cellXfs count="(\d+)"',st).group(1)); used=sorted(set(int(x) for x in re.findall(r' s="(\d+)"',sh)))
  print(f'{name:40}', 'cellXfs=',n,'used=',used,'VALID' if all(u<n for u in used) else 'INVALID')



go('bold,ok,edit,ok',['bold','ok','edit','ok'])


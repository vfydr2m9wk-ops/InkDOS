import json,base64,time,re,os
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:18431/InkDOS/'
S='/tmp/claude-0/-home-user-InkDOS/3e229ea0-7100-5fa3-981b-0b8143bfa533/scratchpad'; FX=S+'/fx'
INIT_FS=r"""
(()=>{window.__saved=[];window.__saveMode='ok';window.__shareCalls=0;
try{delete window.showOpenFilePicker}catch(_){ } window.showOpenFilePicker=undefined;
window.showSaveFilePicker=async(opts)=>{window.__lastSaveOpts=JSON.parse(JSON.stringify(opts||{}));
 if(window.__saveMode==='abort')throw new DOMException('cancelled','AbortError');
 const name=(opts&&opts.suggestedName)||'unnamed';
 return {name,kind:'file',createWritable:async()=>{if(window.__saveMode==='writefail')throw new DOMException('disk full','QuotaExceededError');const parts=[];return{write:async d=>{parts.push(d instanceof Blob?d:new Blob([d]))},close:async()=>{const bl=new Blob(parts);const buf=new Uint8Array(await bl.arrayBuffer());let s='';for(let i=0;i<buf.length;i+=32768)s+=String.fromCharCode.apply(null,buf.subarray(i,i+32768));window.__saved.push({name,size:buf.length,b64:btoa(s),t:performance.now()})}}}}};
})();"""
INIT_NOFS=r"""(()=>{try{window.showOpenFilePicker=undefined;window.showSaveFilePicker=undefined}catch(_){}})();"""
MODAL=r"""()=>{const vb=e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>8&&r.height>8&&c.visibility!=='hidden'&&c.display!=='none'};const vis=e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>40&&r.height>30&&c.visibility!=='hidden'&&c.display!=='none'&&Number(c.opacity)>0.05};
const cands=[...document.querySelectorAll('dialog[open],[role=dialog],[role=alertdialog],.error-overlay,.backdrop,.modal,.session-dialog,[class*=dialog],[class*=overlay],[class*=sheet]:not(#sheetTabs):not(.sheet-tabs)')].filter(e=>!/drawer|toolbar|editbar|tabs|bottom-shell/.test(String(e.className)+' '+e.id)).filter(vis).filter(e=>e.querySelector('button'));
const top=cands.filter(e=>{const b=[...e.querySelectorAll('button')].find(vb);if(!b)return false;const r=b.getBoundingClientRect();const h=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return h&&e.contains(h)});const d=(top.length?top:cands).sort((a,b)=>(b.getBoundingClientRect().width*b.getBoundingClientRect().height)-(a.getBoundingClientRect().width*a.getBoundingClientRect().height)).find(e=>!/drawer|toolbar|editbar|tabs|sheet-tab|bottom-shell/.test(e.className+' '+e.id))
if(!d)return null;return {id:d.id,cls:String(d.className).slice(0,60),text:d.innerText.replace(/\s+/g,' ').slice(0,300),buttons:[...d.querySelectorAll('button')].filter(vb).map(b=>{const r=b.getBoundingClientRect();return {id:b.id,text:b.innerText.trim().replace(/\s+/g,' ').slice(0,40),disabled:b.disabled,x:r.left+r.width/2,y:r.top+r.height/2}})}}"""
class Run:
  def __init__(s,app,profile='fs'):
    s.app=app; s.profile=profile; s.log=[]; s.errors=[]; s.dialogs=[]; s.downloads=[]
  def rec(s,step,status,detail=''):
    s.log.append({'step':step,'status':status,'detail':str(detail)[:600]}); print(f'  [{status}] {step} :: {str(detail)[:300]}',flush=True)
  def start(s,pw,entry='direct'):
    s.br=pw.chromium.launch(); s.ctx=s.br.new_context(viewport={'width':1366,'height':900},accept_downloads=True)
    s.ctx.add_init_script(INIT_FS if s.profile=='fs' else INIT_NOFS)
    s.pg=s.ctx.new_page(); pg=s.pg
    pg.on('console',lambda m: m.type=='error' and s.errors.append('console:'+m.text[:300]))
    pg.on('pageerror',lambda e: s.errors.append('pageerror:'+str(e)[:300]))
    pg.on('dialog',s._dialog)
    pg.on('download',lambda d: s.downloads.append({'name':d.suggested_filename,'path':d.path()}))
    s.dialog_policy='dismiss'
    if entry=='direct': pg.goto(B+f'apps/{s.app}/',wait_until='load')
    else: pg.goto(B,wait_until='load'); pg.click(f'a.workspace-card.{s.app}'); pg.wait_for_load_state('load')
    pg.wait_for_timeout(900)
  def _dialog(s,d):
    s.dialogs.append({'type':d.type,'msg':d.message[:200]})
    try:
      if s.dialog_policy=='accept': d.accept()
      else: d.dismiss()
    except Exception: pass
  def modal(s): return s.pg.evaluate(MODAL)
  def click_modal(s,pattern):
    m=s.modal()
    if not m: return None
    for b in m['buttons']:
      if re.search(pattern,b['text'],re.I) and not b['disabled']:
        s.pg.mouse.click(b['x'],b['y']); s.pg.wait_for_timeout(500); return b['text']
    return None
  def clear(s,pat=r'^(close|cancel|ok|dismiss|done|not now|keep editing|back|×|✕)$'):
    out=[]
    for _ in range(5):
      m=s.modal()
      if not m: break
      c=s.click_modal(pat)
      if not c:
        s.pg.keyboard.press('Escape'); s.pg.wait_for_timeout(300)
        if s.modal()==m: break
      out.append(c)
    return out
  def menu(s):
    openm=s.pg.evaluate("()=>{const b=document.getElementById('menuBackdrop');if(!b)return false;const c=getComputedStyle(b);return c.display!=='none'&&c.visibility!=='hidden'&&!b.hidden&&Number(c.opacity)>0.01&&c.pointerEvents!=='none'}")
    if openm: s.menu_left_open=getattr(s,'menu_left_open',0)+1; return
    s.pg.locator('#menuBtn:visible,#menuButton:visible').first.click(); s.pg.wait_for_timeout(350)
  def saved(s): return s.pg.evaluate("()=>window.__saved?window.__saved.map(x=>({name:x.name,size:x.size})):[]")
  def saved_bytes(s,i=-1):
    b=s.pg.evaluate(f"()=>window.__saved.at({i}).b64"); return base64.b64decode(b)
  def setmode(s,m): s.pg.evaluate(f"()=>window.__saveMode='{m}'")
  def open_via_input(s,f):
    s.pg.set_input_files('#fileInput',f'{FX}/{f}')
  def open_via_chooser(s,click_sel,f,timeout=4000):
    try:
      with s.pg.expect_file_chooser(timeout=timeout) as fc: s.pg.locator(click_sel).first.click()
      fc.value.set_files(f'{FX}/{f}'); return True
    except Exception as e: return False
  def dirty(s):
    return s.pg.evaluate("()=>{const d=document.getElementById('dirtyDot');if(!d)return null;const c=getComputedStyle(d),r=d.getBoundingClientRect();return c.display!=='none'&&c.visibility!=='hidden'&&Number(c.opacity)>0.05&&r.width>0&&!d.hidden}")
  def title(s): return s.pg.evaluate("()=>document.title")
  def shot(s,name): s.pg.screenshot(path=f'{S}/func/{s.app}_{s.profile}_{name}.png')
  def before_unload_guard(s):
    # check whether closing would prompt
    n=len(s.dialogs); s.dialog_policy='dismiss'
    try: s.pg.close(run_before_unload=True); s.pg.wait_for_timeout(700)
    except Exception as e: pass
    got=[d for d in s.dialogs[n:] if d['type']=='beforeunload']
    return bool(got)
  def finish(s):
    try: s.ctx.close(); s.br.close()
    except Exception: pass
    json.dump({'app':s.app,'profile':s.profile,'log':s.log,'errors':s.errors,'dialogs':s.dialogs,'downloads':[d['name'] for d in s.downloads]},open(f'{S}/func/{s.app}_{s.profile}.json','w'),indent=1)

import json,sys,time
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:18431/InkDOS/'; S=sys.argv[1]; FX=S+'/fx'; OUT=S+'/vis'
APPS={'documents':'audit.docx','spreadsheets':'audit.xlsx','presentations':'audit.pptx','txt':'audit.txt','epub':'audit.epub','pdf':'small.pdf'}
METRICS=r"""()=>{
const vis=e=>{if(!e)return false;const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>0&&r.height>0&&c.visibility!=='hidden'&&c.display!=='none'};
const pick=(sels)=>{for(const s of sels){for(const e of document.querySelectorAll(s)){if(vis(e))return e}}return null};
const st=(e,props)=>{if(!e)return null;const c=getComputedStyle(e),r=e.getBoundingClientRect();const o={sel:(e.id?'#'+e.id:e.tagName.toLowerCase()+'.'+[...e.classList].join('.')),w:Math.round(r.width),h:Math.round(r.height)};for(const p of props)o[p]=c.getPropertyValue(p);return o};
const box=['background-color','color','border-top','border-bottom','border-radius','padding','font-family','font-size','font-weight','line-height','box-shadow','opacity'];
const tb=pick(['.toolbar button:not([disabled]):not(.toolbar-scroll)','.editbar button:not([disabled])','.tool-btn:not([disabled])']);
const res={
 url:location.href,
 appearance:document.documentElement.dataset.appearanceResolved||document.documentElement.dataset.appearance,
 density:document.documentElement.dataset.uiDensity,
 body:st(document.body,box),
 header:st(pick(['.topbar','header']),box),
 menuBtn:st(pick(['#menuBtn','#menuButton']),box),
 title:st(pick(['#titleText','#docTitle','.document-title']),box),
 toolbar:st(pick(['.toolbar','.editbar','#editbar','.tool-rail']),box),
 toolBtn:st(tb,box),
 disabledBtn:st(pick(['.toolbar button[disabled]','.editbar button[disabled]','.tool-btn[disabled]','button[disabled]']),box),
 select:st(pick(['.toolbar select','.editbar select','select']),box),
 startPrimary:st(pick(['#startOpen','#openStartBtn']),box),
 startSecondary:st(pick(['#startNew']),box),
 status:st(pick(['.statusbar','.status-bar','#statusBar','footer','.status']),box),
 homeLink:(()=>{const a=[...document.querySelectorAll('a[href*="index.html"]')].find(x=>/\.\.\/\.\.\/index\.html/.test(x.getAttribute('href')));return a?{visible:vis(a),href:a.getAttribute('href')}:null})(),
};
return res}"""
DRAWER=r"""()=>{const vis=e=>{if(!e)return false;const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>0&&r.height>0&&c.visibility!=='hidden'&&c.display!=='none'&&Number(c.opacity)>0.05};
const d=[...document.querySelectorAll('.drawer,.general-drawer,[role=dialog],.menu,.popup-menu')].filter(vis).filter(e=>e.getBoundingClientRect().left<window.innerWidth-5)[0];if(!d)return null;
const c=getComputedStyle(d),r=d.getBoundingClientRect();const item=[...d.querySelectorAll('button')].find(vis);const ic=item?getComputedStyle(item):null;const lab=d.querySelector('.drawer-section-label,.drawer-title,h2,h3');const lc=lab?getComputedStyle(lab):null;
return {sel:d.id||d.className,x:Math.round(r.left),w:Math.round(r.width),h:Math.round(r.height),bg:c.backgroundColor,shadow:c.boxShadow,radius:c.borderRadius,border:c.borderRight,
item:item?{text:item.textContent.trim().slice(0,30),h:Math.round(item.getBoundingClientRect().height),bg:ic.backgroundColor,color:ic.color,radius:ic.borderRadius,pad:ic.padding,fs:ic.fontSize,fw:ic.fontWeight,ff:ic.fontFamily}:null,
label:lab?{text:lab.textContent.trim().slice(0,30),fs:lc.fontSize,fw:lc.fontWeight,color:lc.color,tt:lc.textTransform}:null,
items:[...d.querySelectorAll('button')].filter(vis).map(b=>b.textContent.trim().replace(/\s+/g,' ').slice(0,28))}}"""
out={}
with sync_playwright() as p:
  br=p.chromium.launch()
  for app,fx in APPS.items():
    for entry in ['direct','home']:
      for theme in ['light','dark']:
        key=f'{app}|{entry}|{theme}'
        ctx=br.new_context(viewport={'width':1366,'height':900},color_scheme=theme); pg=ctx.new_page(); errs=[]
        pg.on('console',lambda m,errs=errs: m.type=='error' and errs.append(m.text[:200]))
        pg.on('pageerror',lambda e,errs=errs: errs.append('pageerror:'+str(e)[:200]))
        if entry=='direct': pg.goto(B+f'apps/{app}/',wait_until='load')
        else:
          pg.goto(B,wait_until='load'); pg.wait_for_timeout(400)
          if app=='txt' and theme=='light': pg.screenshot(path=f'{OUT}/home_{theme}.png')
          if app=='txt' and theme=='dark': pg.screenshot(path=f'{OUT}/home_{theme}.png')
          pg.click(f'a.workspace-card.{app}'); pg.wait_for_load_state('load')
        pg.wait_for_timeout(900)
        m=pg.evaluate(METRICS); pg.screenshot(path=f'{OUT}/{app}_{entry}_{theme}_empty.png')
        # drawer
        mb=pg.locator('#menuBtn:visible,#menuButton:visible').first
        drawer=None
        try:
          mb.click(); pg.wait_for_timeout(450); drawer=pg.evaluate(DRAWER); pg.screenshot(path=f'{OUT}/{app}_{entry}_{theme}_drawer.png')
          pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
          still=pg.evaluate(DRAWER)
        except Exception as e: drawer={'error':str(e)[:200]}; still=None
        pg.set_input_files('#fileInput',f'{FX}/{fx}'); pg.wait_for_timeout(2500)
        loaded=pg.evaluate(METRICS); pg.screenshot(path=f'{OUT}/{app}_{entry}_{theme}_loaded.png')
        out[key]={'empty':m,'drawer':drawer,'drawerAfterEscape':bool(still),'loaded':loaded,'errors':errs}
        ctx.close()
  br.close()
json.dump(out,open(f'{S}/visual.json','w'),indent=1)
print('ok',len(out))

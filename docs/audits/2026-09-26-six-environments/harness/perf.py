import sys,json,time,statistics; sys.path.insert(0,sys.argv[1]); from fw import *
N=int(sys.argv[2]) if len(sys.argv)>2 else 5
PERF_INIT=r"""(()=>{window.__lt=[];try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt.push([Math.round(e.startTime),Math.round(e.duration)])}).observe({type:'longtask',buffered:true})}catch(_){}
window.__marks={};document.addEventListener('change',e=>{if(e.target&&e.target.type==='file'){window.__marks.recv=performance.now()}},true);
const hook=()=>{const L0=window.pdfjsLib;if(!L0||window.__pdfHooked)return;window.__pdfHooked=1;const gd=L0.getDocument.bind(L0);const W=function(src){const M=window.__marks;M.gdStart=M.gdStart||performance.now();const task=gd(src);task.promise.then(doc=>{M.proxy=M.proxy||performance.now();const gp=doc.getPage.bind(doc);doc.getPage=function(n){if(n===1&&!M.getPage1Start)M.getPage1Start=performance.now();return gp(n).then(p=>{if(n===1&&!M.page1){M.page1=performance.now();const gv=p.getViewport.bind(p);p.getViewport=function(o){M.viewport1=M.viewport1||performance.now();return gv(o)};const rr=p.render.bind(p);p.render=function(o){M.renderStart1=M.renderStart1||performance.now();const t=rr(o);t.promise.then(()=>{M.renderDone1=M.renderDone1||performance.now()}).catch(()=>{});return t}}if(n>1&&!M.secondaryPage)M.secondaryPage=performance.now();return p})};});return task};window.pdfjsLib=Object.create(L0,{getDocument:{value:W}})};
document.addEventListener('DOMContentLoaded',hook);const iv=setInterval(()=>{hook();if(window.__pdfHooked)clearInterval(iv)},1);})();"""
READY={'documents':'#startOpen','spreadsheets':'#startOpen','presentations':'#startOpen','txt':'#startOpen','epub':'#openStartBtn','pdf':'#openStartBtn'}
VISIBLE={
 'documents':"()=>{const e=document.querySelector('.page-content');return !!e&&e.innerText.length>50&&e.getBoundingClientRect().height>100}",
 'spreadsheets':"()=>{const e=document.querySelector('#gridStage .cell[data-ref=\"B1\"]');return !!e&&e.innerText.length>0}",
 'presentations':"()=>{const s=[...document.querySelectorAll('span')].find(x=>/^Slide 1( Title)?$/.test(x.innerText)&&x.getBoundingClientRect().left>220);return !!s}",
 'txt':"()=>{const e=document.getElementById('editor');return !!e&&e.value.length>10&&e.getBoundingClientRect().height>50}",
 'epub':"()=>{const e=document.getElementById('readerSurface');return !!e&&/Chapter/.test(e.innerText)}",
 'pdf':"()=>{const c=document.querySelector('.pdf-page-host[data-page=\"1\"] canvas')||document.querySelector('.pdf-page-shell canvas');if(!c||!c.width)return false;try{const x=c.getContext('2d',{willReadFrequently:true});const w=c.width,h=Math.min(c.height,Math.floor(c.height*0.25));const d=x.getImageData(0,0,w,h).data;let dark=0;for(let i=0;i<d.length;i+=16){if(d[i]<100&&d[i+3]>0)dark++;if(dark>50)return true}return false}catch(e){return false}}"}
FILES={'documents':['audit.docx','large.docx'],'spreadsheets':['audit.xlsx','large.xlsx'],'presentations':['audit.pptx','large.pptx'],'txt':['audit.txt','large.txt'],'epub':['audit.epub','large.epub'],'pdf':['small.pdf','large.pdf']}
def med(xs): xs=[x for x in xs if x is not None]; return round(statistics.median(xs),1) if xs else None
res={}
with sync_playwright() as pw:
  br=pw.chromium.launch()
  for app in (sys.argv[3].split(',') if len(sys.argv)>3 else FILES):
    for f in FILES[app]:
      runs=[]
      for i in range(N):
        ctx=br.new_context(viewport={'width':1366,'height':900}); ctx.add_init_script(PERF_INIT); pg=ctx.new_page()
        cdp=ctx.new_cdp_session(pg); cdp.send('Performance.enable')
        t=time.time(); pg.goto(B+f'apps/{app}/',wait_until='load')
        pg.wait_for_function(f"()=>{{const b=document.querySelector('{READY[app]}');return b&&!b.disabled&&b.getBoundingClientRect().width>0}}",timeout=20000,polling='raf')
        nav=pg.evaluate("()=>{const n=performance.getEntriesByType('navigation')[0];const p=performance.getEntriesByName('first-contentful-paint')[0];return {dcl:n.domContentLoadedEventEnd,load:n.loadEventEnd,fcp:p?p.startTime:null,ready:performance.now()}}")
        lt0=pg.evaluate("()=>window.__lt.slice()")
        m0={x['name']:x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
        pg.wait_for_timeout(300)
        t_sel=pg.evaluate("()=>performance.now()")
        pg.set_input_files('#fileInput',f'{FX}/{f}')
        pg.wait_for_function(VISIBLE[app],timeout=60000,polling='raf')
        t_vis=pg.evaluate("()=>performance.now()")
        # time to interactive: next frame + a task with no long task pending
        t_int=pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>setTimeout(()=>r(performance.now()),0)))")
        pg.wait_for_timeout(1500)
        marks=pg.evaluate("()=>window.__marks"); lt=pg.evaluate("()=>window.__lt.slice()")
        m1={x['name']:x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
        openlt=[d for s,d in lt if s>=t_sel]
        run={'dcl':nav['dcl'],'load':nav['load'],'fcp':nav['fcp'],'uiReady':nav['ready'],'startupLongTaskMs':sum(d for s,d in lt0),'startupMaxLongTask':max([d for s,d in lt0] or [0]),
             'selToRecv':(marks.get('recv',t_sel)-t_sel),'recvToVisible':t_vis-marks.get('recv',t_sel),'selToVisible':t_vis-t_sel,'visibleToInteractive':t_int-t_vis,
             'openLongTaskTotal':sum(openlt),'openMaxLongTask':max(openlt or [0]),'openCpuTaskSec':round(m1['TaskDuration']-m0['TaskDuration'],3),'openScriptSec':round(m1['ScriptDuration']-m0['ScriptDuration'],3),'heapMB':round(m1['JSHeapUsedSize']/1e6,1)}
        if app=='pdf':
          R=marks.get('recv',t_sel)
          for k in ['gdStart','proxy','getPage1Start','page1','viewport1','renderStart1','renderDone1','secondaryPage']: run['pdf_'+k]=(marks[k]-R) if k in marks else None
          # loading overlay visible at first page?
        runs.append(run); ctx.close()
      agg={k:med([r[k] for r in runs]) for k in runs[0]}
      agg['_min_selToVisible']=round(min(r['selToVisible'] for r in runs),1); agg['_max_selToVisible']=round(max(r['selToVisible'] for r in runs),1)
      res[f'{app}|{f}']=agg; print(app,f,json.dumps(agg),flush=True)
  br.close()
json.dump(res,open(S+'/perf_'+(sys.argv[3] if len(sys.argv)>3 else 'all')+'.json','w'),indent=1)

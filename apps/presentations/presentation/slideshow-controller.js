(function(global){
'use strict';
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{},EMU=12700;
function create({session,overlay,host,counter}={}){
 let index=0,active=false;
 function n(v,f=0){v=Number(v);return Number.isFinite(v)?v:f}
 function px(v){return n(v)/EMU}
 function borderStyle(line){if(!line?.color)return 'none';return `${Math.max(1,px(line.widthEmu||12700))}px solid ${line.color}`}
 function baseBox(el,o){
  el.dataset.objectId=o.id||'';
  el.style.position='absolute';el.style.boxSizing='border-box';
  el.style.left=px(o.x)+'px';el.style.top=px(o.y)+'px';el.style.width=Math.max(0,px(o.w))+'px';el.style.height=Math.max(0,px(o.h))+'px';
  el.style.opacity=String(o.opacity??1);el.style.transform=o.rotation?`rotate(${o.rotation}deg)`:'none';el.style.transformOrigin='center center';
 }
 function renderParagraphs(target,o){
  const pars=Array.isArray(o.paragraphs)&&o.paragraphs.length?o.paragraphs:NS.PresentationModel.normalizeParagraphs(null,o.text,o);
  for(const p of pars){
   const line=document.createElement('div');
   line.style.textAlign=p.align||o.align||'left';
   if(o.wrap==='none')line.style.whiteSpace='nowrap';
   const linePt=Math.max(1,...(p.runs||[]).map(r=>(r.fontSizePt||o.fontSizePt||24)*(o.autoFitScale||1)));
   const lineHeightPt=p.lineSpacingPt!=null?p.lineSpacingPt*(o.autoFitScale||1):linePt*(p.lineSpacing||1.0);
   line.style.fontSize=linePt+'px';line.style.lineHeight=lineHeightPt+'px';line.style.paddingLeft=(Math.max(0,p.level||0)*18)+'px';
   if(p.spaceBeforePt)line.style.marginTop=p.spaceBeforePt+'px';if(p.spaceAfterPt)line.style.marginBottom=p.spaceAfterPt+'px';
   if(p.bullet){const bu=document.createElement('span');bu.textContent=p.bullet+' ';line.appendChild(bu)}
   for(const r of p.runs||[]){
    const s=document.createElement('span');s.textContent=r.text||'';
    s.style.fontSize=((r.fontSizePt||o.fontSizePt||24)*(o.autoFitScale||1))+'px';
    s.style.fontWeight=r.bold?'700':'400';s.style.fontStyle=r.italic?'italic':'normal';s.style.textDecoration=r.underline?'underline':'none';
    if(r.color)s.style.color=r.color;if(r.fontFamily)s.style.fontFamily=`${JSON.stringify(r.fontFamily)},Arial,sans-serif`;
    if(Number.isFinite(Number(r.charSpacingPt))&&Number(r.charSpacingPt)!==0)s.style.letterSpacing=(Number(r.charSpacingPt)*(o.autoFitScale||1))+'px';
    line.appendChild(s);
   }
   target.appendChild(line);
  }
 }
 function textNode(o){
  const box=document.createElement('div');baseBox(box,o);
  box.style.display='flex';box.style.overflow='hidden';box.style.flexDirection='column';
  box.style.padding=`${px(o.marginTopEmu||0)}px ${px(o.marginRightEmu||0)}px ${px(o.marginBottomEmu||0)}px ${px(o.marginLeftEmu||0)}px`;
  box.style.justifyContent=o.verticalAlign==='middle'?'center':o.verticalAlign==='bottom'?'flex-end':'flex-start';
  if(o.fill&&o.fill!=='none')box.style.background=o.fill;box.style.border=borderStyle(o.line);
  const content=document.createElement('div');content.dataset.slideshowTextContent='true';content.style.width='100%';content.style.minHeight='0';
  renderParagraphs(content,o);box.appendChild(content);return box;
 }
 function imageNode(o){
  const wrap=document.createElement('div');baseBox(wrap,o);wrap.style.overflow='hidden';wrap.style.border=borderStyle(o.line);
  const img=document.createElement('img');img.src=o.src||'';img.alt='';img.draggable=false;img.style.position='absolute';
  const c=o.crop||{},l=Math.max(0,Math.min(.95,n(c.left))),r=Math.max(0,Math.min(.95,n(c.right))),t=Math.max(0,Math.min(.95,n(c.top))),b=Math.max(0,Math.min(.95,n(c.bottom))),vw=Math.max(.01,1-l-r),vh=Math.max(.01,1-t-b);
  img.style.width=(100/vw)+'%';img.style.height=(100/vh)+'%';img.style.left=(-l/vw*100)+'%';img.style.top=(-t/vh*100)+'%';
  wrap.appendChild(img);return wrap;
 }
 function shapeNode(o){
  const el=document.createElement('div');baseBox(el,o);if(o.fill&&o.fill!=='none')el.style.background=o.fill;el.style.border=borderStyle(o.line);
  if(o.shapeType==='ellipse')el.style.borderRadius='50%';else if(o.shapeType==='roundRect')el.style.borderRadius='12%';else if(o.shapeType==='line'){el.style.height='0';el.style.border='0';el.style.borderTop=borderStyle(o.line||{color:'#000',widthEmu:12700})}
  return el;
 }
 function applyCellBorder(cell,side,line){if(!line?.color)return;cell.style[`border${side}`]=borderStyle(line)}
 function tableNode(o){
  const wrap=document.createElement('div');baseBox(wrap,o);wrap.style.overflow='hidden';
  const table=document.createElement('table');table.style.width='100%';table.style.height='100%';table.style.borderCollapse='collapse';table.style.tableLayout='fixed';
  const columns=Array.isArray(o.columns)?o.columns:[],totalWidth=Math.max(1,columns.reduce((sum,v)=>sum+(n(v)||0),0));
  if(columns.length){const cg=document.createElement('colgroup');for(const width of columns){const col=document.createElement('col');col.style.width=(Math.max(0,n(width))/totalWidth*100)+'%';cg.appendChild(col)}table.appendChild(cg)}
  const rows=Array.isArray(o.rows)?o.rows:[],totalHeight=Math.max(1,rows.reduce((sum,row)=>sum+(n(row.heightEmu)||0),0)),body=document.createElement('tbody');
  rows.forEach(row=>{const tr=document.createElement('tr');tr.style.height=(Math.max(0,n(row.heightEmu))/totalHeight*100)+'%';(row.cells||[]).forEach(cell=>{if(cell.hMerge||cell.vMerge)return;const td=document.createElement('td');if(n(cell.colSpan)>1)td.colSpan=Math.max(1,Math.round(n(cell.colSpan)));if(n(cell.rowSpan)>1)td.rowSpan=Math.max(1,Math.round(n(cell.rowSpan)));if(cell.fill&&cell.fill!=='none')td.style.background=cell.fill;td.style.verticalAlign=cell.verticalAlign==='top'?'top':cell.verticalAlign==='bottom'?'bottom':'middle';td.style.padding=`${px(cell.marginTopEmu||0)}px ${px(cell.marginRightEmu||0)}px ${px(cell.marginBottomEmu||0)}px ${px(cell.marginLeftEmu||0)}px`;applyCellBorder(td,'Left',cell.borders?.left);applyCellBorder(td,'Right',cell.borders?.right);applyCellBorder(td,'Top',cell.borders?.top);applyCellBorder(td,'Bottom',cell.borders?.bottom);const content=document.createElement('div');renderParagraphs(content,{...cell,fontSizePt:18,autoFitScale:1,wrap:'square'});td.appendChild(content);tr.appendChild(td)});body.appendChild(tr)});
  table.appendChild(body);wrap.appendChild(table);return wrap;
 }
 function animateTransition(layer,slide){const kind=String(slide?.transition||'none').toLowerCase();if(kind==='none'||typeof layer.animate!=='function')return null;let frames=null;if(kind==='fade')frames=[{opacity:0},{opacity:1}];else if(kind==='push')frames=[{transform:'translateX(18%)',opacity:.45},{transform:'translateX(0)',opacity:1}];else if(kind==='wipe')frames=[{clipPath:'inset(0 100% 0 0)'},{clipPath:'inset(0 0 0 0)'}];if(!frames)return null;return layer.animate(frames,{duration:360,easing:'cubic-bezier(.2,.75,.25,1)',fill:'both'})}
 function fit(slide,frame){
  if(!slide||!frame)return;
  const availableW=Math.max(1,overlay?.clientWidth||global.innerWidth||1),availableH=Math.max(1,overlay?.clientHeight||global.innerHeight||1),ratio=Math.max(.01,n(slide.widthEmu,1)/Math.max(1,n(slide.heightEmu,1)));
  let width=availableW,height=width/ratio;if(height>availableH){height=availableH;width=height*ratio}
  host.style.width=width+'px';host.style.height=height+'px';host.style.aspectRatio=`${slide.widthEmu}/${slide.heightEmu}`;
  const intrinsicW=Math.max(1,px(slide.widthEmu)),intrinsicH=Math.max(1,px(slide.heightEmu)),scale=Math.min(width/intrinsicW,height/intrinsicH);
  frame.style.width=intrinsicW+'px';frame.style.height=intrinsicH+'px';frame.style.transform=`scale(${scale})`;frame.style.transformOrigin='top left';
 }
 function fitCurrent(){if(!active)return;const slide=session.slides[index],frame=host.firstElementChild;if(slide&&frame)fit(slide,frame)}
 function render(){
  const slide=session.slides[index];if(!slide)return;
  const frame=document.createElement('div');frame.dataset.slideshowFrame='true';frame.style.position='absolute';frame.style.left='0';frame.style.top='0';
  const layer=document.createElement('div');layer.dataset.slideshowLayer='true';layer.style.cssText=`position:absolute;inset:0;background:${slide.background||'#fff'};color:#161616;overflow:hidden;font-family:Arial,Helvetica,sans-serif`;
  if(slide.backgroundImage){layer.style.backgroundImage=`url(${JSON.stringify(slide.backgroundImage)})`;layer.style.backgroundSize='cover';layer.style.backgroundPosition='center'}
  for(const o of slide.objects||[]){let node=null;if(o.type==='text')node=textNode(o);else if(o.type==='image')node=imageNode(o);else if(o.type==='shape')node=shapeNode(o);else if(o.type==='table')node=tableNode(o);if(node)layer.appendChild(node)}
  frame.appendChild(layer);host.replaceChildren(frame);fit(slide,frame);animateTransition(layer,slide);counter.textContent=`${index+1} / ${session.slides.length}`;
 }
 function open(fromStart=false){if(!session.active)return false;index=fromStart?0:session.currentIndex;active=true;overlay.hidden=false;document.body.dataset.presenting='true';render();overlay.focus();try{overlay.requestFullscreen?.()}catch(_){}return true}
 function close(){active=false;overlay.hidden=true;delete document.body.dataset.presenting;if(document.fullscreenElement)document.exitFullscreen?.().catch?.(()=>{})}
 function next(){if(index<session.slides.length-1){index++;render()}else close()}
 function prev(){if(index>0){index--;render()}}
 function key(e){if(!active)return;if(['ArrowRight','PageDown',' ','Enter'].includes(e.key)){e.preventDefault();next()}else if(['ArrowLeft','PageUp','Backspace'].includes(e.key)){e.preventDefault();prev()}else if(e.key==='Home'){index=0;render()}else if(e.key==='End'){index=session.slides.length-1;render()}else if(e.key==='Escape')close()}
 overlay.addEventListener('click',e=>{if(e.target.closest('[data-present-exit]'))return;next()});overlay.querySelector('[data-present-exit]')?.addEventListener('click',e=>{e.stopPropagation();close()});document.addEventListener('keydown',key);
 global.addEventListener?.('resize',fitCurrent);global.visualViewport?.addEventListener?.('resize',fitCurrent);document.addEventListener('fullscreenchange',fitCurrent);
 if(typeof global.ResizeObserver==='function'){const ro=new global.ResizeObserver(fitCurrent);ro.observe(overlay)}
 return Object.freeze({open,close,render,get active(){return active}})
}
NS.SlideshowController=Object.freeze({create});
})(globalThis);

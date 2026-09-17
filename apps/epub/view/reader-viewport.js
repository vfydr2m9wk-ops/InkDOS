(function(g){
'use strict';
const NS=g.InkDOS2Epub=g.InkDOS2Epub||{};
let probes=null;
function clamp(n,a,b){return Math.max(a,Math.min(b,n))}
function ensureViewportProbes(){
 if(probes||!g.document)return probes;
 const host=document.body||document.documentElement;
 if(!host)return null;
 const make=unit=>{const el=document.createElement('span');el.setAttribute('aria-hidden','true');el.style.cssText='position:fixed;left:-10000px;top:0;width:0;height:100'+unit+';visibility:hidden;pointer-events:none;overflow:hidden;contain:strict;';host.appendChild(el);return el};
 try{probes={small:make('svh'),dynamic:make('dvh')}}catch(_){probes=null}
 return probes;
}
function viewportUnitHeights(){
 if(!(g.CSS&&CSS.supports&&CSS.supports('height','100svh')&&CSS.supports('height','100dvh')))return Object.freeze({small:0,dynamic:0,delta:0});
 const p=ensureViewportProbes();if(!p)return Object.freeze({small:0,dynamic:0,delta:0});
 const small=p.small.getBoundingClientRect().height,dynamic=p.dynamic.getBoundingClientRect().height;
 return Object.freeze({small,dynamic,delta:Math.max(0,dynamic-small)});
}
function normalizePageHeight(rawHeight,dynamicHeight,smallHeight){
 const raw=Math.max(0,Number(rawHeight)||0),dynamic=Math.max(0,Number(dynamicHeight)||0),small=Math.max(0,Number(smallHeight)||0),delta=Math.max(0,dynamic-small);
 return Math.max(0,raw-delta);
}
function measure(viewport,epoch=0){
 const r=viewport.getBoundingClientRect(),units=viewportUnitHeights();
 const stableHeight=units.small>0&&units.dynamic>0?normalizePageHeight(r.height,units.dynamic,units.small):Math.max(0,r.height);
 return Object.freeze({availableWidth:Math.max(0,r.width),availableHeight:stableHeight,physicalHeight:Math.max(0,r.height),viewportDynamicDelta:units.delta,rect:Object.freeze({left:r.left,top:r.top,width:r.width,height:r.height}),dpr:devicePixelRatio||1,epoch,visibility:r.width>0&&r.height>0?'visible':'suspended',unit:'css-px'});
}
function sameLayoutMetrics(a,b,tolerance=.5){return !!(a&&b&&Math.abs(a.availableWidth-b.availableWidth)<=tolerance&&Math.abs(a.availableHeight-b.availableHeight)<=tolerance)}

function stabilizePaginationMetrics(previous,next,tolerance=1){
 if(!previous||!next||previous.availableWidth<=0||previous.availableHeight<=0||next.availableWidth<=0||next.availableHeight<=0)return next;
 if(Math.abs(previous.availableWidth-next.availableWidth)>tolerance)return next;
 const lockedHeight=Math.min(previous.availableHeight,next.availableHeight);
 if(Math.abs(lockedHeight-next.availableHeight)<=.5)return next;
 return Object.freeze({...next,availableHeight:lockedHeight,paginationHeightLocked:true});
}
function anchorElements(surface){return Array.from(surface.querySelectorAll('[data-anchor]'))}
function nearestAnchor(viewport,surface,flow){const vr=viewport.getBoundingClientRect(),els=anchorElements(surface);let best=null,bestScore=Infinity;for(const el of els){const rects=Array.from(el.getClientRects());for(const r of rects){const visibleX=r.right>vr.left&&r.left<vr.right,visibleY=r.bottom>vr.top&&r.top<vr.bottom;if(flow==='pages'){if(!visibleX||!visibleY)continue;const score=Math.abs(r.left-vr.left)+Math.abs(r.top-vr.top)*.1;if(score<bestScore){bestScore=score;best=el}}else{if(!visibleY)continue;const score=Math.abs(r.top-vr.top);if(score<bestScore){bestScore=score;best=el}}}}if(!best)return null;return Object.freeze({anchor:best.dataset.anchor||'',chapter:Number(best.dataset.chapter||1),path:best.dataset.path||'',fragment:best.dataset.sourceId||''})}
function restoreAnchor(viewport,surface,loc,flow,width){if(!loc||!loc.anchor)return false;const esc=(g.CSS&&CSS.escape)?CSS.escape(loc.anchor):loc.anchor.replace(/["\\]/g,'\\$&'),el=surface.querySelector('[data-anchor="'+esc+'"]');if(!el)return false;const vr=viewport.getBoundingClientRect(),er=(Array.from(el.getClientRects())[0]||el.getBoundingClientRect());if(flow==='pages'){const raw=viewport.scrollLeft+(er.left-vr.left);const page=Math.max(0,Math.floor((raw+Math.max(1,width)*.08)/Math.max(1,width)));viewport.scrollTo({left:page*Math.max(1,width),top:0,behavior:'auto'})}else{viewport.scrollTo({top:Math.max(0,viewport.scrollTop+(er.top-vr.top)-22),left:0,behavior:'auto'})}return true}
function apply(viewport,surface,flow,fontPx,metrics){viewport.classList.toggle('mode-pages',flow==='pages');viewport.classList.toggle('mode-scroll',flow==='scroll');surface.style.setProperty('--font-px',fontPx+'px');surface.style.removeProperty('column-width');surface.style.removeProperty('column-gap');surface.style.removeProperty('height');surface.style.removeProperty('min-height');surface.style.removeProperty('width');surface.style.removeProperty('padding');if(flow==='pages'){const desired=Math.min(820,Math.max(1,metrics.availableWidth-40)),side=Math.max(20,(metrics.availableWidth-desired)/2),top=Math.max(22,Math.min(48,metrics.availableHeight*.055)),col=Math.max(1,metrics.availableWidth-side*2);surface.style.width=metrics.availableWidth+'px';surface.style.height=metrics.availableHeight+'px';surface.style.minHeight=metrics.availableHeight+'px';surface.style.padding=top+'px '+side+'px';surface.style.columnWidth=col+'px';surface.style.columnGap=(side*2)+'px';return Object.freeze({flow,fontPx,pageWidth:metrics.availableWidth,pageHeight:metrics.availableHeight,columnWidth:col,gap:side*2})}return Object.freeze({flow,fontPx,pageWidth:0,pageHeight:0,columnWidth:0,gap:0})}
function pageCount(viewport,width){return Math.max(1,Math.round(viewport.scrollWidth/Math.max(1,width)))}
function pageIndex(viewport,width,count){return clamp(Math.round(viewport.scrollLeft/Math.max(1,width)),0,Math.max(0,count-1))}
NS.ReaderViewport={measure,sameLayoutMetrics,stabilizePaginationMetrics,normalizePageHeight,viewportUnitHeights,nearestAnchor,restoreAnchor,apply,pageCount,pageIndex,clamp};
})(globalThis);

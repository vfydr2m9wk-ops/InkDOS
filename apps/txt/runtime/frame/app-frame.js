(function(g){'use strict';
const NS=g.InkDOS2=g.InkDOS2||{};
function centerError(el){if(!el)return null;const r=el.getBoundingClientRect();return Math.abs((r.left+r.width/2)-g.innerWidth/2)}
function configureOptionalHome(){const link=document.querySelector('a[aria-label="Home"]');if(!link)return false;let enabled=false;try{enabled=new URLSearchParams(g.location.search).get('suite')==='1'}catch(_){}if(enabled){link.hidden=false;link.removeAttribute('aria-hidden');link.removeAttribute('tabindex')}else{link.hidden=true;link.setAttribute('aria-hidden','true');link.tabIndex=-1;link.removeAttribute('href')}return enabled}
function bindDrawer({trigger,drawer,backdrop,closeButton,beforeOpen}={}){
  if(!trigger||!drawer||!backdrop||!closeButton)throw new Error('AppFrame.bindDrawer requires trigger, drawer, backdrop and closeButton');
  function open(){if(typeof beforeOpen==='function')beforeOpen();drawer.hidden=false;backdrop.hidden=false;closeButton.focus()}
  function close({restoreFocus=true}={}){drawer.hidden=true;backdrop.hidden=true;if(restoreFocus)trigger.focus({preventScroll:true})}
  trigger.addEventListener('click',open);closeButton.addEventListener('click',()=>close());backdrop.addEventListener('click',()=>close());
  return Object.freeze({open,close,get isOpen(){return !drawer.hidden}})
}
function bindHorizontalScroller(el){
  if(!el)throw new Error('AppFrame.bindHorizontalScroller requires an element');
  let dragging=false,startX=0,startScroll=0;
  const down=e=>{if(e.pointerType==='mouse'&&!e.target.closest('button,input,select')){dragging=true;startX=e.clientX;startScroll=el.scrollLeft;el.setPointerCapture(e.pointerId)}};
  const move=e=>{if(dragging)el.scrollLeft=startScroll-(e.clientX-startX)};
  const stop=()=>{dragging=false};
  const wheel=e=>{if(Math.abs(e.deltaY)>Math.abs(e.deltaX)){el.scrollLeft+=e.deltaY;e.preventDefault()}};
  el.addEventListener('pointerdown',down);el.addEventListener('pointermove',move);el.addEventListener('pointerup',stop);el.addEventListener('pointercancel',stop);el.addEventListener('wheel',wheel,{passive:false});
  return Object.freeze({dispose(){el.removeEventListener('pointerdown',down);el.removeEventListener('pointermove',move);el.removeEventListener('pointerup',stop);el.removeEventListener('pointercancel',stop);el.removeEventListener('wheel',wheel)}})
}
function installToolbarRail(target){
  if(!target)throw new Error('AppFrame.installToolbarRail requires a toolbar');
  if(target.closest('.inkdos-toolbar-rail'))return false;
  if(!document.getElementById('inkdosToolbarRailStyle')){const style=document.createElement('style');style.id='inkdosToolbarRailStyle';style.textContent=`.inkdos-toolbar-rail{width:100%;min-width:0;display:grid;grid-template-columns:34px 1px minmax(0,1fr) 1px 34px;align-items:stretch;background:var(--chrome,var(--frame-chrome,#fff));border-bottom:1px solid var(--line,var(--frame-line,#d7dce2));position:relative;z-index:30}.inkdos-toolbar-rail>.inkdos-toolbar-scroll{grid-column:3;min-width:0!important;width:100%!important;max-width:none!important;border-bottom:0!important}.inkdos-toolbar-arrow{width:34px;min-width:34px;min-height:44px;padding:0;border:0;border-radius:0;background:transparent;color:var(--muted,var(--frame-muted,#5f6368));font:600 18px/1 Arial,sans-serif;display:grid;place-items:center;cursor:pointer;user-select:none;-webkit-user-select:none}.inkdos-toolbar-arrow:hover:not(:disabled),.inkdos-toolbar-arrow:focus-visible:not(:disabled){background:var(--toolbar-hover,var(--frame-hover,rgba(60,64,67,.08)));color:var(--text,var(--frame-text,#202124));outline:none}.inkdos-toolbar-arrow:disabled{opacity:.28;cursor:default}.inkdos-toolbar-separator{width:1px;height:calc(100% - 16px);min-height:22px;align-self:center;background:var(--line,var(--frame-line,#d7dce2));pointer-events:none}.inkdos-toolbar-rail-host::after{display:none!important}@media(max-width:480px){.inkdos-toolbar-rail{grid-template-columns:30px 1px minmax(0,1fr) 1px 30px}.inkdos-toolbar-arrow{width:30px;min-width:30px;font-size:17px}}`;(document.head||document.documentElement).appendChild(style)}
  const shell=document.createElement('div');shell.className='inkdos-toolbar-rail';
  const left=document.createElement('button'),right=document.createElement('button'),sepL=document.createElement('span'),sepR=document.createElement('span');
  left.type=right.type='button';left.className=right.className='inkdos-toolbar-arrow';sepL.className=sepR.className='inkdos-toolbar-separator';left.textContent='<';right.textContent='>';left.setAttribute('aria-label','Scroll toolbar left');right.setAttribute('aria-label','Scroll toolbar right');
  const parent=target.parentNode;if(!parent)throw new Error('AppFrame.installToolbarRail requires a mounted toolbar');parent.insertBefore(shell,target);shell.append(left,sepL,target,sepR,right);target.classList.add('inkdos-toolbar-scroll');if(parent.classList?.contains('toolstrip-shell'))parent.classList.add('inkdos-toolbar-rail-host');
  function sync(){const max=Math.max(0,target.scrollWidth-target.clientWidth);left.disabled=max<2||target.scrollLeft<=1;right.disabled=max<2||target.scrollLeft>=max-1}
  function move(dir){const amount=Math.max(150,Math.round(target.clientWidth*.62));try{target.scrollBy({left:dir*amount,behavior:'smooth'})}catch(_){target.scrollLeft+=dir*amount}setTimeout(sync,180)}
  left.addEventListener('click',()=>move(-1));right.addEventListener('click',()=>move(1));target.addEventListener('scroll',sync,{passive:true});g.addEventListener('resize',sync,{passive:true});
  if(g.ResizeObserver)new ResizeObserver(sync).observe(target);new MutationObserver(sync).observe(target,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class','style']});requestAnimationFrame(sync);return true
}
configureOptionalHome();
NS.AppFrame=Object.freeze({centerError,bindDrawer,bindHorizontalScroller,installToolbarRail,configureOptionalHome});
})(globalThis);

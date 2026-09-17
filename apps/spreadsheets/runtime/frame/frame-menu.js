(function(global){'use strict';
const NS=global.InkDOS2Spreadsheets=global.InkDOS2Spreadsheets||{};
function configureOptionalHome(){
 const link=document.querySelector('a[aria-label="Home"]');if(!link)return false;
 let enabled=false;try{enabled=new URLSearchParams(global.location.search).get('suite')==='1'}catch(_){}
 if(enabled){link.hidden=false;link.removeAttribute('aria-hidden');link.removeAttribute('tabindex')}
 else{link.hidden=true;link.setAttribute('aria-hidden','true');link.tabIndex=-1;link.removeAttribute('href')}
 return enabled
}
function bindDrawer({trigger,drawer,backdrop,closeButton,onOpen,onClose}={}){
 if(!trigger||!drawer||!backdrop)throw new Error('FrameDrawer requires trigger, drawer and backdrop.');
 function open(){if(typeof onOpen==='function')onOpen();drawer.hidden=false;backdrop.hidden=false;trigger.setAttribute('aria-expanded','true');requestAnimationFrame(()=>closeButton?.focus?.({preventScroll:true}))}
 function close({restoreFocus=true}={}){drawer.hidden=true;backdrop.hidden=true;trigger.setAttribute('aria-expanded','false');if(typeof onClose==='function')onClose();if(restoreFocus)trigger.focus?.({preventScroll:true})}
 function toggle(){drawer.hidden?open():close()}
 trigger.addEventListener('click',toggle);closeButton?.addEventListener('click',()=>close());backdrop.addEventListener('click',()=>close());
 return Object.freeze({open,close,toggle,get isOpen(){return !drawer.hidden}})
}
function bindPopover({trigger,popover,onOpen,onClose}={}){
 if(!trigger||!popover)throw new Error('FramePopover requires trigger and popover.');
 function position(){popover.hidden=false;const r=trigger.getBoundingClientRect(),margin=12,w=popover.offsetWidth||280;let left=Math.min(innerWidth-margin-w,Math.max(margin,r.left));if(!Number.isFinite(left))left=margin;popover.style.left=left+'px';popover.style.top=Math.min(innerHeight-margin-(popover.offsetHeight||260),r.bottom+8)+'px'}
 function open(){position();trigger.setAttribute('aria-expanded','true');if(typeof onOpen==='function')onOpen()}
 function close(){popover.hidden=true;trigger.setAttribute('aria-expanded','false');if(typeof onClose==='function')onClose()}
 function toggle(){popover.hidden?open():close()}
 trigger.addEventListener('click',toggle);document.addEventListener('pointerdown',e=>{if(!popover.hidden&&!popover.contains(e.target)&&!trigger.contains(e.target))close()});window.addEventListener('resize',()=>{if(!popover.hidden)close()},{passive:true});
 return Object.freeze({open,close,toggle,get isOpen(){return !popover.hidden}})
}
function installToolbarRail(target){
 function install(){
  if(!target||target.closest('.inkdos-toolbar-rail'))return;
  if(!document.getElementById('inkdosToolbarRailStyle')){const style=document.createElement('style');style.id='inkdosToolbarRailStyle';style.textContent=`.inkdos-toolbar-rail{width:100%;min-width:0;display:grid;grid-template-columns:34px 1px minmax(0,1fr) 1px 34px;align-items:stretch;background:var(--chrome,var(--frame-chrome,#fff));border-bottom:1px solid var(--line,var(--frame-line,#d7dce2));position:relative;z-index:30}.inkdos-toolbar-rail>.inkdos-toolbar-scroll{grid-column:3;min-width:0!important;width:100%!important;max-width:none!important;border-bottom:0!important}.inkdos-toolbar-arrow{width:34px;min-width:34px;min-height:44px;padding:0;border:0;border-radius:0;background:transparent;color:var(--muted,var(--frame-muted,#5f6368));font:600 18px/1 Arial,sans-serif;display:grid;place-items:center;cursor:pointer;user-select:none;-webkit-user-select:none}.inkdos-toolbar-arrow:hover:not(:disabled),.inkdos-toolbar-arrow:focus-visible:not(:disabled){background:var(--toolbar-hover,var(--frame-hover,rgba(60,64,67,.08)));color:var(--text,var(--frame-text,#202124));outline:none}.inkdos-toolbar-arrow:disabled{opacity:.28;cursor:default}.inkdos-toolbar-separator{width:1px;height:calc(100% - 16px);min-height:22px;align-self:center;background:var(--line,var(--frame-line,#d7dce2));pointer-events:none}.inkdos-toolbar-rail-host::after{display:none!important}@media(max-width:480px){.inkdos-toolbar-rail{grid-template-columns:30px 1px minmax(0,1fr) 1px 30px}.inkdos-toolbar-arrow{width:30px;min-width:30px;font-size:17px}}`;(document.head||document.documentElement).appendChild(style)}
  const shell=document.createElement('div');shell.className='inkdos-toolbar-rail';
  const left=document.createElement('button'),right=document.createElement('button'),sepL=document.createElement('span'),sepR=document.createElement('span');
  left.type=right.type='button';left.className=right.className='inkdos-toolbar-arrow';sepL.className=sepR.className='inkdos-toolbar-separator';left.textContent='<';right.textContent='>';left.setAttribute('aria-label','Scroll toolbar left');right.setAttribute('aria-label','Scroll toolbar right');
  const parent=target.parentNode;parent.insertBefore(shell,target);shell.append(left,sepL,target,sepR,right);target.classList.add('inkdos-toolbar-scroll');if(parent.classList?.contains('toolstrip-shell'))parent.classList.add('inkdos-toolbar-rail-host');
  function sync(){const max=Math.max(0,target.scrollWidth-target.clientWidth);left.disabled=max<2||target.scrollLeft<=1;right.disabled=max<2||target.scrollLeft>=max-1}
  function move(dir){const amount=Math.max(150,Math.round(target.clientWidth*.62));try{target.scrollBy({left:dir*amount,behavior:'smooth'})}catch(_){target.scrollLeft+=dir*amount}setTimeout(sync,180)}
  left.addEventListener('click',()=>move(-1));right.addEventListener('click',()=>move(1));target.addEventListener('scroll',sync,{passive:true});global.addEventListener('resize',sync,{passive:true});
  if(global.ResizeObserver)new ResizeObserver(sync).observe(target);new MutationObserver(sync).observe(target,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class','style']});requestAnimationFrame(sync);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
}
configureOptionalHome();
NS.FrameUI=Object.freeze({bindDrawer,bindPopover,configureOptionalHome,installToolbarRail});
})(globalThis);

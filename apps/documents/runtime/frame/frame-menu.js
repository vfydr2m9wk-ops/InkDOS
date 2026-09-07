(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
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
configureOptionalHome();
NS.FrameUI=Object.freeze({bindDrawer,bindPopover,configureOptionalHome});
})(globalThis);

(function(g){'use strict';
const NS=g.InkDOS2=g.InkDOS2||{};
function centerError(el){if(!el)return null;const r=el.getBoundingClientRect();return Math.abs((r.left+r.width/2)-g.innerWidth/2)}
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
NS.AppFrame=Object.freeze({centerError,bindDrawer,bindHorizontalScroller});
})(globalThis);

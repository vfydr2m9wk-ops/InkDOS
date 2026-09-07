(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function create({state,editor}={}){const $=id=>document.getElementById(id),rulerState={left:0,first:0,right:0};let syncing=false;
 function track(){return $('ruler')?.querySelector('.ruler-track')||null}
 function update(){ $('leftIndent').style.left=rulerState.left+'px';$('hangingIndent').style.left=rulerState.left+'px';$('firstIndent').style.left=rulerState.first+'px';$('rightIndent').style.right=rulerState.right+'px'}
 function specFor(block){return NS.PageSpec.normalize(block?.closest?.('.doc-page')?._pageSpec||state.currentPageSpec)}
 function syncFromBlock(block){const t=track();if(!t||!block)return false;const rect=t.getBoundingClientRect(),spec=specFor(block),width=Math.max(1,spec.contentWidthPx),scale=rect.width/width,cs=getComputedStyle(block),left=Math.max(0,parseFloat(cs.marginLeft)||0),right=Math.max(0,parseFloat(cs.marginRight)||0),indent=parseFloat(cs.textIndent)||0;rulerState.left=Math.max(0,Math.min(rect.width,left*scale));rulerState.first=Math.max(0,Math.min(rect.width,(left+indent)*scale));rulerState.right=Math.max(0,Math.min(rect.width,right*scale));update();return true}
 function sync(){if(syncing)return;syncing=true;try{const block=editor.currentSelectionBlock();if(block)syncFromBlock(block)}finally{syncing=false}}
 function apply(rect){const b=editor.selectionBlock();if(!b)return;const width=specFor(b).contentWidthPx,px=x=>Math.round(x*(width/Math.max(1,rect.width)));const left=px(rulerState.left),first=px(rulerState.first),right=px(rulerState.right);b.style.marginLeft=left+'px';b.style.textIndent=(first-left)+'px';b.style.marginRight=right+'px';editor.rememberSelection();editor.markDirty()}
 function bind(id,kind){const h=$(id),t=track();let down=false,startX=0,startLeft=0,startFirst=0;h.onpointerdown=e=>{sync();down=true;startX=e.clientX;startLeft=rulerState.left;startFirst=rulerState.first;h.setPointerCapture?.(e.pointerId);e.preventDefault()};h.onpointermove=e=>{if(!down)return;const rect=t.getBoundingClientRect(),max=rect.width,local=Math.max(0,Math.min(max,e.clientX-rect.left));if(kind==='first')rulerState.first=local;else if(kind==='hanging')rulerState.left=local;else if(kind==='left'){const d=e.clientX-startX;rulerState.left=Math.max(0,Math.min(max,startLeft+d));rulerState.first=Math.max(0,Math.min(max,startFirst+d))}else rulerState.right=Math.max(0,Math.min(max,rect.right-e.clientX));update();apply(rect)};h.onpointerup=h.onpointercancel=()=>{down=false;sync()}}
 function install(){update();bind('firstIndent','first');bind('hangingIndent','hanging');bind('leftIndent','left');bind('rightIndent','right');editor.onContextChange(sync);window.addEventListener('resize',sync)}
 return Object.freeze({install,update,sync,syncFromBlock});
}
NS.RulerController=Object.freeze({create});
})(globalThis);

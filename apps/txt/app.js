(function(g){'use strict';
const NS=g.InkDOS2,controls=NS.TxtControls.create(),E=controls.elements;let t1=null,t2=null;
const frameMenu=NS.AppFrame.bindDrawer({trigger:E.menuBtn,drawer:E.menu,backdrop:E.backdrop,closeButton:E.closeMenu,beforeOpen:()=>{controls.closeListMenu();t1?.closeTools();t2?.close()}});NS.AppFrame.bindHorizontalScroller(E.toolbar);
const state=NS.TxtState.create(),editor=NS.TxtEditorController.create({elements:E,state}),files=NS.TxtFileController.create({elements:E,state,editor}),commands=NS.TxtCommands.create({state,editor,files,requestOpen:()=>E.fileInput.click()});
editor.setCheckpointHandler(files.checkpoint);new NS.ContentViewportAdapter(document.querySelector('.content-viewport'),editor.setMetrics);
t2=NS.TxtT2XmlTools.create({elements:E,state,editor,files,beforeOpen:()=>t1?.closeTools()});t2.install();t1=NS.TxtT1Essentials.create({elements:E,state,editor,files,controls,commands});controls.bind({editor,files,state,commands},frameMenu);t1.install();NS.TxtAppDebug=Object.freeze({state,commands,...editor.debug(),...files.debug(),txtT1:t1.debug(),txtT2:t2.debug()});files.initialize();
})(globalThis);

(function(global){'use strict';
function installToolbarRail(){
 const target=document.getElementById('formatbar')||document.getElementById('editbar')||document.getElementById('toolbar');
 if(!target||target.closest('.inkdos-toolbar-rail'))return;
 const style=document.createElement('style');style.id='inkdosToolbarRailStyle';style.textContent=`.inkdos-toolbar-rail{width:100%;min-width:0;display:grid;grid-template-columns:34px 1px minmax(0,1fr) 1px 34px;align-items:stretch;background:var(--chrome,var(--frame-chrome,#fff));border-bottom:1px solid var(--line,var(--frame-line,#d7dce2));position:relative;z-index:30}.inkdos-toolbar-rail>.inkdos-toolbar-scroll{grid-column:3;min-width:0!important;width:100%!important;max-width:none!important;border-bottom:0!important}.inkdos-toolbar-arrow{width:34px;min-width:34px;min-height:44px;padding:0;border:0;border-radius:0;background:transparent;color:var(--muted,var(--frame-muted,#5f6368));font:600 18px/1 Arial,sans-serif;display:grid;place-items:center;cursor:pointer;user-select:none;-webkit-user-select:none}.inkdos-toolbar-arrow:hover:not(:disabled),.inkdos-toolbar-arrow:focus-visible:not(:disabled){background:var(--toolbar-hover,var(--frame-hover,rgba(60,64,67,.08)));color:var(--text,var(--frame-text,#202124));outline:none}.inkdos-toolbar-arrow:disabled{opacity:.28;cursor:default}.inkdos-toolbar-separator{width:1px;height:calc(100% - 16px);min-height:22px;align-self:center;background:var(--line,var(--frame-line,#d7dce2));pointer-events:none}.inkdos-toolbar-rail-host::after{display:none!important}@media(max-width:480px){.inkdos-toolbar-rail{grid-template-columns:30px 1px minmax(0,1fr) 1px 30px}.inkdos-toolbar-arrow{width:30px;min-width:30px;font-size:17px}}`;(document.head||document.documentElement).appendChild(style);
 const shell=document.createElement('div');shell.className='inkdos-toolbar-rail';
 const left=document.createElement('button'),right=document.createElement('button'),sepL=document.createElement('span'),sepR=document.createElement('span');
 left.type=right.type='button';left.className=right.className='inkdos-toolbar-arrow';sepL.className=sepR.className='inkdos-toolbar-separator';left.textContent='<';right.textContent='>';left.setAttribute('aria-label','Scroll toolbar left');right.setAttribute('aria-label','Scroll toolbar right');
 const parent=target.parentNode;parent.insertBefore(shell,target);shell.append(left,sepL,target,sepR,right);target.classList.add('inkdos-toolbar-scroll');if(parent.classList?.contains('toolstrip-shell'))parent.classList.add('inkdos-toolbar-rail-host');
 function sync(){const max=Math.max(0,target.scrollWidth-target.clientWidth);left.disabled=max<2||target.scrollLeft<=1;right.disabled=max<2||target.scrollLeft>=max-1}
 function move(dir){const amount=Math.max(150,Math.round(target.clientWidth*.62));try{target.scrollBy({left:dir*amount,behavior:'smooth'})}catch(_){target.scrollLeft+=dir*amount}setTimeout(sync,180)}
 left.addEventListener('click',()=>move(-1));right.addEventListener('click',()=>move(1));target.addEventListener('scroll',sync,{passive:true});global.addEventListener('resize',sync,{passive:true});
 if(global.ResizeObserver)new ResizeObserver(sync).observe(target);new MutationObserver(sync).observe(target,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class','style']});requestAnimationFrame(sync);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installToolbarRail,{once:true});else installToolbarRail();
})(globalThis);

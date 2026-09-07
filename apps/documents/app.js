(function(global){'use strict';
const NS=global.InkDOS2Documents;if(!NS)throw new Error('Documents runtime namespace missing.');
const $=id=>document.getElementById(id);
function loadScript(src,test){if(test?.())return Promise.resolve();return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(new Error('DOCUMENTS_LOCAL_ASSET_LOAD_FAILED: '+src));document.head.appendChild(s)})}
function loadCss(href,key){if(document.querySelector('link[data-doc-'+key+']'))return;const l=document.createElement('link');l.rel='stylesheet';l.href=href;l.dataset['doc'+key.toUpperCase()]='1';document.head.appendChild(l)}
async function loadD1(){loadCss('ui/d1-tools.css','d1');await loadScript('engine/d1-docx-extension.js',()=>!!NS.D1DocxExtension);await loadScript('ui/d1-tools.js',()=>!!NS.D1Tools)}
async function loadD2(){loadCss('ui/d2-tools.css','d2');await loadScript('engine/d2-docx-extension.js',()=>!!NS.D2DocxExtension);await loadScript('ui/d2-tools.js',()=>!!NS.D2Tools)}
async function boot(){await loadD1();await loadD2();
const session=new NS.DocumentSession();
const state=new NS.DocumentState(session);
const viewport=$('viewport'),pagesHost=$('pagesHost'),welcome=$('welcome'),fileInput=$('fileInput');
const adapter=new NS.ContentViewportAdapter(viewport,pagesHost);
let zoomControls=null;
const zoom=new NS.ZoomController(adapter,pagesHost,info=>zoomControls?.update(info));
const navigation=NS.NavigationPanel.create({pagesHost});
const chrome=NS.ChromeController.create({session});
const sessionDialog=NS.SessionDialog.create();
const surface=NS.PageSurface.create({state,session,viewport,pagesHost,welcome,zoom,navigation});
const editor=NS.EditorController.create({state,session,pagesHost,surface,chrome,zoom});
const ruler=NS.RulerController.create({state,editor});
const fileOpen=NS.FileOpenController.create({state,session,fileInput,pagesHost,chrome,surface,editor,sessionDialog});
const saveController=NS.SaveController.create({session,pagesHost,chrome});
zoomControls=NS.ZoomControls.create({zoom});
const commands=NS.CommandController.create({session,pagesHost,chrome,fileOpen,saveController,editor,ruler,navigation,zoom,zoomControls});
const d1=NS.D1Tools.create({state,session,pagesHost,surface,editor,navigation,chrome});
const d2=NS.D2Tools.create({state,session,pagesHost,surface,editor,navigation,chrome,d1});
chrome.setChooseFile(fileOpen.requestOpen);
NS.Appearance.install();
zoom.install();
fileOpen.install();
commands.install();
d1.install();
d2.install();
chrome.syncDirty();
surface.updateStats();
NS.DocumentsApp=Object.freeze({session,state,zoom,d1,d2,open:fileOpen.openFile,requestOpen:fileOpen.requestOpen,newDocument:fileOpen.requestNew,save:saveController.save});
}
boot().catch(e=>{console.error(e);const status=$('statusText');if(status)status.textContent='Documents tools failed to load'});
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

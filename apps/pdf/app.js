(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{},$=id=>document.getElementById(id);
function loadReaderTools(){if(NS.ReaderTools)return Promise.resolve();return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='ui/reader-tools.js';s.onload=resolve;s.onerror=()=>reject(new Error('PDF_READER_TOOLS_LOAD_FAILED'));document.head.appendChild(s)})}
async function boot(){await loadReaderTools();NS.PdfWorker.configure();
const session=new NS.PdfSession();
const chrome=NS.ChromeController.create({session});
const scheduler=new NS.PageScheduler(9);
let commands=null,readerTools=null,pageTools=null;
const editor=new NS.PdfjsEditorAdapter({container:$('contentViewport'),viewer:$('pdfStack'),session,chrome,onState:()=>commands?.syncEditor()});
const pageLayers=new NS.PdfjsPageLayers({editor});
const extensions=new NS.ReviewAnnotations({editor,session,chrome});
const layout=new NS.PageLayout({viewport:$('contentViewport'),stack:$('pdfStack'),onPageChange:n=>commands?.syncPage(),onScaleChange:s=>editor.setScale(s),onPageRendered:async info=>{await pageLayers.onPageRendered(info);extensions.onPageRendered(info)},onPageUnmount:n=>{extensions.onPageUnmount(n);pageLayers.onPageUnmount(n)}});
const adapter=new NS.ContentViewportAdapter($('contentViewport'),m=>layout.setMetrics(m));
const zoom=new NS.ZoomController(layout,()=>{});
const zoomControls=NS.ZoomControls.create({zoom,select:$('zoomSelect')});
const navigation=NS.NavigationController.create({layout,chrome});
const modeController=NS.ModeController.create({editor,extensions,pageLayers,chrome});
const fileOpen=NS.FileOpenController.create({session,fileInput:$('fileInput'),scheduler,layout,chrome,
  prepareToReplace:()=>{editor.commit();return editor.doc?.annotationStorage.serializable.hash},canReplace:()=>!save.saving,
  onBeforeReplace:async()=>{readerTools?.resetDocument();pageTools?.resetDocument();layout.clearDocument();extensions.setDocument(null);pageLayers.setDocument(null);navigation.close()},
  onDocumentOpened:async info=>{pageLayers.setDocument(info.pdfDocument);extensions.setDocument(info.pdfDocument);await navigation.setDocument(info.pdfDocument,info.pageCount);modeController.setMode('view');readerTools?.resetDocument();readerTools?.syncEnabled();pageTools?.resetDocument();pageTools?.syncEnabled()}
});
const save=NS.SaveController.create({session,getDocument:()=>fileOpen.pdfDocument,editor,chrome});
readerTools=NS.ReaderTools.create({session,getDocument:()=>fileOpen.pdfDocument,layout,chrome});
pageTools=NS.PageTools.create({session,getDocument:()=>fileOpen.pdfDocument,fileOpen,editor,chrome,layout,navigation});
commands=NS.CommandController.create({session,chrome,fileOpen,save,layout,editor,navigation,modeController,readerTools,pageTools});
NS.Appearance.install();
fileOpen.install();
zoomControls.install();
navigation.install();
extensions.install();
modeController.install();
readerTools.install();
pageTools.install();
commands.install();
global.addEventListener('beforeunload',e=>{editor.commit();if(session.dirty){e.preventDefault();e.returnValue=''}});
adapter.measure();
chrome.title();chrome.dirty();chrome.page(1,0);
NS.ReaderCompletionDebug=Object.freeze({readerTools,pageTools,layout});
}
boot().catch(e=>{console.error(e);const status=$('statusText');if(status)status.textContent='Reader tools failed to load'});
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

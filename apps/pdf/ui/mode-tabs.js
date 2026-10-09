(function(global){'use strict';
// PDF workspace, two bars: this top bar chooses what to do (View, Annotate, Edit PDF) and the toolbar
// below shows that task's tools. The existing editing switch (#editModeBtn) moves into this bar as Annotate
// (form fields are filled there too). Edit PDF frames the BentoPDF toolkit of InkDOS-tools (its own
// origin, AGENTS.md origin isolation) over the workspace and hands it the open PDF through the viewer protocol
// (InkDOS-tools viewers/viewer-embed.js + bento-carry.js): every message checked against, and sent to, that origin.
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
const TOOLS_ORIGIN='https://inkdos-offic.pages.dev',TOOLKIT=TOOLS_ORIGIN+'/InkDOS-tools/bentopdf/';
const doc=document,root=doc.documentElement,$=id=>doc.getElementById(id);
const pt=()=>/^pt/i.test(String(global.InkDOSLocalization?.currentLanguage||root.lang||global.navigator.language||''));
const LABELS={view:['Visualizar','View'],annotate:['Anotar','Annotate'],edit:['Editar PDF','Edit PDF'],back:['Voltar ao PDF','Back to the PDF'],open:['Abra um PDF primeiro.','Open a PDF first.']};
const label=k=>LABELS[k][pt()?0:1];
const desktop=()=>!!global.InkDOSDesktop||root.dataset.inkdosHost==='tauri';
function debug(){return NS.PdfStabilityDebug||null}
function editing(){return $('editModeBtn')?.getAttribute('aria-pressed')==='true'}
function hasDocument(){const b=$('editModeBtn');return !!b&&b.dataset.editState!=='empty'}
function whenEditing(fn){const b=$('editModeBtn');if(!b)return;if(editing())return fn();if(b.disabled)return;b.click();let n=0;(function wait(){if(editing())return fn();if(++n<100)setTimeout(wait,100)})()}
function css(){const s=doc.createElement('style');s.textContent=
 // one more row for this bar in the app grid; the tools below wrap onto a second line instead of scrolling behind side
 // arrows (cut off on iPad)
 '.app-shell{grid-template-rows:auto auto auto minmax(0,1fr) auto!important}.inkdos-toolbar-rail{display:block!important}.inkdos-toolbar-rail>.inkdos-toolbar-arrow,.inkdos-toolbar-rail>.inkdos-toolbar-separator{display:none!important}.inkdos-toolbar-rail>.inkdos-toolbar-scroll{grid-column:1!important}'+
 '#editbar.editbar{height:auto!important;min-height:44px;flex-wrap:wrap!important;overflow:visible!important;justify-content:center;align-content:flex-start;row-gap:4px;padding-top:6px!important;padding-bottom:6px!important}#editbar.editbar>*{min-height:0!important;height:auto!important}'+
 '.pdf-task-bar{display:flex;gap:6px;align-items:center;overflow-x:auto;white-space:nowrap;padding:6px calc(var(--safe-r,0px) + 12px) 6px calc(var(--safe-l,0px) + 12px);background:var(--chrome);border-bottom:1px solid var(--line);scrollbar-width:none}'+
 '.pdf-task-bar button{height:32px;padding:0 14px;border:1px solid transparent;border-radius:9px;background:transparent;color:var(--muted,inherit);font:inherit;font-size:13px;font-weight:600;cursor:pointer}'+
 '.pdf-task-bar button[data-current]{background:var(--surface,#fff);border-color:var(--line);color:var(--text,inherit);box-shadow:0 1px 3px rgba(31,45,61,.1)}'+
 '.pdf-task-bar button:disabled{opacity:.45;cursor:default}'+
 '#pdfTaskBar #editModeBtn svg,#pdfTaskBar #editModeLabel{display:none}#pdfTaskBar #editModeBtn{width:auto;min-width:0}'+
 '.pdf-toolkit-layer{position:fixed;inset:0;z-index:2147483646;display:flex;flex-direction:column;background:var(--bg,#f2f5f8)}'+
 '.pdf-toolkit-layer>div{display:flex;align-items:center;gap:10px;padding:6px 10px;background:var(--chrome,#fff);border-bottom:1px solid var(--line,#e3e8ef);font-weight:600;font-size:13px}'+
 '.pdf-toolkit-layer>div span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'+
 '.pdf-toolkit-layer>div button{height:32px;padding:0 12px;border:1px solid var(--line,#d5dce6);border-radius:9px;background:var(--surface,#f0f2f5);color:inherit;font:inherit;cursor:pointer}'+
 '.pdf-toolkit-layer iframe{flex:1;width:100%;border:0;background:#fff}';
 doc.head.appendChild(s)}
let bar=null,task='view',pending=null;
function setTask(next){task=next;pending=null;root.dataset.pdfTask=next;delete root.dataset.pdfSigning;for(const b of bar.querySelectorAll('[data-task]')){const on=b.dataset.task===next;b.toggleAttribute('data-current',on);if(b.id!=='editModeBtn')b.setAttribute('aria-pressed',String(on))}}
function choose(next){
 const modes=debug()?.modeController;
 if(next==='edit')return openToolkit();
 if(next==='view'){if(editing())$('editModeBtn').click();return setTask('view')}
 if(!hasDocument()){status(label("open"));return}
 pending=next;whenEditing(()=>{modes?.setTool('select');setTask(next)});
}
function status(text){try{debug()?.commands?.chrome?.status?.(text)}catch(_){}const live=$('statusText')||$('pdfStatus');if(live)live.textContent=text}
function currentFile(){const s=debug()?.session;if(!s?.sourceBytes)return null;const name=String(s.fileName||'document.pdf');return new File([s.sourceBytes],/\.pdf$/i.test(name)?name:name+'.pdf',{type:'application/pdf'})}
function openToolkit(){
 const file=currentFile();if(!file){status(label('open'));return}
 const layer=doc.createElement('div');layer.className='pdf-toolkit-layer';layer.setAttribute('role','dialog');layer.setAttribute('aria-label','BentoPDF');
 const head=doc.createElement('div'),title=doc.createElement('span'),back=doc.createElement('button');
 title.textContent='BentoPDF · '+file.name;back.type='button';back.textContent=label('back');head.append(title,back);
 const frame=doc.createElement('iframe');frame.title='BentoPDF';
 const url=new URL(TOOLKIT);url.searchParams.set('embed','1');url.searchParams.set('inkdos-theme',root.dataset.theme==='dark'?'dark':'light');frame.src=url.href;
 layer.append(head,frame);doc.body.appendChild(layer);
 let sent=false;
 const onMessage=event=>{if(event.origin!==TOOLS_ORIGIN||event.source!==frame.contentWindow)return;if(event.data?.type==='inkdos-viewer-ready'&&!sent){sent=true;frame.contentWindow.postMessage({type:'inkdos-viewer-open',file},TOOLS_ORIGIN)}};
 global.addEventListener('message',onMessage);
 back.addEventListener('click',()=>{global.removeEventListener('message',onMessage);layer.remove()});
}
function install(){
 const editbar=$('editbar');if(!editbar||$('pdfTaskBar'))return;css();
 bar=doc.createElement('div');bar.id='pdfTaskBar';bar.className='pdf-task-bar';bar.setAttribute('role','toolbar');bar.setAttribute('aria-label',pt()?'Tarefa no PDF':'PDF task');
 const edit=$('editModeBtn');
 for(const k of ['view','annotate','edit']){
  if(k==='edit'&&desktop())continue;
  if(k==='annotate'&&edit){edit.dataset.task='annotate';const t=doc.createElement('span');t.className='pdf-task-label';t.textContent=label('annotate');edit.appendChild(t);bar.appendChild(edit);continue}
  const b=doc.createElement('button');b.type='button';b.dataset.task=k;b.textContent=label(k);b.setAttribute('aria-pressed',String(k==='view'));b.addEventListener('click',()=>choose(k));bar.appendChild(b)}
 // Annotate while already editing: switch the task, do not finish editing
 bar.addEventListener('click',e=>{if(e.target.closest('#editModeBtn')&&editing()&&task!=='annotate'){e.stopPropagation();e.preventDefault();debug()?.modeController?.setTool('select');setTask('annotate')}},true);
 editbar.parentNode.insertBefore(bar,editbar);
 // keep the bar in step with the editing switch (a document closed or opened elsewhere)
 if(edit)new MutationObserver(()=>{const empty=!hasDocument();for(const b of bar.querySelectorAll('[data-task]'))if(b.dataset.task!=='view'&&b.id!=='editModeBtn')b.disabled=empty;if(!editing()&&task!=='view')setTask('view');else if(editing()&&task==='view')setTask(pending||'annotate')}).observe(edit,{attributes:true,attributeFilter:['aria-pressed','data-edit-state']});
 for(const b of bar.querySelectorAll('[data-task]'))if(b.dataset.task!=='view'&&b.id!=='editModeBtn')b.disabled=!hasDocument();
 setTask('view');
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',()=>setTimeout(install,0),{once:true});else setTimeout(install,0);
NS.PdfTaskBar=Object.freeze({choose,get task(){return task}});
})(globalThis);

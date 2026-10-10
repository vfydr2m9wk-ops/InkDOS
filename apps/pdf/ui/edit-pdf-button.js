(function(global){'use strict';
// PDF workspace: Edit PDF, a header button left of Settings (sun) like Edit with ONLYOFFICE in the office apps. The
// tool bar stays the single 2.8 bar. The button frames the BentoPDF toolkit of InkDOS-tools (its own origin, AGENTS.md
// origin isolation) over the workspace and hands it the open PDF through the viewer protocol (InkDOS-tools
// viewers/viewer-embed.js + bento-carry.js): every message checked against, and sent to, that origin.
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
const TOOLS_ORIGIN='https://inkdos-tools.github.io',TOOLKIT=TOOLS_ORIGIN+'/InkDOS-tools/bentopdf/';
// BentoPDF pages opened with the current PDF from the Security (lock) menu
const PAGES={protect:'encrypt-pdf.html',unprotect:'decrypt-pdf.html'};
const doc=document,root=doc.documentElement,$=id=>doc.getElementById(id);
const pt=()=>/^pt/i.test(String(global.InkDOSLocalization?.currentLanguage||root.lang||global.navigator.language||''));
const LABELS={edit:['Editar PDF','Edit PDF'],section:['Senha do PDF','PDF password'],protect:['Proteger com senha','Protect with password'],unprotect:['Remover senha','Remove password'],back:['Voltar ao PDF','Back to the PDF'],open:['Abra um PDF primeiro.','Open a PDF first.']};
const label=k=>LABELS[k][pt()?0:1];
const desktop=()=>!!global.InkDOSDesktop||root.dataset.inkdosHost==='tauri';
function debug(){return NS.PdfStabilityDebug||null}
function status(text){try{debug()?.commands?.chrome?.status?.(text)}catch(_){}const live=$('statusText')||$('pdfStatus');if(live)live.textContent=text}
function currentFile(){const s=debug()?.session;if(!s?.sourceBytes)return null;const name=String(s.fileName||'document.pdf');return new File([s.sourceBytes],/\.pdf$/i.test(name)?name:name+'.pdf',{type:'application/pdf'})}
function css(){if($('pdfEditBtnStyle'))return;const s=doc.createElement('style');s.id='pdfEditBtnStyle';s.textContent=
 '#pdfEditBtn{width:auto;min-width:0;padding:0 10px;display:inline-flex;align-items:center;white-space:nowrap;font:inherit;font-size:13px;font-weight:600}'+
 '@media (max-width:640px){#pdfEditBtn{padding:0 6px;font-size:12px}}'+
 '.pdf-toolkit-layer{position:fixed;inset:0;z-index:2147483646;display:flex;flex-direction:column;background:var(--bg,#f2f5f8);color:var(--text,#192235)}'+
 '.pdf-toolkit-layer>.pdf-toolkit-head{display:flex;align-items:center;gap:10px;padding:6px 10px;background:var(--chrome,#fff);border-bottom:1px solid var(--line,#e3e8ef);font-weight:600;font-size:13px}'+
 '.pdf-toolkit-head span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'+
 '.pdf-toolkit-head button{height:32px;padding:0 12px;border:1px solid var(--line,#d5dce6);border-radius:9px;background:var(--control-bg,var(--panel,#f0f2f5));color:var(--control-fg,var(--text,#192235));font:inherit;cursor:pointer}'+
 '.pdf-toolkit-body{position:relative;flex:1 1 auto;min-height:0;overflow:auto;-webkit-overflow-scrolling:touch}'+
 '.pdf-toolkit-body iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#fff}';
 doc.head.appendChild(s)}
function openToolkit(page){
 const file=currentFile();if(!file){status(label('open'));return}
 // the toolkit opens as a page of its own, with no white frame over the workspace (owner, 2026-10-10); the PDF goes
 // through runtime/platform/file-launch.js and the browser's Back returns here
 const launch=global.InkDOSFileLaunch;
 if(launch?.handOff&&global.indexedDB){launch.handOff(file,new URL(typeof page==='string'?page:'',TOOLKIT)).catch(error=>{console.error('InkDOS: could not hand the PDF to BentoPDF',error);status(label('open'))});return}
 const layer=doc.createElement('div');layer.className='pdf-toolkit-layer';layer.setAttribute('role','dialog');layer.setAttribute('aria-label','BentoPDF');
 const head=doc.createElement('div'),body=doc.createElement('div'),title=doc.createElement('span'),back=doc.createElement('button');
 title.textContent='BentoPDF · '+file.name;back.type='button';back.textContent=label('back');head.append(title,back);
 const frame=doc.createElement('iframe');frame.title='BentoPDF';
 const url=new URL(typeof page==='string'?page:'',TOOLKIT);url.searchParams.set('embed','1');url.searchParams.set('inkdos-theme',root.dataset.theme==='dark'?'dark':'light');frame.src=url.href;
 head.className='pdf-toolkit-head';body.className='pdf-toolkit-body';body.appendChild(frame);layer.append(head,body);doc.body.appendChild(layer);
 let sent=false;
 const onMessage=event=>{if(event.origin!==TOOLS_ORIGIN||event.source!==frame.contentWindow)return;if(event.data?.type==='inkdos-viewer-ready'&&!sent){sent=true;frame.contentWindow.postMessage({type:'inkdos-viewer-open',file},TOOLS_ORIGIN)}};
 global.addEventListener('message',onMessage);
 back.addEventListener('click',()=>{global.removeEventListener('message',onMessage);layer.remove()});
}
function installHeaderButton(){
 if(desktop()||$('pdfEditBtn'))return;
 const find=()=>doc.querySelector('[data-frame-action="sun"]'),sun=find();
 if(sun)return addHeaderButton(sun);
 // joins the header in the same moment as the sun, so the sun never moves under a finger
 const watch=new MutationObserver(()=>{const s=find();if(s){watch.disconnect();if(!$('pdfEditBtn'))addHeaderButton(s)}});
 watch.observe(doc.documentElement,{childList:true,subtree:true});setTimeout(()=>watch.disconnect(),15000);
}
function addHeaderButton(sun){
 css();const b=doc.createElement('button');b.type='button';b.id='pdfEditBtn';b.className='frame-btn inkdos-office-btn';
 b.textContent=label('edit');b.title=label('edit')+' (BentoPDF)';b.setAttribute('aria-label',label('edit'));b.addEventListener('click',()=>openToolkit());
 sun.parentNode.insertBefore(b,sun);
}
installHeaderButton();
// Security (lock): protect the open PDF with a password, or remove one the user knows (BentoPDF, encrypted there)
if(!desktop())global.InkDOSSecurityExtras=[...(global.InkDOSSecurityExtras||[]),...['protect','unprotect'].map(k=>({get section(){return label('section')},get label(){return label(k)},value:'pdf-'+k,run:()=>openToolkit(PAGES[k])}))];
NS.PdfEditButton=Object.freeze({open:openToolkit});
})(globalThis);

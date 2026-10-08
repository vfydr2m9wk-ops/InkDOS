(function(global){'use strict';
// PDF tools (beta, web edition) in a panel over the workspace: the open PDF stays open underneath,
// is handed to the tools page (shared/localization/settings-strip.js message bridge) and a result
// comes straight back here. The frame is created on open and removed on close, so nothing the tools
// held (certificates, passwords) outlives the panel. Hidden in the desktop app (beta channel there).
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
const doc=global.document;
const desktop=()=>!!global.InkDOSDesktop||doc.documentElement.dataset.inkdosHost==='tauri';
let panel=null,frame=null,lastFocus=null;
function build(){
 panel=doc.getElementById('betaToolsPanel');if(!panel)return null;
 doc.getElementById('betaToolsClose')?.addEventListener('click',()=>close());
 doc.addEventListener('keydown',event=>{if(event.key==='Escape'&&isOpen())close()});
 return panel;
}
function isOpen(){return !!(panel&&!panel.hidden)}
function open(){
 if(desktop())return false;
 if(!panel&&!build())return false;
 if(isOpen())return true;
 lastFocus=doc.activeElement;
 frame=doc.createElement('iframe');frame.className='beta-tools-frame';frame.title='PDF tools (beta)';
 frame.src=new URL('../../labs/pdf/index.html?from=app&embed=1',global.location.href).href;
 doc.getElementById('betaToolsBody').replaceChildren(frame);
 panel.hidden=false;doc.getElementById('betaToolsBtn')?.setAttribute('aria-expanded','true');
 doc.getElementById('betaToolsClose')?.focus();
 return true;
}
function close(){
 if(!isOpen())return;
 panel.hidden=true;frame?.remove();frame=null;
 doc.getElementById('betaToolsBtn')?.setAttribute('aria-expanded','false');
 try{lastFocus?.focus?.()}catch(_){}lastFocus=null;
}
function install(){
 const button=doc.getElementById('betaToolsBtn');if(!button)return;
 if(desktop()){button.hidden=true;return}
 // INKDOS:FROZEN-LEGACY legacy-pdf-signer: the signer is no longer offered from the toolbar (its signatures carry
 // no legal validity check a user could rely on); open() and the hand-over bridge stay for its reactivation
 button.hidden=true;button.addEventListener('click',()=>isOpen()?close():open());
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',install,{once:true});else install();
NS.PdfBetaToolsPanel=Object.freeze({open,close,get isOpen(){return isOpen()},get frame(){return frame}});
})(globalThis);

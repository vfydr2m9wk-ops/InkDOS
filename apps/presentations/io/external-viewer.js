(function(global){'use strict';
// View-only presentations InkDOS does not edit (LibreOffice/OpenDocument .odp, Apple Keynote .key):
// an open-source viewer published by InkDOS-tools is embedded in the workspace and the file is
// handed to it locally (postMessage); nothing is uploaded or converted. InkDOS-tools is a separate
// origin on purpose (its third-party code cannot reach InkDOS storage), so every message is
// checked against, and addressed to, that origin only.
// Viewer protocol: InkDOS-tools site-src/viewers/viewer-embed.js.
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
const VIEWERS=Object.freeze([
 {viewer:'odf',ext:['odp'],label:'OpenDocument presentation'},
 {viewer:'pnk',ext:['key'],label:'Apple Keynote'}
]);
const LOAD_TIMEOUT_MS=45000;
function viewerFor(name){const m=/\.([a-z0-9]+)$/i.exec(String(name||''));const ext=m?m[1].toLowerCase():'';return VIEWERS.find(v=>v.ext.includes(ext))||null}
// global.InkDOSToolsBase overrides the published site (local tests serve a stub viewer)
const TOOLS_BASE=String(global.InkDOSToolsBase||'https://inkdos-tools.github.io/InkDOS-tools/'),TOOLS_ORIGIN=new URL(TOOLS_BASE,global.location.href).origin;
function viewerUrl(viewer){const url=new URL(viewer+'/',new URL(TOOLS_BASE,global.location.href));url.searchParams.set('embed','1');url.searchParams.set('inkdos-theme',document.documentElement.dataset.theme==='dark'?'dark':'light');return url.href}
function create({host,cover=[]}={}){
 let box=null,cleanup=null;
 function close(){cleanup?.();cleanup=null;box?.remove();box=null;for(const el of cover)if(el)el.style.display=''}
 // options.viewer names a viewer for a file this table does not list (the PPTX preview of ui/pptx-preview.js)
 function show(file,options={}){
  close();
  const v=options.viewer?{viewer:options.viewer,label:options.label||'Presentation'}:viewerFor(file&&file.name);
  if(!v||!host)return Promise.reject(new Error('This file type has no viewer.'));
  box=document.createElement('div');box.className='external-viewer';box.dataset.viewer=v.viewer;
  box.style.cssText='position:absolute;inset:0;z-index:4;background:var(--bg)';
  const frame=document.createElement('iframe');frame.title=v.label+' (view only)';
  frame.style.cssText='display:block;width:100%;height:100%;border:0;background:transparent';
  // the covered workspace content leaves the layout, so the viewer fills the (scrolling) host
  for(const el of cover)if(el)el.style.display='none';
  if(global.getComputedStyle(host).position==='static')host.style.position='relative';
  return new Promise((resolve,reject)=>{
   let settled=false;
   const finish=(ok,error)=>{if(settled)return;settled=true;clearTimeout(timer);ok?resolve():reject(error)};
   const onMessage=event=>{
    if(event.origin!==TOOLS_ORIGIN||event.source!==frame.contentWindow)return;
    const data=event.data||{};
    if(data.type==='inkdos-viewer-ready')frame.contentWindow.postMessage({type:'inkdos-viewer-open',file},TOOLS_ORIGIN);
    else if(data.type==='inkdos-viewer-loaded')finish(!!data.ok,new Error(data.error||'This file could not be shown.'));
   };
   const timer=setTimeout(()=>finish(false,new Error('The viewer did not load. It is part of the InkDOS web edition and needs a connection the first time it is used.')),LOAD_TIMEOUT_MS);
   global.addEventListener('message',onMessage);
   cleanup=()=>{global.removeEventListener('message',onMessage);finish(false,new Error('closed'))};
   frame.src=viewerUrl(v.viewer);box.appendChild(frame);host.appendChild(box);
  });
 }
 return Object.freeze({show,close,get active(){return !!box}});
}
NS.ExternalViewer=Object.freeze({create,viewerFor,extensions:VIEWERS.flatMap(v=>v.ext)});
})(globalThis);

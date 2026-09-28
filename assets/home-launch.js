(function(global){'use strict';
// Home receives any supported file (web file handling / launchQueue) and hands it to the
// matching workspace, loaded unchanged in a frame. The workspace keeps its own runtime and
// state; Home only routes the file into the workspace's own "Open" input.
const ROUTES=[
 {app:'documents',label:'Documents',ext:['docx','rtf','doc'],mime:['application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/rtf','application/msword']},
 {app:'spreadsheets',label:'Spreadsheets',ext:['xlsx','xls','csv','tsv'],mime:['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.ms-excel','text/csv','text/tab-separated-values']},
 {app:'presentations',label:'Presentations',ext:['pptx','ppt'],mime:['application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.ms-powerpoint']},
 {app:'pdf',label:'PDF',ext:['pdf'],mime:['application/pdf']},
 {app:'epub',label:'EPUB',ext:['epub'],mime:['application/epub+zip']},
 {app:'txt',label:'Plain Text',ext:['txt','md','markdown','log','ini','cfg','conf','toml','properties','xml','json','jsonl','ndjson','yaml','yml'],mime:['text/plain','application/xml','application/json','application/yaml']}
];
function routeFor(file){
 const name=String(file&&file.name||''),dot=name.lastIndexOf('.'),ext=dot>=0?name.slice(dot+1).toLowerCase():'',type=String(file&&file.type||'').toLowerCase();
 return ROUTES.find(r=>ext&&r.ext.includes(ext))||ROUTES.find(r=>type&&r.mime.includes(type))||null;
}
const sessions=[];let host=null,bar=null,active=null,titleTimer=0;
function ensureHost(){
 if(host)return;
 host=document.createElement('div');host.className='home-launch-host';
 bar=document.createElement('div');bar.className='home-launch-tabs';bar.setAttribute('role','tablist');bar.hidden=true;
 host.appendChild(bar);document.body.appendChild(host);document.body.classList.add('home-launching');
}
function select(session){
 active=session;
 for(const s of sessions){const on=s===session;s.frame.hidden=!on;s.tab.setAttribute('aria-selected',on?'true':'false')}
 syncTitle();
}
function syncTitle(){
 try{const t=active&&active.frame.contentDocument&&active.frame.contentDocument.title;if(t)document.title=t}catch(_){}
}
function domReady(){return document.body?Promise.resolve():new Promise(r=>document.addEventListener('DOMContentLoaded',r,{once:true}))}
function wait(ms){return new Promise(r=>setTimeout(r,ms))}
async function waitFor(check,timeout){
 const end=Date.now()+timeout;
 while(Date.now()<end){try{const v=check();if(v)return v}catch(_){}await wait(50)}
 return null;
}
function status(text){
 ensureHost();
 let note=host.querySelector('.home-launch-note');
 if(!note){note=document.createElement('p');note.className='home-launch-note';note.setAttribute('role','status');host.appendChild(note)}
 note.textContent=text;
}
async function openInWorkspace(file){
 await domReady();
 const route=routeFor(file);
 if(!route){status('InkDOS cannot open "'+(file&&file.name||'this file')+'".');return false}
 ensureHost();
 const frame=document.createElement('iframe');
 frame.className='home-launch-frame';frame.title=route.label+' — '+file.name;
 frame.src='./apps/'+route.app+'/index.html';
 const tab=document.createElement('button');
 tab.type='button';tab.className='home-launch-tab';tab.setAttribute('role','tab');tab.textContent=route.label+' · '+file.name;
 const session={frame,tab,route,file};
 tab.addEventListener('click',()=>select(session));
 sessions.push(session);bar.appendChild(tab);bar.hidden=sessions.length<2;
 host.appendChild(frame);select(session);
 await new Promise(r=>frame.addEventListener('load',r,{once:true}));
 const input=await waitFor(()=>frame.contentDocument&&frame.contentDocument.getElementById('fileInput'),20000);
 if(!input){status('The '+route.label+' workspace did not start.');return false}
 await wait(250);
 // Rebuild the file in the workspace's own realm so its readers see native ArrayBuffers.
 const win=frame.contentWindow,local=new win.File([await file.arrayBuffer()],file.name,{type:file.type,lastModified:file.lastModified}),dt=new win.DataTransfer();
 dt.items.add(local);input.files=dt.files;
 input.dispatchEvent(new win.Event('change',{bubbles:true}));
 if(!titleTimer)titleTimer=setInterval(syncTitle,1000);
 return true;
}
async function consume(params){
 const handles=params&&params.files?Array.from(params.files):[];
 for(const handle of handles){
  try{const file=handle&&typeof handle.getFile==='function'?await handle.getFile():handle;if(file)await openInWorkspace(file)}
  catch(e){status('InkDOS could not read the selected file.')}
 }
}
if(global.launchQueue&&typeof global.launchQueue.setConsumer==='function')global.launchQueue.setConsumer(consume);
global.InkDOSHomeLaunch=Object.freeze({routeFor,openInWorkspace,routes:ROUTES.map(r=>Object.freeze({app:r.app,ext:r.ext.slice(),mime:r.mime.slice()}))});
})(globalThis);

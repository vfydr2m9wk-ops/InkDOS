(function(){'use strict';
// Engine switch (Home): Light uses the InkDOS editors and this Home; Full is InkDOS Office, a Home of its own whose
// Word, Excel and PowerPoint cards use the ONLYOFFICE editors (https://github.com/inkdos-tools/inkdos-tools.github.io).
// That suite is third-party code, so it stays on its own origin (AGENTS.md, origin isolation). On the web, choosing
// Full goes to the InkDOS Office Home right away, in this same tab (one page in memory; also where a web desktop such
// as XeOS cannot open new tabs), and this Home sends there while Full is the choice; its "Light version" button comes
// back with ?engine=light. Its service worker keeps each editor on the device after its first use. In the desktop app
// (Full by default) InkDOS Office opens in an office window of its own (inkdos_open_office), whose offline copy stays
// in the app's data folder. Files opened from the system follow the same choice (workspace launch bridges,
// desktop-host.js).
const KEY='inkdos2:engine',OFFICE='https://inkdos-tools.github.io/';
const OFFICE_CARDS=['documents','spreadsheets','presentations'];
const doc=document,root=doc.documentElement;
const NOTES={
  light:'InkDOS editors: light and fast, kept on this device.',
  complete:'ONLYOFFICE editors for Word, Excel and PowerPoint. About 100 MB the first time each one opens, then kept on this device.'
};
let engine='light',cards=[],buttons=[],note=null,offline=null;
// texts are set in English only when they change; the Home localization translates the new text (and a language
// change only refreshes the links, so the two never trigger each other)
const say=(el,text)=>{if(el&&el.dataset.source!==text){el.dataset.source=text;el.textContent=text}};
const desktop=()=>!!window.InkDOSDesktop||root.dataset.inkdosHost==='tauri';
// stored choice; without one, Complete in the desktop app and Light on the web
// ?engine=light|complete (from the InkDOS Office Home) sets the choice, then leaves the address
function fromAddress(){
  try{
    const url=new URL(location.href),v=url.searchParams.get('engine');if(v===null)return;
    if(v==='complete'||v==='light')localStorage.setItem(KEY,v);
    url.searchParams.delete('engine');history.replaceState(history.state,'',url.pathname+url.search+url.hash);
  }catch(_){}
}
function read(){let v=null;try{v=localStorage.getItem(KEY)}catch(_){}return v==='complete'||v==='light'?v:(desktop()?'complete':'light')}
function officeHref(){
  const url=new URL(OFFICE);url.searchParams.set('inkdos-theme',root.dataset.theme==='dark'?'dark':'light');
  const lang=window.InkDOSLocalization?.currentLanguage;if(lang)url.searchParams.set('lang',lang);return url.href;
}
function apply(){
  const complete=engine==='complete';
  root.dataset.inkdosEngine=complete?'complete':'light';
  for(const card of cards){
    if(!card.dataset.lightHref)card.dataset.lightHref=card.getAttribute('href');
    card.setAttribute('href',complete&&!desktop()?officeHref():card.dataset.lightHref); // desktop: see openOffice
  }
  for(const b of buttons)b.setAttribute('aria-pressed',String(b.dataset.engine===engine));
  say(note,NOTES[engine]);
}
// The InkDOS files (and drafts) live in the browser's storage on disk; asking for persistent storage keeps the
// browser from clearing them under storage pressure. The status says whether this browser keeps InkDOS offline.
async function status(ask){
  if(!offline)return;
  if(desktop()){offline.dataset.state='installed';say(offline,'Installed on this computer');return}
  let persisted=false;
  try{if(ask&&navigator.storage?.persist)persisted=await navigator.storage.persist();else if(navigator.storage?.persisted)persisted=await navigator.storage.persisted()}catch(_){}
  const kept=!!(navigator.serviceWorker&&navigator.serviceWorker.controller);
  offline.dataset.state=kept?(persisted?'kept':'cached'):'online';
  say(offline,kept?(persisted?'Saved on this device (offline, kept by the browser)':'Saved on this device (offline)'):'Not saved on this device: this browser loads InkDOS from the internet');
}
// desktop app, Complete: the office start page opens in its own window (no IPC there, see desktop main.rs)
function openOffice(event){
  if(root.dataset.inkdosEngine!=='complete'||!desktop())return;
  const invoke=window.__TAURI__?.core?.invoke;if(typeof invoke!=='function')return;
  event.preventDefault();goFull();
}
// Full: switch the Home itself, now (web: go to the InkDOS Office Home; desktop: open it in its office window)
function goFull(){
  if(!desktop()){location.assign(officeHref());return}
  const invoke=window.__TAURI__?.core?.invoke;if(typeof invoke!=='function')return;
  invoke('inkdos_open_office',{theme:root.dataset.theme==='dark'?'dark':'light',lang:String(window.InkDOSLocalization?.currentLanguage||'')}).catch(error=>console.error('InkDOS could not open the full version:',error));
}
function set(next){
  if(next!=='light'&&next!=='complete')return;
  engine=next;try{localStorage.setItem(KEY,engine)}catch(_){}
  apply();status(true);
  if(engine==='complete')goFull();
}
function install(){
  fromAddress();
  // web, Full chosen: this Home is the Light one, so the InkDOS Office Home takes its place
  if(!desktop()&&read()==='complete'){location.replace(officeHref());return}
  cards=OFFICE_CARDS.map(id=>doc.querySelector('.workspace-grid a.workspace-card.'+id)).filter(Boolean);
  buttons=[...doc.querySelectorAll('[data-engine]')];note=doc.getElementById('engineNote');offline=doc.getElementById('engineOffline');
  engine=read();
  for(const b of buttons)b.addEventListener('click',()=>set(b.dataset.engine));
  // the office link carries the current appearance and language (that origin cannot read them)
  for(const card of cards){const fresh=()=>{if(root.dataset.inkdosEngine==='complete'&&!desktop())card.href=officeHref()};card.addEventListener('pointerdown',fresh);card.addEventListener('focus',fresh);card.addEventListener('click',fresh);card.addEventListener('click',openOffice)}
  addEventListener('storage',event=>{if(event.key===KEY){engine=read();apply()}});
  doc.addEventListener('inkdos:language',()=>{for(const card of cards)if(root.dataset.inkdosEngine==='complete'&&!desktop())card.href=officeHref()});
  apply();
  if(navigator.serviceWorker)navigator.serviceWorker.ready.then(()=>status(false)).catch(()=>{});
  setTimeout(()=>status(false),1500);
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',install,{once:true});else install();
window.InkDOSEngine=Object.freeze({get engine(){return engine},set});
})();

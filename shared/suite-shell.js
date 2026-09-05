(function (global) {
'use strict';
const doc=global.document;
if(!doc)return;
const product=global.InkDOSProduct||{name:'InkDOS',longName:'Ink Desk Offline Suite'};
const state={filter:'all',pendingAppId:null};
function modules(){return global.InkDOSModules||null;
}
function recentService(){return global.InkDOSRecentFiles||null;
}
function router(){return global.InkDOSFileRouter||null;
}
function prepareHome(){doc.body.dataset.inkdosApp='home';
doc.querySelector('.hub-intro')?.remove();
doc.querySelector('.workspace-grid')?.remove();
doc.querySelector('#suiteSidebar')?.remove();
doc.querySelector('.hub-footer nav')?.remove();
const topbar=doc.querySelector('.hub-topbar');
if(topbar){
topbar.dataset.inkdosShellRegion='titlebar';
const oldMenu=topbar.querySelector('[data-suite-action="menu"]');
if(oldMenu)oldMenu.remove();
}const section=doc.querySelector('.recent-section');
if(section){
section.innerHTML=[
'<div class="section-heading"><div><p class="eyebrow">Local. Offline. Private.</p>',
'<h1 id="recentTitle">Recent</h1></div>',
'<button class="recent-clear" type="button" data-recent-clear hidden>Clear recent</button></div>',
'<div class="recent-filters" data-recent-filters aria-label="Filter recent files"></div>',
'<div class="recent-table" data-recent-table>',
'<div class="recent-table-head" aria-hidden="true">',
'<span>Name</span><span>Type</span><span>Modified</span><span></span></div>',
'<ul class="recent-list" data-recent-list aria-live="polite"></ul></div>',
'<div class="recent-empty-state" data-recent-empty hidden><strong>No recent files</strong>',
'<p>Files you open or create in InkDOS will appear here.</p>',
'<button class="suite-action primary recent-open" type="button" data-recent-open>Open file</button></div>',
'<p class="recent-status" data-recent-status role="status" aria-live="polite"></p>',
'<input id="suiteOpenInput" type="file" hidden>'
].join('');
}}
function readRecent(){const service=recentService();
return service?service.list():[];
}
function formatWhen(value){const time=Number(value||0);
if(!time)return'—';
const date=new Date(time),now=new Date();
if(date.toDateString()===now.toDateString())return'Today, '+date.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'});
return date.toLocaleDateString(undefined,{day:'2-digit',month:'short',year:date.getFullYear()===now.getFullYear()?undefined:'numeric'});
}
function setStatus(message){const target=doc.querySelector('[data-recent-status]');
if(target)target.textContent=String(message||'');
}
function setInputAccept(appId){const input=doc.querySelector('#suiteOpenInput'),runtime=modules();
if(input&&runtime)input.accept=appId?runtime.buildAcceptFor(appId):runtime.buildAccept();
}
const recentFilterAccents=Object.freeze({
all:'#757575',
documents:'#2e6fed',
spreadsheets:'#2a854c',
presentations:'#cf4723',
pdf:'#e12c1e',
txt:'#93700e',
epub:'#8163cb'
});
function makeFilter(id,label){const button=doc.createElement('button');
button.type='button';
button.className='recent-filter';
button.dataset.recentFilter=id;
button.textContent=label;
button.style.setProperty('--recent-filter-accent',recentFilterAccents[id]||recentFilterAccents.all);
button.setAttribute('aria-pressed',id===state.filter?'true':'false');
button.addEventListener('click',()=>{state.filter=id;
renderFilters();
renderRecent();
});
return button;
}
function renderFilters(){const target=doc.querySelector('[data-recent-filters]'),runtime=modules();
if(!target)return;
target.replaceChildren(makeFilter('all','All'));
if(runtime)runtime.listEnabled().forEach(module=>target.appendChild(makeFilter(module.id,module.shortLabel)));
}
function requestOpen(appId=null){state.pendingAppId=appId;
setInputAccept(appId);
doc.querySelector('#suiteOpenInput')?.click();
}
async function open(file){const route=router().routeForFile(file),service=recentService();
if(service)await service.registerOpened(file,route.appId);
return router().openFromHub(file);
}
async function reopen(item){const service=recentService();
if(!service)return;
const resolved=await service.resolveFile(item.id);
if(resolved.available&&resolved.file){await open(resolved.file);
return;
}const runtime=modules(),module=runtime&&runtime.get(item.appId);
setStatus('“'+item.name+'” is no longer directly available. Select it again'+(module?' for '+module.label:'')+'.');
requestOpen(item.appId);
}
function appIcon(module){const span=doc.createElement('span');
span.className='recent-app-icon';
span.style.setProperty('--app-accent',module?module.accent:'#6b7280');
if(module&&module.icon){const image=doc.createElement('img');
image.src='./'+module.icon.replace(/^\.\//,'');
image.alt='';
span.appendChild(image);
}return span;
}
function makeRow(item){const runtime=modules(),module=runtime&&runtime.get(item.appId),row=doc.createElement('li');
row.className='recent-row';
const openButton=doc.createElement('button');
openButton.type='button';
openButton.className='recent-file-button';
openButton.setAttribute('aria-label','Open '+item.name);
const copy=doc.createElement('span'),name=doc.createElement('strong'),meta=doc.createElement('small');
copy.className='recent-file-copy';
name.textContent=item.name;
meta.textContent=formatWhen(item.lastOpened);
copy.append(name,meta);
openButton.append(appIcon(module),copy);
openButton.addEventListener('click',()=>reopen(item).catch(error=>setStatus(error.message||'Could not reopen file.')));
const type=doc.createElement('span');
type.className='recent-type';
type.textContent=item.extension.toUpperCase();
const modified=doc.createElement('time');
modified.className='recent-modified';
modified.textContent=formatWhen(item.lastOpened);
const more=doc.createElement('button');
more.type='button';
more.className='recent-more';
more.textContent='⋯';
more.setAttribute('aria-label','Remove '+item.name+' from Recent');
more.addEventListener('click',async()=>{await recentService().remove(item.id);
renderRecent();
});
const actions=doc.createElement('div');
actions.className='recent-actions';
actions.appendChild(more);
row.append(openButton,type,modified,actions);
return row;
}
function renderRecent(){const list=doc.querySelector('[data-recent-list]'),empty=doc.querySelector('[data-recent-empty]'),clear=doc.querySelector('[data-recent-clear]'),table=doc.querySelector('[data-recent-table]');
if(!list||!empty||!clear||!table)return;
const all=readRecent(),visible=state.filter==='all'?all:all.filter(item=>item.appId===state.filter);
clear.hidden=all.length===0;
list.replaceChildren();
if(!all.length){empty.hidden=false;
table.hidden=true;
return;
}empty.hidden=true;
table.hidden=false;
if(!visible.length){const row=doc.createElement('li');
row.className='recent-filter-empty';
row.textContent='No recent files in this filter.';
list.appendChild(row);
return;
}visible.forEach(item=>list.appendChild(makeRow(item)));
}
function initInput(){const input=doc.querySelector('#suiteOpenInput');
if(!input)return;
setInputAccept(null);
input.addEventListener('change',async()=>{const file=input.files&&input.files[0];
input.value='';
if(!file)return;
try{const expected=state.pendingAppId;
state.pendingAppId=null;
const runtime=modules(),owner=runtime&&runtime.resolveFile(file);
if(expected&&owner.id!==expected)setStatus('This format belongs to '+owner.label+'. Opening the correct app.');
await open(file);
}catch(error){console.error(error);
setStatus(error&&error.message?error.message:'Unsupported file.');
}finally{setInputAccept(null);
}});
}
function init(){prepareHome();
doc.title=product.name+' — '+product.longName;
doc.querySelectorAll('[data-product-name]').forEach(node=>node.textContent=product.name);
doc.querySelectorAll('[data-product-long-name]').forEach(node=>node.textContent=product.longName);
doc.querySelectorAll('[data-release-badge],[data-release-version]').forEach(node=>node.textContent='v'+product.version);
renderFilters();
renderRecent();
initInput();
doc.querySelector('[data-recent-open]')?.addEventListener('click',()=>requestOpen());
doc.querySelector('[data-recent-clear]')?.addEventListener('click',async()=>{await recentService().clear();
state.filter='all';
renderFilters();
renderRecent();
});
global.addEventListener('inkdos:recent-files-changed',renderRecent);
if(global.InkDOSAppShell&&global.InkDOSAppShell.refreshTriggers)global.InkDOSAppShell.refreshTriggers();
}
global.InkDOSSuite=Object.freeze({product,open,readRecent,renderRecent,setFilter(value){state.filter=String(value||'all');
renderFilters();
renderRecent();
},clearRecent(){return recentService()?recentService().clear():Promise.resolve();
}});
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});
else init();
})(typeof window!=='undefined'?window:globalThis);

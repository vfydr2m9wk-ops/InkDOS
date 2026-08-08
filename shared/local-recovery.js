(function(global){
'use strict';

const DB_NAME='InkDeskLocalRecovery';
const DB_VERSION=1;
const SNAPSHOT_STORE='snapshots';
const SOURCE_STORE='sources';
const MAX_PER_DOCUMENT=3;
const MAX_PER_MODULE=12;
const MAX_AGE_MS=30*24*60*60*1000;
const DEFAULT_DEBOUNCE_MS=900;

function requestResult(request){
  return new Promise((resolve,reject)=>{
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error||new Error('IndexedDB request failed.'));
  });
}
function transactionDone(transaction){
  return new Promise((resolve,reject)=>{
    transaction.oncomplete=()=>resolve();
    transaction.onerror=()=>reject(transaction.error||new Error('IndexedDB transaction failed.'));
    transaction.onabort=()=>reject(transaction.error||new Error('IndexedDB transaction was aborted.'));
  });
}
function openDatabase(){
  if(!global.indexedDB)return Promise.reject(new Error('IndexedDB is not available in this browser context.'));
  return new Promise((resolve,reject)=>{
    const request=global.indexedDB.open(DB_NAME,DB_VERSION);
    request.onupgradeneeded=()=>{
      const db=request.result;
      if(!db.objectStoreNames.contains(SNAPSHOT_STORE)){
        const store=db.createObjectStore(SNAPSHOT_STORE,{keyPath:'id'});
        store.createIndex('module','module',{unique:false});
        store.createIndex('documentKey','documentKey',{unique:false});
        store.createIndex('updatedAt','updatedAt',{unique:false});
      }
      if(!db.objectStoreNames.contains(SOURCE_STORE)){
        const store=db.createObjectStore(SOURCE_STORE,{keyPath:'id'});
        store.createIndex('module','module',{unique:false});
        store.createIndex('documentKey','documentKey',{unique:false});
      }
    };
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error||new Error('Could not open the recovery database.'));
    request.onblocked=()=>reject(new Error('The recovery database is blocked by another InkDesk tab.'));
  });
}
async function withStore(storeName,mode,callback){
  const db=await openDatabase();
  try{
    const transaction=db.transaction(storeName,mode);
    // Register completion handlers before awaiting any IndexedDB request. Some
    // engines can complete a readonly transaction during the callback's await;
    // installing the handlers afterwards would leave this promise unresolved.
    const done=transactionDone(transaction);
    const result=await callback(transaction.objectStore(storeName),transaction);
    await done;
    return result;
  }finally{db.close()}
}
async function allFromIndex(storeName,indexName,value){
  return withStore(storeName,'readonly',async store=>{
    const index=store.index(indexName);
    return requestResult(index.getAll(IDBKeyRange.only(value)));
  });
}
async function getAllSnapshots(moduleName){
  const records=await allFromIndex(SNAPSHOT_STORE,'module',moduleName);
  return records.sort((a,b)=>Number(b.updatedAt||0)-Number(a.updatedAt||0));
}
async function getSource(moduleName,documentKey){
  const id=moduleName+':'+documentKey;
  return withStore(SOURCE_STORE,'readonly',store=>requestResult(store.get(id)));
}
async function putSource(moduleName,documentKey,fileName,data,meta){
  if(data==null)return;
  const record={id:moduleName+':'+documentKey,module:moduleName,documentKey,fileName:fileName||'',data,meta:meta||{},updatedAt:Date.now()};
  await withStore(SOURCE_STORE,'readwrite',store=>{store.put(record)});
}
async function deleteDocument(moduleName,documentKey){
  const snapshots=await allFromIndex(SNAPSHOT_STORE,'documentKey',documentKey);
  await withStore(SNAPSHOT_STORE,'readwrite',store=>{
    snapshots.filter(item=>item.module===moduleName).forEach(item=>store.delete(item.id));
  });
  await withStore(SOURCE_STORE,'readwrite',store=>{store.delete(moduleName+':'+documentKey)});
}
async function deleteSnapshotsOnly(moduleName,documentKey){
  const snapshots=await allFromIndex(SNAPSHOT_STORE,'documentKey',documentKey);
  await withStore(SNAPSHOT_STORE,'readwrite',store=>{
    snapshots.filter(item=>item.module===moduleName).forEach(item=>store.delete(item.id));
  });
}
async function prune(moduleName,documentKey){
  const now=Date.now();
  const moduleSnapshots=await getAllSnapshots(moduleName);
  const expired=moduleSnapshots.filter(item=>now-Number(item.updatedAt||0)>MAX_AGE_MS);
  const documentSnapshots=moduleSnapshots.filter(item=>item.documentKey===documentKey);
  const excessDocument=documentSnapshots.slice(MAX_PER_DOCUMENT);
  const surviving=moduleSnapshots.filter(item=>!expired.some(x=>x.id===item.id)&&!excessDocument.some(x=>x.id===item.id));
  const excessModule=surviving.slice(MAX_PER_MODULE);
  const ids=new Set(expired.concat(excessDocument,excessModule).map(item=>item.id));
  const remaining=moduleSnapshots.filter(item=>!ids.has(item.id));
  if(ids.size)await withStore(SNAPSHOT_STORE,'readwrite',store=>{ids.forEach(id=>store.delete(id))});
  const remainingDocumentKeys=new Set(remaining.map(item=>item.documentKey));
  const sources=await allFromIndex(SOURCE_STORE,'module',moduleName);
  const orphanSources=sources.filter(item=>!remainingDocumentKeys.has(item.documentKey));
  if(orphanSources.length)await withStore(SOURCE_STORE,'readwrite',store=>{orphanSources.forEach(item=>store.delete(item.id))});
}
function randomKey(){
  if(global.crypto&&typeof global.crypto.randomUUID==='function')return global.crypto.randomUUID();
  return Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
}
function formatTimestamp(value){
  try{return new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(value))}
  catch(_){return new Date(value).toLocaleString()}
}
function injectStyles(){
  if(document.querySelector('style[data-inkdesk-local-recovery]'))return;
  const style=document.createElement('style');
  style.dataset.inkdeskLocalRecovery='1';
  style.textContent=`
.inkdesk-recovery-overlay{position:fixed;inset:0;z-index:2147482000;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(7,10,17,.72);backdrop-filter:blur(8px);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#eef2ff}
.inkdesk-recovery-card{width:min(520px,100%);border:1px solid rgba(255,255,255,.18);border-radius:22px;background:linear-gradient(145deg,#202635,#151923);box-shadow:0 24px 80px rgba(0,0,0,.48);padding:24px}
.inkdesk-recovery-kicker{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#9faafc;margin:0 0 10px}
.inkdesk-recovery-card h2{font-size:24px;line-height:1.2;margin:0 0 10px;color:#fff}
.inkdesk-recovery-card p{line-height:1.55;margin:0 0 14px;color:#c9cfdb}
.inkdesk-recovery-meta{display:grid;grid-template-columns:auto 1fr;gap:7px 12px;margin:16px 0 20px;padding:14px;border-radius:14px;background:rgba(255,255,255,.055);font-size:13px}
.inkdesk-recovery-meta span:nth-child(odd){color:#929aac}.inkdesk-recovery-meta strong{overflow-wrap:anywhere;color:#f4f6fb}
.inkdesk-recovery-actions{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:10px}
.inkdesk-recovery-actions button{min-height:42px;border:1px solid rgba(255,255,255,.16);border-radius:12px;padding:0 15px;background:#252b38;color:#f4f6fb;font:inherit;font-weight:700;cursor:pointer}
.inkdesk-recovery-actions button:hover{background:#303747}.inkdesk-recovery-actions .primary{border-color:#6f7df2;background:#5363df}.inkdesk-recovery-actions .danger{color:#ffb4b4}
@media(max-width:560px){.inkdesk-recovery-overlay{align-items:flex-end;padding:12px}.inkdesk-recovery-card{border-radius:22px 22px 14px 14px;padding:20px}.inkdesk-recovery-actions{display:grid;grid-template-columns:1fr}.inkdesk-recovery-actions button{width:100%}}
`;
  document.head.appendChild(style);
}
function makePrompt(record,count,handlers){
  injectStyles();
  const overlay=document.createElement('div');
  overlay.className='inkdesk-recovery-overlay';
  overlay.setAttribute('role','dialog');
  overlay.setAttribute('aria-modal','true');
  overlay.setAttribute('aria-labelledby','inkdeskRecoveryTitle');
  const card=document.createElement('div');card.className='inkdesk-recovery-card';
  const kicker=document.createElement('p');kicker.className='inkdesk-recovery-kicker';kicker.textContent='Local recovery';
  const heading=document.createElement('h2');heading.id='inkdeskRecoveryTitle';heading.textContent='Unsaved work is available';
  const description=document.createElement('p');description.textContent='InkDesk found a private recovery snapshot stored only in this browser. Restoring it does not replace the original file.';
  const meta=document.createElement('div');meta.className='inkdesk-recovery-meta';
  const add=(label,value)=>{const a=document.createElement('span');a.textContent=label;const b=document.createElement('strong');b.textContent=value;meta.append(a,b)};
  add('File',record.fileName||'Untitled');add('Saved locally',formatTimestamp(record.updatedAt));add('Available versions',String(count));
  const actions=document.createElement('div');actions.className='inkdesk-recovery-actions';
  const discard=document.createElement('button');discard.type='button';discard.className='danger';discard.textContent='Discard recovery';
  const normal=document.createElement('button');normal.type='button';normal.textContent='Open normally';
  const restore=document.createElement('button');restore.type='button';restore.className='primary';restore.textContent='Restore';
  actions.append(discard,normal,restore);card.append(kicker,heading,description,meta,actions);overlay.appendChild(card);document.body.appendChild(overlay);
  const close=()=>overlay.remove();
  discard.onclick=async()=>{discard.disabled=normal.disabled=restore.disabled=true;await handlers.discard();close()};
  normal.onclick=()=>{handlers.normal();close()};
  restore.onclick=async()=>{discard.disabled=normal.disabled=restore.disabled=true;restore.textContent='Restoring…';try{await handlers.restore();close()}catch(error){console.error('InkDesk recovery restore failed.',error);restore.textContent='Restore';discard.disabled=normal.disabled=restore.disabled=false;alert('The local recovery snapshot could not be restored. The snapshot remains available.') }};
  requestAnimationFrame(()=>restore.focus());
  return overlay;
}
function create(options){
  options=options||{};
  const moduleName=String(options.module||'workspace');
  const serialize=typeof options.serialize==='function'?options.serialize:async()=>null;
  const restoreCallback=typeof options.restore==='function'?options.restore:async()=>{};
  const status=typeof options.status==='function'?options.status:()=>{};
  const debounceMs=Math.max(250,Number(options.debounceMs)||DEFAULT_DEBOUNCE_MS);
  let documentKey='';
  let fileName=String(options.defaultFileName||'Untitled');
  let dirty=false;
  let revision=0;
  let timer=null;
  let writing=null;
  let destroyed=false;

  function report(message,error){
    try{status(message,error)}catch(statusError){console.warn('Recovery status callback failed.',statusError)}
  }
  async function startDocument(config){
    config=config||{};
    clearTimeout(timer);timer=null;dirty=false;revision=0;
    documentKey=String(config.documentKey||randomKey());
    fileName=String(config.fileName||fileName||'Untitled');
    try{
      if(config.resetSnapshots)await deleteSnapshotsOnly(moduleName,documentKey);
      if(Object.prototype.hasOwnProperty.call(config,'sourceData'))await putSource(moduleName,documentKey,fileName,config.sourceData,config.sourceMeta||{});
    }catch(error){console.warn('InkDesk could not initialize local recovery.',error);report('Local recovery unavailable',error)}
    return documentKey;
  }
  async function flush(){
    if(destroyed||!dirty||!documentKey)return null;
    if(writing)return writing.then(()=>dirty?flush():null);
    const capturedRevision=revision;
    writing=(async()=>{
      try{
        const payload=await serialize();
        if(payload==null)return null;
        const now=Date.now();
        const record={id:moduleName+':'+documentKey+':'+now+':'+Math.random().toString(36).slice(2,7),module:moduleName,documentKey,fileName,appVersion:String(options.appVersion||'0.20.2.20'),schemaVersion:1,createdAt:now,updatedAt:now,payload};
        await withStore(SNAPSHOT_STORE,'readwrite',store=>{store.put(record)});
        await prune(moduleName,documentKey);
        if(revision===capturedRevision)dirty=false;
        report('Recovery snapshot saved locally');
        return record;
      }catch(error){console.warn('InkDesk could not save a local recovery snapshot.',error);report('Local recovery snapshot failed',error);return null}
      finally{
        writing=null;
        if(!destroyed&&dirty&&revision>capturedRevision){
          clearTimeout(timer);timer=setTimeout(()=>{timer=null;flush()},debounceMs);
        }
      }
    })();
    return writing;
  }
  function markDirty(){
    if(destroyed)return;
    revision+=1;dirty=true;clearTimeout(timer);timer=setTimeout(()=>{timer=null;flush()},debounceMs);
  }
  async function markClean(){
    dirty=false;revision=0;clearTimeout(timer);timer=null;
    if(!documentKey)return;
    try{await deleteDocument(moduleName,documentKey);report('Recovery snapshot cleared after save')}
    catch(error){console.warn('InkDesk could not clear the recovery snapshot.',error)}
  }
  async function discardCurrent(){
    dirty=false;revision=0;clearTimeout(timer);timer=null;
    if(documentKey)await deleteDocument(moduleName,documentKey);
  }
  function updateFileName(value){fileName=String(value||fileName||'Untitled')}
  async function promptLatest(){
    if(destroyed)return null;
    try{
      const snapshots=await getAllSnapshots(moduleName);
      if(!snapshots.length)return null;
      const record=snapshots[0];
      const versions=snapshots.filter(item=>item.documentKey===record.documentKey).length;
      return makePrompt(record,versions,{
        normal:()=>report('Recovery snapshot kept for later'),
        discard:async()=>{await deleteDocument(moduleName,record.documentKey);report('Recovery snapshot discarded')},
        restore:async()=>{
          documentKey=record.documentKey;fileName=record.fileName||fileName;revision+=1;dirty=true;
          const source=await getSource(moduleName,record.documentKey);
          await restoreCallback({snapshot:record,source:source||null});
          report('Recovery snapshot restored');
        }
      });
    }catch(error){console.warn('InkDesk could not inspect local recovery snapshots.',error);return null}
  }
  function getState(){return{module:moduleName,documentKey,fileName,dirty,revision,writing:Boolean(writing)}}
  function destroy(){
    destroyed=true;dirty=false;clearTimeout(timer);timer=null;
    document.removeEventListener('visibilitychange',visibilityHandler);
    global.removeEventListener('pagehide',pageHideHandler);
  }
  const visibilityHandler=()=>{if(document.visibilityState==='hidden')flush()};
  const pageHideHandler=()=>{flush()};
  document.addEventListener('visibilitychange',visibilityHandler);
  global.addEventListener('pagehide',pageHideHandler);
  return Object.freeze({startDocument,markDirty,flush,markClean,discardCurrent,updateFileName,promptLatest,getState,destroy});
}
async function clearModule(moduleName){
  const snapshots=await getAllSnapshots(String(moduleName));
  await withStore(SNAPSHOT_STORE,'readwrite',store=>snapshots.forEach(item=>store.delete(item.id)));
  const sources=await allFromIndex(SOURCE_STORE,'module',String(moduleName));
  await withStore(SOURCE_STORE,'readwrite',store=>sources.forEach(item=>store.delete(item.id)));
}

global.InkDeskLocalRecovery=Object.freeze({
  version:'0.20.2.20',
  create,
  openDatabase,
  listSnapshots:getAllSnapshots,
  clearModule,
  constants:Object.freeze({DB_NAME,DB_VERSION,MAX_PER_DOCUMENT,MAX_PER_MODULE,MAX_AGE_MS})
});
})(window);

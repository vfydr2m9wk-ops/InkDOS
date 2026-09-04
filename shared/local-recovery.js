(function(global){
'use strict';
const DB_NAME='Ink'+'DeskLocalRecovery';
const DB_VERSION=1;
const SNAPSHOT_STORE='snapshots';
const SOURCE_STORE='sources';
const MAX_PER_DOCUMENT=3,MAX_PER_MODULE=12;
const MAX_AGE_MS=30*24*60*60*1000;
const SOURCE_ORPHAN_GRACE_MS=MAX_AGE_MS;
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
    request.onblocked=()=>reject(new Error('The recovery database is blocked by another InkDOS tab.'));
  });
}
async function withStore(storeName,mode,callback){
  const db=await openDatabase();
  try{
    const transaction=db.transaction(storeName,mode);
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
function sameSession(item,sessionId){return String(item.sessionId||'')===String(sessionId||'')}
async function deleteSnapshotsOnly(moduleName,documentKey,sessionId){
  const snapshots=await allFromIndex(SNAPSHOT_STORE,'documentKey',documentKey);
  await withStore(SNAPSHOT_STORE,'readwrite',store=>{snapshots.filter(item=>item.module===moduleName&&sameSession(item,sessionId)).forEach(item=>store.delete(item.id))});
}
async function deleteRecoverySession(moduleName,record){return deleteSnapshotsOnly(moduleName,record.documentKey,record.sessionId||'')}
async function cleanupOrphanSources(moduleName){
  const now=Date.now(),live=new Set((await getAllSnapshots(moduleName)).map(item=>item.documentKey)),sources=await allFromIndex(SOURCE_STORE,'module',moduleName);
  const orphanSources=sources.filter(item=>!live.has(item.documentKey)&&now-Number(item.updatedAt||0)>SOURCE_ORPHAN_GRACE_MS);
  if(orphanSources.length)await withStore(SOURCE_STORE,'readwrite',store=>{orphanSources.forEach(item=>store.delete(item.id))});return orphanSources.length}
async function prune(moduleName,documentKey,sessionId){
  const now=Date.now();
  const moduleSnapshots=await getAllSnapshots(moduleName);
  const expired=moduleSnapshots.filter(item=>now-Number(item.updatedAt||0)>MAX_AGE_MS);
  const documentSnapshots=moduleSnapshots.filter(item=>item.documentKey===documentKey&&sameSession(item,sessionId));
  const excessDocument=documentSnapshots.slice(MAX_PER_DOCUMENT);
  const surviving=moduleSnapshots.filter(item=>!expired.some(x=>x.id===item.id)&&!excessDocument.some(x=>x.id===item.id));
  const groupCounts=new Map(),excessModule=[];surviving.forEach(item=>{const key=item.documentKey+'|'+String(item.sessionId||'');groupCounts.set(key,(groupCounts.get(key)||0)+1)});
  for(const item of [...surviving].reverse()){if(surviving.length-excessModule.length<=MAX_PER_MODULE)break;const key=item.documentKey+'|'+String(item.sessionId||'');if((groupCounts.get(key)||0)>1){excessModule.push(item);groupCounts.set(key,groupCounts.get(key)-1)}}
  const ids=new Set(expired.concat(excessDocument,excessModule).map(item=>item.id));
  if(ids.size)await withStore(SNAPSHOT_STORE,'readwrite',store=>{ids.forEach(id=>store.delete(id))});await cleanupOrphanSources(moduleName);
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
  if(document.querySelector('style[data-inkdos-local-recovery]'))return;
  const style=document.createElement('style');
  style.dataset.inkdosLocalRecovery='1';
  style.textContent=`
.inkdos-recovery-overlay{position:fixed;inset:0;z-index:2147482000;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(7,10,17,.72);backdrop-filter:blur(8px);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#eef2ff}
.inkdos-recovery-card{width:min(520px,100%);border:1px solid rgba(255,255,255,.18);border-radius:22px;background:linear-gradient(145deg,#202635,#151923);box-shadow:0 24px 80px rgba(0,0,0,.48);padding:24px}
.inkdos-recovery-kicker{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#9faafc;margin:0 0 10px}
.inkdos-recovery-card h2{font-size:24px;line-height:1.2;margin:0 0 10px;color:#fff}
.inkdos-recovery-card p{line-height:1.55;margin:0 0 14px;color:#c9cfdb}
.inkdos-recovery-meta{display:grid;grid-template-columns:auto 1fr;gap:7px 12px;margin:16px 0 20px;padding:14px;border-radius:14px;background:rgba(255,255,255,.055);font-size:13px}
.inkdos-recovery-meta span:nth-child(odd){color:#929aac}.inkdos-recovery-meta strong{overflow-wrap:anywhere;color:#f4f6fb}
.inkdos-recovery-actions{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:10px}
.inkdos-recovery-actions button{min-height:42px;border:1px solid rgba(255,255,255,.16);border-radius:12px;padding:0 15px;background:#252b38;color:#f4f6fb;font:inherit;font-weight:700;cursor:pointer}
.inkdos-recovery-actions button:hover{background:#303747}.inkdos-recovery-actions .primary{border-color:#6f7df2;background:#5363df}.inkdos-recovery-actions .danger{color:#ffb4b4}
@media(max-width:560px){.inkdos-recovery-overlay{align-items:flex-end;padding:12px}.inkdos-recovery-card{border-radius:22px 22px 14px 14px;padding:20px}.inkdos-recovery-actions{display:grid;grid-template-columns:1fr}.inkdos-recovery-actions button{width:100%}}
`;
  document.head.appendChild(style);
}
function makePrompt(record,count,handlers){
  injectStyles();
  const overlay=document.createElement('div');
  overlay.className='inkdos-recovery-overlay';
  overlay.setAttribute('role','dialog');
  overlay.setAttribute('aria-modal','true');
  overlay.setAttribute('aria-labelledby','inkdosRecoveryTitle');
  const card=document.createElement('div');card.className='inkdos-recovery-card';
  const kicker=document.createElement('p');kicker.className='inkdos-recovery-kicker';kicker.textContent='Local recovery';
  const heading=document.createElement('h2');heading.id='inkdosRecoveryTitle';heading.textContent='Unsaved work is available';
  const description=document.createElement('p');description.textContent='InkDOS found a private recovery snapshot stored only in this browser. Restoring it does not replace the original file.';
  const meta=document.createElement('div');meta.className='inkdos-recovery-meta';
  const add=(label,value)=>{const a=document.createElement('span');a.textContent=label;const b=document.createElement('strong');b.textContent=value;meta.append(a,b)};
  add('File',record.fileName||'Untitled');add('Saved locally',formatTimestamp(record.updatedAt));add('Available versions',String(count));
  const actions=document.createElement('div');actions.className='inkdos-recovery-actions';
  const discard=document.createElement('button');discard.type='button';discard.className='danger';discard.textContent='Discard recovery';
  const normal=document.createElement('button');normal.type='button';normal.textContent='Open normally';
  const restore=document.createElement('button');restore.type='button';restore.className='primary';restore.textContent='Restore';
  actions.append(discard,normal,restore);card.append(kicker,heading,description,meta,actions);overlay.appendChild(card);document.body.appendChild(overlay);
  const close=()=>overlay.remove();
  discard.onclick=async()=>{discard.disabled=normal.disabled=restore.disabled=true;await handlers.discard();close()};
  normal.onclick=()=>{handlers.normal();close()};
  restore.onclick=async()=>{discard.disabled=normal.disabled=restore.disabled=true;restore.textContent='Restoring…';try{await handlers.restore();close()}catch(error){console.error('InkDOS recovery restore failed.',error);restore.textContent='Restore';discard.disabled=normal.disabled=restore.disabled=false;alert('The local recovery snapshot could not be restored. The snapshot remains available.') }};
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
  let documentKey='',fileName=String(options.defaultFileName||'Untitled'),sessionId=String(options.sessionId||randomKey());
  let sourceData=null,sourceMeta={};
  let dirty=false,revision=0,generation=0,destroyed=false,promptEpoch=0,activePrompt=null;
  let timer=null,writing=null;
  function report(message,error){
    try{status(message,error)}catch(statusError){console.warn('Recovery status callback failed.',statusError)}
  }
  async function startDocument(config){
    config=config||{};generation+=1;
    clearTimeout(timer);timer=null;dirty=false;revision=0;
    documentKey=String(config.documentKey||randomKey());fileName=String(config.fileName||fileName||'Untitled');
    sourceData=Object.prototype.hasOwnProperty.call(config,'sourceData')?config.sourceData:null;sourceMeta=sourceData==null?{}:(config.sourceMeta||{});
    try{if(config.resetSnapshots)await deleteSnapshotsOnly(moduleName,documentKey,sessionId);
      if(sourceData!=null)await putSource(moduleName,documentKey,fileName,sourceData,sourceMeta)
    }catch(error){console.warn('InkDOS could not initialize local recovery.',error);report('Local recovery unavailable',error)}
    return documentKey;
  }
  async function flush(){
    if(destroyed||!dirty||!documentKey)return null;
    if(writing)return writing.then(()=>dirty?flush():null);
    const capturedRevision=revision,capturedGeneration=generation;
    const capturedDocumentKey=documentKey,capturedFileName=fileName,capturedSessionId=sessionId,capturedSourceData=sourceData,capturedSourceMeta=sourceMeta;
    writing=(async()=>{
      try{
        const payload=await serialize();
        if(payload==null)return null;
        if(destroyed||capturedGeneration!==generation||capturedDocumentKey!==documentKey||capturedSessionId!==sessionId)return null;
        if(capturedSourceData!=null)try{const existing=await getSource(moduleName,capturedDocumentKey);
          if(!existing)await putSource(moduleName,capturedDocumentKey,capturedFileName,capturedSourceData,capturedSourceMeta)
        }catch(error){console.warn('InkDOS could not rehydrate the recovery source package.',error)}
        if(destroyed||capturedGeneration!==generation||capturedDocumentKey!==documentKey||capturedSessionId!==sessionId)return null;
        const now=Date.now();
        const record={id:moduleName+':'+capturedDocumentKey+':'+capturedSessionId+':'+now+':'+Math.random().toString(36).slice(2,7),
          module:moduleName,documentKey:capturedDocumentKey,sessionId:capturedSessionId,fileName:capturedFileName,
          appVersion:String(options.appVersion||'0.20.3.0'),schemaVersion:2,createdAt:now,updatedAt:now,payload};
        await withStore(SNAPSHOT_STORE,'readwrite',store=>{store.put(record)});
        if(capturedGeneration!==generation||capturedDocumentKey!==documentKey||capturedSessionId!==sessionId){
          await withStore(SNAPSHOT_STORE,'readwrite',store=>{store.delete(record.id)});
          return null;
        }
        await prune(moduleName,capturedDocumentKey,capturedSessionId);
        if(revision===capturedRevision&&capturedGeneration===generation)dirty=false;
        report('Recovery snapshot saved locally');
        return record;
      }catch(error){console.warn('InkDOS could not save a local recovery snapshot.',error);report('Local recovery snapshot failed',error);return null}
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
  async function clearSnapshots(){
    const key=documentKey,pending=writing;generation+=1;dirty=false;revision=0;clearTimeout(timer);timer=null;if(pending)await pending;if(!key)return;
    if(documentKey===key&&(dirty||revision>0)){report('Recovery cleanup deferred because new edits arrived');return}
    try{await deleteSnapshotsOnly(moduleName,key,sessionId);report('Recovery snapshots cleared');if(documentKey===key&&(dirty||revision>0))await flush()}catch(error){console.warn('InkDOS could not clear recovery snapshots.',error)}
  }
  async function markClean(){
    const key=documentKey,pending=writing;generation+=1;dirty=false;revision=0;clearTimeout(timer);timer=null;if(pending)await pending;if(!key)return;
    if(documentKey===key&&(dirty||revision>0)){report('Recovery cleanup deferred because new edits arrived');return}
    try{await deleteSnapshotsOnly(moduleName,key,sessionId);report('Recovery snapshot cleared after save');
      if(documentKey===key&&(dirty||revision>0))await flush()}catch(error){console.warn('InkDOS could not clear the recovery snapshot.',error)}
  }
  async function discardCurrent(){
    const key=documentKey,pending=writing;generation+=1;dirty=false;revision=0;sourceData=null;sourceMeta={};clearTimeout(timer);timer=null;
    if(pending)await pending;if(!key)return;try{await deleteSnapshotsOnly(moduleName,key,sessionId);report('Recovery session discarded')}catch(error){console.warn('InkDOS could not discard this recovery session.',error)}
  }
  function updateFileName(value){fileName=String(value||fileName||'Untitled')}
  function cancelPrompt(){promptEpoch+=1;if(activePrompt){activePrompt.remove();activePrompt=null;report('Recovery prompt deferred because another document action started')}}
  async function promptLatest(){
    if(destroyed)return null;
    const token=++promptEpoch,capturedGeneration=generation,capturedDocumentKey=documentKey;
    const stillCurrent=()=>!destroyed&&token===promptEpoch&&capturedGeneration===generation&&capturedDocumentKey===documentKey;
    try{
      await cleanupOrphanSources(moduleName);if(!stillCurrent())return null;
      const snapshots=await getAllSnapshots(moduleName);if(!stillCurrent()||!snapshots.length)return null;
      const record=snapshots[0];
      const versions=snapshots.filter(item=>item.documentKey===record.documentKey&&sameSession(item,record.sessionId||'')).length;
      activePrompt=makePrompt(record,versions,{
        normal:()=>report('Recovery snapshot kept for later'),
        discard:async()=>{await deleteRecoverySession(moduleName,record);report('Recovery snapshot discarded')},
        restore:async()=>{
          documentKey=record.documentKey;fileName=record.fileName||fileName;revision+=1;dirty=true;const source=await getSource(moduleName,record.documentKey);
          sourceData=source&&Object.prototype.hasOwnProperty.call(source,'data')?source.data:null;sourceMeta=source?.meta||{};
          await restoreCallback({snapshot:record,source:source||null});await deleteRecoverySession(moduleName,record);await flush();report('Recovery snapshot restored');
        }
      });
      return activePrompt;
    }catch(error){console.warn('InkDOS could not inspect local recovery snapshots.',error);return null}
  }
  function getState(){return{module:moduleName,documentKey,sessionId,fileName,dirty,revision,generation,writing:Boolean(writing),hasSourceData:sourceData!=null}}
  function destroy(){generation+=1;destroyed=true;dirty=false;cancelPrompt();clearTimeout(timer);timer=null;document.removeEventListener('visibilitychange',visibilityHandler);global.removeEventListener('pagehide',pageHideHandler)}
  const visibilityHandler=()=>{if(document.visibilityState==='hidden')flush()};
  const pageHideHandler=()=>{flush()};
  document.addEventListener('visibilitychange',visibilityHandler);
  global.addEventListener('pagehide',pageHideHandler);
  return Object.freeze({startDocument,markDirty,flush,clearSnapshots,markClean,discardCurrent,updateFileName,cancelPrompt,promptLatest,getState,destroy});
}
async function clearModule(moduleName){
  const snapshots=await getAllSnapshots(String(moduleName));
  await withStore(SNAPSHOT_STORE,'readwrite',store=>snapshots.forEach(item=>store.delete(item.id)));
  const sources=await allFromIndex(SOURCE_STORE,'module',String(moduleName));
  await withStore(SOURCE_STORE,'readwrite',store=>sources.forEach(item=>store.delete(item.id)));
}
global.InkDOSLocalRecovery=Object.freeze({
  version:'0.20.3.0',
  create,
  openDatabase,
  listSnapshots:getAllSnapshots,
  clearModule,
  constants:Object.freeze({DB_NAME,DB_VERSION,MAX_PER_DOCUMENT,MAX_PER_MODULE,MAX_AGE_MS,SOURCE_ORPHAN_GRACE_MS})
});
})(window);

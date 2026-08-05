(function(global){
'use strict';

const DB_NAME='inkdesk-file-handoff';
const DB_VERSION=1;
const STORE_NAME='files';
const MAX_AGE_MS=15*60*1000;
const BRIDGE_TIMEOUT_MS=30*1000;
const BRIDGE_PROTOCOL_VERSION=1;
const OPAQUE_ORIGIN='null';
const ROUTES={
  docx:'./apps/documents/index.html',
  xls:'./apps/spreadsheets/index.html',
  xlsx:'./apps/spreadsheets/index.html',
  pptx:'./apps/presentations/index.html',
  pdf:'./apps/pdf/index.html'
};

let activeEmbeddedCleanup=null;

function extensionOf(name){
  const match=String(name||'').trim().toLowerCase().match(/\.([a-z0-9]+)$/);
  return match?match[1]:'';
}

function routeForFile(file){
  const extension=extensionOf(file&&file.name);
  const path=ROUTES[extension];
  if(!path)throw new Error('Choose a DOCX, XLS, XLSX, PPTX or PDF file.');
  return {extension,path};
}

function randomToken(){
  if(global.crypto&&typeof global.crypto.randomUUID==='function')return global.crypto.randomUUID();
  const bytes=new Uint8Array(16);
  if(global.crypto&&typeof global.crypto.getRandomValues==='function')global.crypto.getRandomValues(bytes);
  else for(let i=0;i<bytes.length;i++)bytes[i]=Math.floor(Math.random()*256);
  return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
}

function openDatabase(){
  return new Promise((resolve,reject)=>{
    if(!global.indexedDB)return reject(new Error('Temporary browser storage is unavailable.'));
    const request=global.indexedDB.open(DB_NAME,DB_VERSION);
    request.onupgradeneeded=()=>{
      const db=request.result;
      if(!db.objectStoreNames.contains(STORE_NAME))db.createObjectStore(STORE_NAME,{keyPath:'token'});
    };
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error||new Error('Temporary browser storage could not be opened.'));
    request.onblocked=()=>reject(new Error('Temporary browser storage is blocked by another InkDesk tab.'));
  });
}

function transactionPromise(transaction){
  return new Promise((resolve,reject)=>{
    transaction.oncomplete=()=>resolve();
    transaction.onabort=()=>reject(transaction.error||new Error('Temporary file transfer was aborted.'));
    transaction.onerror=()=>reject(transaction.error||new Error('Temporary file transfer failed.'));
  });
}

async function purgeExpiredHandoffs(now=Date.now()){
  const db=await openDatabase();
  try{
    const transaction=db.transaction(STORE_NAME,'readwrite');
    const store=transaction.objectStore(STORE_NAME);
    const cutoff=Number(now)-MAX_AGE_MS;
    const request=store.openCursor();
    request.onsuccess=()=>{
      const cursor=request.result;
      if(!cursor)return;
      if(Number(cursor.value&&cursor.value.createdAt)<cutoff)cursor.delete();
      cursor.continue();
    };
    request.onerror=()=>transaction.abort();
    await transactionPromise(transaction);
  }finally{db.close()}
}

async function clearTemporaryData(){
  const db=await openDatabase();
  try{
    const transaction=db.transaction(STORE_NAME,'readwrite');
    transaction.objectStore(STORE_NAME).clear();
    await transactionPromise(transaction);
  }finally{db.close()}
}

async function stageFile(file){
  if(!(file instanceof Blob)||!file.size)throw new Error('The selected file is empty or unavailable.');
  const token=randomToken();
  const db=await openDatabase();
  try{
    const transaction=db.transaction(STORE_NAME,'readwrite');
    const store=transaction.objectStore(STORE_NAME);
    const cutoff=Date.now()-MAX_AGE_MS;
    const cursorRequest=store.openCursor();
    cursorRequest.onsuccess=()=>{
      const cursor=cursorRequest.result;
      if(!cursor)return;
      if(Number(cursor.value&&cursor.value.createdAt)<cutoff)cursor.delete();
      cursor.continue();
    };
    cursorRequest.onerror=()=>transaction.abort();
    store.put({
      token,
      name:String(file.name||'document'),
      type:String(file.type||''),
      lastModified:Number(file.lastModified||Date.now()),
      size:Number(file.size||0),
      blob:file,
      createdAt:Date.now()
    });
    await transactionPromise(transaction);
    return token;
  }finally{db.close()}
}

async function takeFile(token){
  const db=await openDatabase();
  try{
    const transaction=db.transaction(STORE_NAME,'readwrite');
    const store=transaction.objectStore(STORE_NAME);
    const record=await new Promise((resolve,reject)=>{
      const request=store.get(token);
      request.onsuccess=()=>resolve(request.result||null);
      request.onerror=()=>reject(request.error||new Error('The selected file could not be recovered.'));
    });
    store.delete(token);
    await transactionPromise(transaction);
    if(!record)throw new Error('The temporary file transfer expired or was already used.');
    if(Date.now()-Number(record.createdAt||0)>MAX_AGE_MS)throw new Error('The temporary file transfer expired.');
    if(!(record.blob instanceof Blob)||Number(record.size)!==Number(record.blob.size))throw new Error('The temporary file transfer is incomplete.');
    if(typeof File==='function')return new File([record.blob],record.name,{type:record.type,lastModified:record.lastModified});
    record.blob.name=record.name;
    record.blob.lastModified=record.lastModified;
    return record.blob;
  }finally{db.close()}
}

function appendQuery(path,values){
  const separator=path.includes('?')?'&':'?';
  return path+separator+Object.entries(values).map(([key,value])=>encodeURIComponent(key)+'='+encodeURIComponent(value)).join('&');
}

function bridgeOriginPolicy(urlLike){
  const url=new URL(urlLike,global.location.href);
  if(url.protocol==='http:'||url.protocol==='https:'){
    return Object.freeze({opaque:false,expectedOrigin:url.origin,targetOrigin:url.origin});
  }
  if(url.protocol==='file:'){
    return Object.freeze({opaque:true,expectedOrigin:OPAQUE_ORIGIN,targetOrigin:null});
  }
  throw new Error('Embedded file transfer is unavailable for this URL scheme.');
}

function eventMatchesPolicy(event,policy){
  return Boolean(event&&event.origin===policy.expectedOrigin);
}

function postMessageToOpaqueOrigin(target,message){
  if(global.location.protocol!=='file:')throw new Error('Opaque-origin messaging is restricted to local file mode.');
  // INKDESK_ALLOW_OPAQUE_TARGET: file:// has an opaque origin and requires "*" as targetOrigin.
  target.postMessage(message,'*');
}

function postBridgeMessage(target,message,policy){
  if(!target||typeof target.postMessage!=='function')throw new Error('The embedded workspace is unavailable.');
  if(policy.opaque){
    postMessageToOpaqueOrigin(target,message);
    return;
  }
  target.postMessage(message,policy.targetOrigin);
}

function removeEmbeddedFrame(frame){
  if(frame&&frame.isConnected)frame.remove();
  if(!document.getElementById('workspaceFrame'))document.body.classList.remove('workspace-active');
}

function createEmbeddedWorkspace(file,path){
  if(!(file instanceof Blob)||!file.size)throw new Error('The selected file is empty or unavailable.');
  if(activeEmbeddedCleanup)activeEmbeddedCleanup(true);

  const token=randomToken();
  const expiresAt=Date.now()+BRIDGE_TIMEOUT_MS;
  let pendingFile=file;
  let state='waiting-ready';
  let timer=0;
  let frame=document.getElementById('workspaceFrame');
  if(frame)frame.remove();
  frame=document.createElement('iframe');
  frame.id='workspaceFrame';
  frame.className='workspace-frame';
  frame.title='InkDesk document workspace';
  frame.src=appendQuery(path,{embedded:'1',bridge:token,bridgeVersion:BRIDGE_PROTOCOL_VERSION,bridgeExpires:expiresAt});
  const policy=bridgeOriginPolicy(frame.src);
  document.body.appendChild(frame);
  document.body.classList.add('workspace-active');

  const cleanup=removeFrame=>{
    global.removeEventListener('message',onMessage);
    if(timer)global.clearTimeout(timer);
    timer=0;
    pendingFile=null;
    if(removeFrame)removeEmbeddedFrame(frame);
    if(activeEmbeddedCleanup===cleanup)activeEmbeddedCleanup=null;
  };

  const fail=message=>{
    if(state==='complete'||state==='failed')return;
    state='failed';
    cleanup(true);
    global.alert(message);
  };

  const onMessage=event=>{
    if(event.source!==frame.contentWindow||!eventMatchesPolicy(event,policy))return;
    const data=event.data||{};
    if(data.version!==BRIDGE_PROTOCOL_VERSION||data.token!==token)return;
    if(Date.now()>expiresAt){
      fail('The local file transfer timed out. The original file was not modified. Choose the file again.');
      return;
    }
    if(data.type==='inkdesk:workspace-ready'&&state==='waiting-ready'){
      state='waiting-receipt';
      try{
        postBridgeMessage(frame.contentWindow,{type:'inkdesk:open-file',version:BRIDGE_PROTOCOL_VERSION,token,expiresAt,file:pendingFile},policy);
        pendingFile=null;
      }catch(error){
        console.error('The selected file could not be sent to the embedded workspace.',error);
        fail('The selected file could not be transferred. The original file was not modified.');
      }
      return;
    }
    if(data.type==='inkdesk:file-received'&&state==='waiting-receipt'){
      state='complete';
      cleanup(false);
      return;
    }
    if(data.type==='inkdesk:bridge-error'&&(state==='waiting-ready'||state==='waiting-receipt')){
      fail('The selected file could not be transferred. The original file was not modified.\n\n'+String(data.message||'The embedded workspace rejected the transfer.'));
    }
  };

  global.addEventListener('message',onMessage);
  timer=global.setTimeout(()=>fail('The local file transfer timed out. The original file was not modified. Choose the file again.'),BRIDGE_TIMEOUT_MS);
  activeEmbeddedCleanup=cleanup;
  return {mode:'embedded',path};
}

async function openFromHub(file){
  const route=routeForFile(file);
  purgeExpiredHandoffs().catch(error=>console.warn('Expired temporary file records could not be removed.',error));
  if(global.location.protocol==='file:')return createEmbeddedWorkspace(file,route.path);
  try{
    const token=await stageFile(file);
    global.location.assign(appendQuery(route.path,{openToken:token}));
    return {mode:'navigation',path:route.path};
  }catch(error){
    console.warn('Same-tab file handoff was unavailable; using an embedded workspace.',error);
    return createEmbeddedWorkspace(file,route.path);
  }
}

function cleanHandoffQuery(){
  try{
    const url=new URL(global.location.href);
    url.searchParams.delete('openToken');
    if(global.history&&typeof global.history.replaceState==='function')global.history.replaceState(null,'',url.pathname+url.search+url.hash);
  }catch(error){console.debug('The handoff query could not be removed.',error)}
}

function validForWorkspace(file,extensions){
  const extension=extensionOf(file&&file.name);
  return extensions.map(value=>String(value).toLowerCase()).includes(extension);
}

function attachWorkspace(options){
  const openFile=options&&options.openFile;
  const extensions=(options&&options.extensions)||[];
  if(typeof openFile!=='function')throw new TypeError('A workspace openFile function is required.');
  purgeExpiredHandoffs().catch(error=>console.warn('Expired temporary file records could not be removed.',error));

  const params=new URLSearchParams(global.location.search||'');
  const bridgeToken=params.get('bridge');
  const bridgeVersion=Number(params.get('bridgeVersion'));
  const bridgeExpires=Number(params.get('bridgeExpires'));
  const embedded=params.get('embedded')==='1'&&bridgeToken&&global.parent!==global;

  if(embedded){
    const policy=bridgeOriginPolicy(global.location.href);
    let consumed=false;
    let timer=0;

    const cleanup=()=>{
      global.removeEventListener('message',listener);
      if(timer)global.clearTimeout(timer);
      timer=0;
    };

    const reportBridgeError=message=>{
      try{postBridgeMessage(global.parent,{type:'inkdesk:bridge-error',version:BRIDGE_PROTOCOL_VERSION,token:bridgeToken,message:String(message)},policy)}
      catch(error){console.error('The embedded transfer error could not be reported.',error)}
    };

    const listener=event=>{
      if(consumed||event.source!==global.parent||!eventMatchesPolicy(event,policy))return;
      const data=event.data||{};
      if(data.type!=='inkdesk:open-file'||data.version!==BRIDGE_PROTOCOL_VERSION||data.token!==bridgeToken)return;
      if(Date.now()>bridgeExpires||Date.now()>Number(data.expiresAt||0)){
        consumed=true;
        cleanup();
        reportBridgeError('The transfer token expired.');
        return;
      }
      const file=data.file;
      if(!(file instanceof Blob)||!validForWorkspace(file,extensions)){
        consumed=true;
        cleanup();
        reportBridgeError('The selected file does not match this InkDesk workspace.');
        global.alert('The selected file does not match this InkDesk workspace.');
        return;
      }
      consumed=true;
      cleanup();
      try{postBridgeMessage(global.parent,{type:'inkdesk:file-received',version:BRIDGE_PROTOCOL_VERSION,token:bridgeToken},policy)}
      catch(error){console.error('The embedded transfer receipt could not be sent.',error)}
      Promise.resolve(openFile(file)).catch(error=>{
        console.error('The routed document could not be opened.',error);
        global.alert('The selected document could not be opened. The original file was not modified.\n\n'+(error&&error.message?error.message:error));
      });
    };

    if(bridgeVersion!==BRIDGE_PROTOCOL_VERSION||!Number.isFinite(bridgeExpires)||Date.now()>bridgeExpires){
      reportBridgeError('The transfer token is invalid or expired.');
    }else{
      global.addEventListener('message',listener);
      timer=global.setTimeout(()=>{
        if(consumed)return;
        consumed=true;
        cleanup();
        reportBridgeError('The transfer token expired before a file was received.');
      },Math.max(0,bridgeExpires-Date.now()));
      try{postBridgeMessage(global.parent,{type:'inkdesk:workspace-ready',version:BRIDGE_PROTOCOL_VERSION,token:bridgeToken},policy)}
      catch(error){
        cleanup();
        console.error('The embedded workspace could not announce readiness.',error);
      }
    }
  }

  const handoffToken=params.get('openToken');
  if(handoffToken){
    cleanHandoffQuery();
    Promise.resolve().then(()=>takeFile(handoffToken)).then(file=>{
      if(!validForWorkspace(file,extensions))throw new Error('The selected file does not match this InkDesk workspace.');
      return openFile(file);
    }).catch(error=>{
      console.error('The selected document could not be transferred to the workspace.',error);
      global.alert('InkDesk opened the correct workspace, but the selected file could not be transferred automatically. The original file was not modified. Use the Open button and choose it again.\n\n'+(error&&error.message?error.message:error));
    });
  }
}

global.InkDeskFileRouter=Object.freeze({
  extensionOf,
  routeForFile,
  openFromHub,
  attachWorkspace,
  clearTemporaryData,
  _test:{stageFile,takeFile,purgeExpiredHandoffs,bridgeOriginPolicy,eventMatchesPolicy}
});
})(window);

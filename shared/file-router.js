(function(global){
'use strict';

const DB_NAME='inkdesk-file-handoff';
const DB_VERSION=1;
const STORE_NAME='files';
const MAX_AGE_MS=15*60*1000;
const ROUTES={
  docx:'./apps/documents/index.html',
  xls:'./apps/spreadsheets/index.html',
  xlsx:'./apps/spreadsheets/index.html',
  pptx:'./apps/presentations/index.html',
  pdf:'./apps/pdf/index.html',
  txt:'./apps/txt/index.html',
  epub:'./apps/epub/index.html'
};

function extensionOf(name){
  const match=String(name||'').trim().toLowerCase().match(/\.([a-z0-9]+)$/);
  return match?match[1]:'';
}
function routeForFile(file){
  const extension=extensionOf(file&&file.name);
  const path=ROUTES[extension];
  if(!path)throw new Error(
    'Choose a DOCX, XLS, XLSX, PPTX, PDF, TXT or EPUB file.'
  );
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
function createEmbeddedWorkspace(file,path){
  const token=randomToken();
  let frame=document.getElementById('workspaceFrame');
  if(frame)frame.remove();
  frame=document.createElement('iframe');
  frame.id='workspaceFrame';
  frame.className='workspace-frame';
  frame.title='InkDesk document workspace';
  frame.src=appendQuery(path,{embedded:'1',bridge:token});
  document.body.appendChild(frame);
  document.body.classList.add('workspace-active');
  const onMessage=event=>{
    if(event.source!==frame.contentWindow)return;
    const data=event.data||{};
    if(data.type!=='inkdesk:workspace-ready'||data.token!==token)return;
    frame.contentWindow.postMessage({type:'inkdesk:open-file',token,file},'*');
    global.removeEventListener('message',onMessage);
  };
  global.addEventListener('message',onMessage);
  return {mode:'embedded',path};
}
async function openFromHub(file){
  const route=routeForFile(file);
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
  const params=new URLSearchParams(global.location.search||'');
  const bridgeToken=params.get('bridge');
  const embedded=params.get('embedded')==='1'&&bridgeToken&&global.parent!==global;
  if(embedded){
    const listener=event=>{
      if(event.source!==global.parent)return;
      const data=event.data||{};
      if(data.type!=='inkdesk:open-file'||data.token!==bridgeToken)return;
      const file=data.file;
      if(!(file instanceof Blob)||!validForWorkspace(file,extensions)){
        global.alert('The selected file does not match this InkDesk workspace.');
        return;
      }
      Promise.resolve(openFile(file)).catch(error=>{
        console.error('The routed document could not be opened.',error);
        global.alert('The selected document could not be opened.\n\n'+(error&&error.message?error.message:error));
      });
    };
    global.addEventListener('message',listener);
    global.parent.postMessage({type:'inkdesk:workspace-ready',token:bridgeToken},'*');
  }
  const handoffToken=params.get('openToken');
  if(handoffToken){
    cleanHandoffQuery();
    Promise.resolve().then(()=>takeFile(handoffToken)).then(file=>{
      if(!validForWorkspace(file,extensions))throw new Error('The selected file does not match this InkDesk workspace.');
      return openFile(file);
    }).catch(error=>{
      console.error('The selected document could not be transferred to the workspace.',error);
      global.alert('InkDesk opened the correct workspace, but the selected file could not be transferred automatically. Use the Open button and choose it again.\n\n'+(error&&error.message?error.message:error));
    });
  }
}
global.InkDeskFileRouter=Object.freeze({
  version:'0.20.0',
  extensionOf,
  routeForFile,
  openFromHub,
  attachWorkspace,
  _test:{stageFile,takeFile}
});
})(window);

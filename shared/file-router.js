(function (global) {
'use strict';
const DB_NAME='inkdos-file-handoff',DB_VERSION=1,STORE_NAME='files',MAX_AGE_MS=15*60*1000;
function registry(){if(!global.InkDOSModules)throw new Error('InkDOS module registry is unavailable.');
return global.InkDOSModules;
}
function extensionOf(name){return registry().extensionOf(name);
}
function routeForFile(file){const extension=extensionOf(file&&file.name),module=registry().resolveExtension(extension);
if(!module)throw new Error('This file type is not supported by an enabled InkDOS app.');
return Object.freeze({extension,appId:module.id,module,path:'./'+module.route.replace(/^\.?\//,'')});
}
function acceptedExtensions(appId){const module=registry().get(appId);
return module&&module.enabled?module.extensions.slice():[];
}
function randomToken(){if(global.crypto&&typeof global.crypto.randomUUID==='function')return global.crypto.randomUUID();
const bytes=new Uint8Array(16);
if(global.crypto&&typeof global.crypto.getRandomValues==='function')global.crypto.getRandomValues(bytes);
else for(let i=0;
i<bytes.length;
i+=1)bytes[i]=Math.floor(Math.random()*256);
return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
}
function openDatabase(){return new Promise((resolve,reject)=>{if(!global.indexedDB){reject(new Error('Temporary browser storage is unavailable.'));
return;
}const request=global.indexedDB.open(DB_NAME,DB_VERSION);
request.onupgradeneeded=()=>{const db=request.result;
if(!db.objectStoreNames.contains(STORE_NAME))db.createObjectStore(STORE_NAME,{keyPath:'token'});
};
request.onsuccess=()=>resolve(request.result);
request.onerror=()=>reject(request.error||new Error('Temporary browser storage could not be opened.'));
request.onblocked=()=>reject(new Error('Temporary browser storage is blocked by another InkDOS tab.'));
});
}
function transactionPromise(transaction){return new Promise((resolve,reject)=>{transaction.oncomplete=()=>resolve();
transaction.onabort=()=>reject(transaction.error||new Error('Temporary file transfer was aborted.'));
transaction.onerror=()=>reject(transaction.error||new Error('Temporary file transfer failed.'));
});
}
async function stageFile(file){if(!(file instanceof Blob)||!file.size)throw new Error('The selected file is empty or unavailable.');
const token=randomToken(),db=await openDatabase();
try{const tx=db.transaction(STORE_NAME,'readwrite'),store=tx.objectStore(STORE_NAME),cutoff=Date.now()-MAX_AGE_MS,cursor=store.openCursor();
cursor.onsuccess=()=>{const item=cursor.result;
if(!item)return;
if(Number(item.value&&item.value.createdAt)<cutoff)item.delete();
item.continue();
};
store.put({token,name:String(file.name||'document'),type:String(file.type||''),lastModified:Number(file.lastModified||Date.now()),size:Number(file.size||0),blob:file,createdAt:Date.now()});
await transactionPromise(tx);
return token;
}finally{db.close();
}}
async function takeFile(token){const db=await openDatabase();
try{const tx=db.transaction(STORE_NAME,'readwrite'),store=tx.objectStore(STORE_NAME);
const record=await new Promise((resolve,reject)=>{const request=store.get(token);
request.onsuccess=()=>resolve(request.result||null);
request.onerror=()=>reject(request.error||new Error('The selected file could not be recovered.'));
});
store.delete(token);
await transactionPromise(tx);
if(!record)throw new Error('The temporary file transfer expired or was already used.');
if(Date.now()-Number(record.createdAt||0)>MAX_AGE_MS)throw new Error('The temporary file transfer expired.');
if(!(record.blob instanceof Blob)||Number(record.size)!==Number(record.blob.size))throw new Error('The temporary file transfer is incomplete.');
if(typeof File==='function')return new File([record.blob],record.name,{type:record.type,lastModified:record.lastModified});
record.blob.name=record.name;
record.blob.lastModified=record.lastModified;
return record.blob;
}finally{db.close();
}}
function appendQuery(path,values){const separator=path.includes('?')?'&':'?';
return path+separator+Object.entries(values).map(([key,value])=>encodeURIComponent(key)+'='+encodeURIComponent(value)).join('&');
}
function messageOrigin(){const origin=String(global.location&&global.location.origin||'');
return origin&&origin!=='null'?origin:null;
}
function trustedMessage(event,source){if(event.source!==source)return false;
const origin=messageOrigin();
return origin?event.origin===origin:event.origin==='null';
}
function createEmbeddedWorkspace(file,path){const token=randomToken();
let frame=document.getElementById('workspaceFrame');
if(frame)frame.remove();
frame=document.createElement('iframe');
frame.id='workspaceFrame';
frame.className='workspace-frame';
frame.title='InkDOS document workspace';
frame.src=appendQuery(path,{embedded:'1',bridge:token});
document.body.appendChild(frame);
document.body.classList.add('workspace-active');
const onMessage=event=>{if(!trustedMessage(event,frame.contentWindow))return;
const data=event.data||{};
if(data.type!=='inkdos:workspace-ready'||data.token!==token)return;
frame.contentWindow.postMessage({type:'inkdos:open-file',token,file},messageOrigin()||'*');
global.removeEventListener('message',onMessage);
};
global.addEventListener('message',onMessage);
return{mode:'embedded',path};
}
async function openFromHub(file){const route=routeForFile(file);
if(global.location.protocol==='file:')return createEmbeddedWorkspace(file,route.path);
try{const token=await stageFile(file);
global.location.assign(appendQuery(route.path,{openToken:token}));
return{mode:'navigation',path:route.path};
}catch(error){console.warn('Same-tab file handoff was unavailable; using embedded workspace.',error);
return createEmbeddedWorkspace(file,route.path);
}}
function cleanHandoffQuery(){try{const url=new URL(global.location.href);
url.searchParams.delete('openToken');
if(global.history&&typeof global.history.replaceState==='function')global.history.replaceState(null,'',url.pathname+url.search+url.hash);
}catch(error){console.debug('The handoff query could not be removed.',error);
}}
function validForWorkspace(file,appId){return acceptedExtensions(appId).includes(extensionOf(file&&file.name));
}
function attachWorkspace(options){const openFile=options&&options.openFile,appId=String(options&&options.appId||'');
if(typeof openFile!=='function')throw new TypeError('A workspace openFile function is required.');
if(!registry().get(appId))throw new Error('The workspace is not registered in InkDOS.');
const params=new URLSearchParams(global.location.search||''),bridgeToken=params.get('bridge'),embedded=params.get('embedded')==='1'&&bridgeToken&&global.parent!==global;
if(embedded){const listener=event=>{if(!trustedMessage(event,global.parent))return;
const data=event.data||{};
if(data.type!=='inkdos:open-file'||data.token!==bridgeToken)return;
const file=data.file;
if(!(file instanceof Blob)||!validForWorkspace(file,appId)){global.alert('The selected file does not match this InkDOS app.');
return;
}Promise.resolve(openFile(file)).catch(error=>{console.error('The routed document could not be opened.',error);
global.alert('The selected document could not be opened.\n\n'+(error&&error.message?error.message:error));
});
};
global.addEventListener('message',listener);
global.parent.postMessage({type:'inkdos:workspace-ready',token:bridgeToken},messageOrigin()||'*');
}const handoffToken=params.get('openToken');
if(!handoffToken)return;
cleanHandoffQuery();
Promise.resolve().then(()=>takeFile(handoffToken)).then(file=>{if(!validForWorkspace(file,appId))throw new Error('The selected file does not match this InkDOS app.');
return openFile(file);
}).catch(error=>{console.error('The selected document could not be transferred to the workspace.',error);
global.alert('InkDOS opened the correct app, but the selected file could not be transferred automatically. Use Open and choose it again.\n\n'+(error&&error.message?error.message:error));
});
}
global.InkDOSFileRouter=Object.freeze({version:'1',extensionOf,routeForFile,appForFile:file=>routeForFile(file).module,acceptedExtensions,openFromHub,attachWorkspace,_test:Object.freeze({stageFile,takeFile,validForWorkspace})});
})(typeof window!=='undefined'?window:globalThis);

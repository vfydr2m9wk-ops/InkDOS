(function(g){'use strict';const NS=g.InkDOS2=g.InkDOS2||{};
let deliveryInFlight=null;
function singleFlight(run){if(deliveryInFlight)return deliveryInFlight;let p;try{p=Promise.resolve(run())}catch(e){return Promise.reject(e)}deliveryInFlight=p;p.finally(()=>{if(deliveryInFlight===p)deliveryInFlight=null}).catch(()=>{});return p}
async function sha256(bytes){if(!(g.crypto&&g.crypto.subtle))return null;const buf=bytes instanceof ArrayBuffer?bytes:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);const dig=await g.crypto.subtle.digest('SHA-256',buf);return Array.from(new Uint8Array(dig),b=>b.toString(16).padStart(2,'0')).join('')}
function safeName(name){let n=String(name||'Untitled.txt').trim()||'Untitled.txt';n=n.replace(/[\\/:*?"<>|]+/g,'-');return /\.txt$/i.test(n)?n:n+'.txt'}
function toFile(blob,fileName){const name=safeName(fileName);try{return new File([blob],name,{type:blob.type||'text/plain',lastModified:Date.now()})}catch(_){return null}}
function canShareFile(file){if(!file||!g.navigator||typeof navigator.share!=='function'||typeof navigator.canShare!=='function')return false;try{return !!navigator.canShare({files:[file]})}catch(_){return false}}
function isAppleTouchHost(){const nav=g.navigator||{};const ua=String(nav.userAgent||'');const platform=String(nav.platform||'');const touches=Number(nav.maxTouchPoints||0);return /iPad|iPhone|iPod/i.test(ua)||(platform==='MacIntel'&&touches>1)}
function capabilities(file){return Object.freeze({fileSystem:typeof g.showSaveFilePicker==='function',share:canShareFile(file),download:!!(g.document&&g.URL&&URL.createObjectURL),preferShareSave:isAppleTouchHost()})}
function stamp(base){return Object.assign({requestedAt:new Date().toISOString(),deliveryConfirmed:false},base)}
async function finishReceipt(base,blob){const bytes=new Uint8Array(await blob.arrayBuffer());return Object.freeze(Object.assign(stamp(base),{bytes:bytes.byteLength,sha256:await sha256(bytes)}))}
function chooseRoute(file){const c=capabilities(file);const local=(g.location&&g.location.protocol==='file:');if((local||c.preferShareSave)&&c.share)return 'web-share';if(c.fileSystem)return 'file-system-access';if(c.share)return 'web-share';return 'download'}
async function viaPicker(blob,fileName){let handlePromise;try{handlePromise=g.showSaveFilePicker({suggestedName:safeName(fileName),types:[{description:'Plain text',accept:{'text/plain':['.txt']}}]})}catch(e){throw deliveryError('picker-blocked','Native save picker is unavailable in this host.',e)}
let handle;try{handle=await handlePromise}catch(e){if(e&&e.name==='AbortError')throw deliveryError('cancelled','Save cancelled.',e);throw deliveryError('picker-blocked','Native save picker was blocked by this host.',e)}
try{const writable=await handle.createWritable();await writable.write(blob);await writable.close()}catch(e){throw deliveryError('write-failed','The selected file could not be written.',e)}
return finishReceipt({fileName:safeName(fileName),method:'file-system-access',deliveryConfirmed:true},blob)}
async function viaShare(blob,fileName,file){let sharePromise;try{sharePromise=navigator.share({files:[file],title:safeName(fileName)})}catch(e){throw deliveryError('share-blocked','System share is unavailable in this host.',e)}
try{await sharePromise}catch(e){if(e&&e.name==='AbortError')throw deliveryError('cancelled','Share cancelled.',e);throw deliveryError('share-blocked','System share was blocked by this host.',e)}
return finishReceipt({fileName:safeName(fileName),method:'web-share',deliveryConfirmed:false},blob)}
async function viaDownload(blob,fileName){if(!(g.document&&g.URL&&URL.createObjectURL))throw deliveryError('download-unavailable','Download is unavailable in this host.');const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download=safeName(fileName);a.rel='noopener';a.hidden=true;document.body.appendChild(a);try{a.click()}finally{a.remove();setTimeout(()=>URL.revokeObjectURL(u),15000)}return finishReceipt({fileName:safeName(fileName),method:'download',deliveryConfirmed:false},blob)}
function deliveryError(code,message,cause){const e=new Error(message);e.name='InkDOSDeliveryError';e.code=code;if(cause)e.cause=cause;return e}
function share(blob,fileName){const file=toFile(blob,fileName);if(!canShareFile(file))return Promise.reject(deliveryError('share-unavailable','System file sharing is unavailable in this host.'));return viaShare(blob,fileName,file)}
function deliverOnce(blob,fileName){const file=toFile(blob,fileName);const route=chooseRoute(file);/* Invoke exactly one chosen native route before any await so transient user activation remains available without duplicate delivery. */
if(route==='web-share')return viaShare(blob,fileName,file);
if(route==='file-system-access')return viaPicker(blob,fileName).catch(e=>{if(e.code==='cancelled'||e.code==='write-failed')throw e;if(canShareFile(file))return viaShare(blob,fileName,file).catch(()=>viaDownload(blob,fileName).catch(()=>{throw e}));return viaDownload(blob,fileName).catch(()=>{throw e})});
return viaDownload(blob,fileName)}
function deliver(blob,fileName){return singleFlight(()=>deliverOnce(blob,fileName))}
NS.sha256=sha256;NS.FileDelivery={deliver,share,capabilities,safeName};})(globalThis);

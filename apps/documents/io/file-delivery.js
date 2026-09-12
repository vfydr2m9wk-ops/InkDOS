(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
let deliveryInFlight=null;
function singleFlight(run){if(deliveryInFlight)return deliveryInFlight;let p;try{p=Promise.resolve(run())}catch(e){return Promise.reject(e)}deliveryInFlight=p;p.finally(()=>{if(deliveryInFlight===p)deliveryInFlight=null}).catch(()=>{});return p}
function fail(code,message,cause){const e=new Error(message);e.name='InkDOSDocumentsDeliveryError';e.code=code;if(cause)e.cause=cause;throw e}
function safeName(name){let n=String(name||'Untitled.docx').trim()||'Untitled.docx';n=n.replace(/[\\/:*?"<>|]+/g,'-');return /\.docx$/i.test(n)?n:n+'.docx'}
function toFile(blob,fileName){try{return new File([blob],safeName(fileName),{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document',lastModified:Date.now()})}catch(_){return null}}
function canShare(file){if(!file||typeof navigator==='undefined'||typeof navigator.share!=='function'||typeof navigator.canShare!=='function')return false;try{return !!navigator.canShare({files:[file]})}catch(_){return false}}
function isAppleTouchHost(){const nav=global.navigator||{};const ua=String(nav.userAgent||'');const platform=String(nav.platform||'');const touches=Number(nav.maxTouchPoints||0);return /iPad|iPhone|iPod/i.test(ua)||(platform==='MacIntel'&&touches>1)}
function capabilities(blob,fileName){const file=toFile(blob,fileName);return Object.freeze({fileSystem:typeof global.showSaveFilePicker==='function',share:canShare(file),download:!!(global.document&&global.URL&&URL.createObjectURL),local:!!(global.location&&global.location.protocol==='file:'),preferShareSave:isAppleTouchHost()})}
async function viaPicker(blob,fileName){let handle;try{handle=await global.showSaveFilePicker({suggestedName:safeName(fileName),types:[{description:'Word document',accept:{'application/vnd.openxmlformats-officedocument.wordprocessingml.document':['.docx']}}]})}catch(e){if(e?.name==='AbortError')fail('cancelled','Save cancelled.',e);fail('picker-blocked','Native save picker was blocked by this host.',e)}try{const writable=await handle.createWritable();await writable.write(blob);await writable.close()}catch(e){fail('write-failed','The selected DOCX could not be written.',e)}return Object.freeze({method:'file-system-access',fileName:safeName(fileName),deliveryConfirmed:true})}
async function viaShare(blob,fileName,file){try{await navigator.share({files:[file]})}catch(e){if(e?.name==='AbortError')fail('cancelled','Share cancelled.',e);fail('share-blocked','System file sharing was blocked by this host.',e)}return Object.freeze({method:'web-share',fileName:safeName(fileName),deliveryConfirmed:false})}
async function share(blob,fileName){const file=toFile(blob,fileName);if(!canShare(file))fail('share-unavailable','System file sharing is unavailable in this host.');return viaShare(blob,fileName,file)}
async function viaDownload(blob,fileName){if(!(global.document&&global.URL&&URL.createObjectURL))fail('download-unavailable','Download is unavailable in this host.');const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=safeName(fileName);a.rel='noopener';a.hidden=true;document.body.appendChild(a);try{a.click()}finally{a.remove();setTimeout(()=>URL.revokeObjectURL(u),15000)}return Object.freeze({method:'download',fileName:safeName(fileName),deliveryConfirmed:false})}
async function deliverOnce(blob,fileName){const file=toFile(blob,fileName),c=capabilities(blob,fileName);
 // Exactly-once invariant: after Web Share is invoked, its outcome is terminal for this Save; only pre-invocation routing may fall back.
 if(c.local){if(c.share)return viaShare(blob,fileName,file);fail('local-delivery-unavailable','This HTML viewer blocks direct DOCX downloads. Use a browser/host with system file sharing enabled, or open the InkDOS app from its normal host.');}
 if(c.preferShareSave&&c.share)return viaShare(blob,fileName,file)
 if(c.fileSystem){try{return await viaPicker(blob,fileName)}catch(e){if(e.code==='cancelled'||e.code==='write-failed')throw e;if(c.share)return viaShare(blob,fileName,file);return viaDownload(blob,fileName)}}
 if(c.share)return viaShare(blob,fileName,file)
 return viaDownload(blob,fileName)
}
function deliver(blob,fileName){return singleFlight(()=>deliverOnce(blob,fileName))}
NS.FileDelivery=Object.freeze({deliver,share,capabilities,safeName});
})(globalThis);

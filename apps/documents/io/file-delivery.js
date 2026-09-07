(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function fail(code,message,cause){const e=new Error(message);e.name='InkDOSDocumentsDeliveryError';e.code=code;if(cause)e.cause=cause;throw e}
function safeName(name){let n=String(name||'Untitled.docx').trim()||'Untitled.docx';n=n.replace(/[\\/:*?"<>|]+/g,'-');return /\.docx$/i.test(n)?n:n+'.docx'}
function toFile(blob,fileName){try{return new File([blob],safeName(fileName),{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document',lastModified:Date.now()})}catch(_){return null}}
function canShare(file){if(!file||!navigator||typeof navigator.share!=='function'||typeof navigator.canShare!=='function')return false;try{return !!navigator.canShare({files:[file]})}catch(_){return false}}
function capabilities(blob,fileName){const file=toFile(blob,fileName);return Object.freeze({fileSystem:typeof global.showSaveFilePicker==='function',share:canShare(file),download:!!(global.document&&global.URL&&URL.createObjectURL),local:location&&location.protocol==='file:'})}
async function viaPicker(blob,fileName){let handle;try{handle=await global.showSaveFilePicker({suggestedName:safeName(fileName),types:[{description:'Word document',accept:{'application/vnd.openxmlformats-officedocument.wordprocessingml.document':['.docx']}}]})}catch(e){if(e?.name==='AbortError')fail('cancelled','Save cancelled.',e);fail('picker-blocked','Native save picker was blocked by this host.',e)}try{const writable=await handle.createWritable();await writable.write(blob);await writable.close()}catch(e){fail('write-failed','The selected DOCX could not be written.',e)}return Object.freeze({method:'file-system-access',fileName:safeName(fileName),deliveryConfirmed:true})}
async function viaShare(blob,fileName,file){try{await navigator.share({files:[file],title:safeName(fileName)})}catch(e){if(e?.name==='AbortError')fail('cancelled','Share cancelled.',e);fail('share-blocked','System file sharing was blocked by this host.',e)}return Object.freeze({method:'web-share',fileName:safeName(fileName),deliveryConfirmed:false})}
async function share(blob,fileName){const file=toFile(blob,fileName);if(!canShare(file))fail('share-unavailable','System file sharing is unavailable in this host.');return viaShare(blob,fileName,file)}
async function viaDownload(blob,fileName){if(!(global.document&&global.URL&&URL.createObjectURL))fail('download-unavailable','Download is unavailable in this host.');const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=safeName(fileName);a.rel='noopener';a.hidden=true;document.body.appendChild(a);try{a.click()}finally{a.remove();setTimeout(()=>URL.revokeObjectURL(u),15000)}return Object.freeze({method:'download',fileName:safeName(fileName),deliveryConfirmed:false})}
async function deliver(blob,fileName){const file=toFile(blob,fileName),c=capabilities(blob,fileName);
 // Local HTML viewers on iPad commonly block blob: navigation. Prefer native share there and never force the blocked route.
 if(c.local){if(c.share)return viaShare(blob,fileName,file);fail('local-delivery-unavailable','This HTML viewer blocks direct DOCX downloads. Use a browser/host with system file sharing enabled, or open the InkDOS app from its normal host.');}
 if(c.fileSystem){try{return await viaPicker(blob,fileName)}catch(e){if(e.code==='cancelled')throw e;if(c.share)try{return await viaShare(blob,fileName,file)}catch(_){}return viaDownload(blob,fileName)}}
 if(c.share){try{return await viaShare(blob,fileName,file)}catch(e){if(e.code==='cancelled')throw e;return viaDownload(blob,fileName)}}
 return viaDownload(blob,fileName)
}
NS.FileDelivery=Object.freeze({deliver,share,capabilities,safeName});
})(globalThis);

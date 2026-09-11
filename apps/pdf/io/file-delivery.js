(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
function safeName(name){let n=String(name||'document-annotated.pdf').trim()||'document-annotated.pdf';n=n.replace(/[\\/:*?"<>|]+/g,'-');return /\.pdf$/i.test(n)?n:n+'.pdf'}
function toFile(blob,name){try{return new File([blob],safeName(name),{type:'application/pdf',lastModified:Date.now()})}catch(_){return null}}
function canShare(file){try{return !!file&&typeof navigator.share==='function'&&typeof navigator.canShare==='function'&&navigator.canShare({files:[file]})}catch(_){return false}}
function deliveryError(code,message,cause){const e=new Error(message);e.code=code;if(cause)e.cause=cause;return e}
function isAppleTouchHost(){const nav=global.navigator||{};const ua=String(nav.userAgent||'');const platform=String(nav.platform||'');const touches=Number(nav.maxTouchPoints||0);return /iPad|iPhone|iPod/i.test(ua)||(platform==='MacIntel'&&touches>1)}
async function share(blob,name){name=safeName(name);const file=toFile(blob,name);if(!canShare(file))throw deliveryError('share-unavailable','System file sharing is unavailable in this host.');try{await navigator.share({files:[file],title:name})}catch(cause){if(cause?.name==='AbortError')throw cause;throw deliveryError('share-blocked','System file sharing was blocked by this host.',cause)}return {method:'web-share',fileName:name,deliveryConfirmed:false}}
async function picker(blob,name){let h;try{h=await global.showSaveFilePicker({suggestedName:name,types:[{description:'PDF document',accept:{'application/pdf':['.pdf']}}]})}catch(e){if(e?.name==='AbortError')throw e;throw deliveryError('picker-blocked','Native save picker was blocked by this host.',e)}try{const w=await h.createWritable();await w.write(blob);await w.close()}catch(e){throw deliveryError('write-failed','The selected PDF could not be written.',e)}return {method:'file-system-access',fileName:name,deliveryConfirmed:true}}
async function download(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.hidden=true;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),15000);return {method:'download',fileName:name,deliveryConfirmed:false}}
async function deliver(blob,name){name=safeName(name);const file=toFile(blob,name),local=!!(global.location&&global.location.protocol==='file:');
 if(local&&canShare(file))return share(blob,name)
 // Apple touch hosts use one terminal native delivery route. Never follow an invoked Web Share operation with a second download.
 if(isAppleTouchHost()&&canShare(file))return share(blob,name)
 if(typeof global.showSaveFilePicker==='function'){try{return await picker(blob,name)}catch(e){if(e?.name==='AbortError'||e.code==='write-failed')throw e}}
 if(canShare(file)){try{return await share(blob,name)}catch(e){if(e?.name==='AbortError')throw e}}
 return download(blob,name)
}
NS.FileDelivery=Object.freeze({deliver,share,safeName});
})(globalThis);

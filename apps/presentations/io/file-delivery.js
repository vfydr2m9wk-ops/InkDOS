(function(global){'use strict';
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{},MIME='application/vnd.openxmlformats-officedocument.presentationml.presentation';
let deliveryInFlight=null;
function singleFlight(run){if(deliveryInFlight)return deliveryInFlight;let p;try{p=Promise.resolve(run())}catch(e){return Promise.reject(e)}deliveryInFlight=p;p.finally(()=>{if(deliveryInFlight===p)deliveryInFlight=null}).catch(()=>{});return p}
function fail(code,message,cause){const e=new Error(message);e.name='InkDOSPresentationsDeliveryError';e.code=code;if(cause)e.cause=cause;throw e}
function safeName(name){let n=String(name||'Untitled.pptx').trim()||'Untitled.pptx';n=n.replace(/[\\/:*?"<>|]+/g,'-');return /\.pptx$/i.test(n)?n:n+'.pptx'}
function toFile(blob,fileName){try{return new File([blob],safeName(fileName),{type:MIME,lastModified:Date.now()})}catch(_){return null}}
function canShare(file){if(!file||typeof navigator==='undefined'||typeof navigator.share!=='function'||typeof navigator.canShare!=='function')return false;try{return !!navigator.canShare({files:[file]})}catch(_){return false}}
function isAppleTouchHost(){const nav=global.navigator||{};const ua=String(nav.userAgent||'');const platform=String(nav.platform||'');const touches=Number(nav.maxTouchPoints||0);return /iPad|iPhone|iPod/i.test(ua)||(platform==='MacIntel'&&touches>1)}
async function picker(blob,name){let handle;try{handle=await global.showSaveFilePicker({suggestedName:safeName(name),types:[{description:'PowerPoint presentation',accept:{[MIME]:['.pptx']}}]})}catch(e){if(e?.name==='AbortError')fail('cancelled','Save cancelled.',e);fail('picker-blocked','Native save picker was blocked.',e)}try{const w=await handle.createWritable();await w.write(blob);await w.close()}catch(e){fail('write-failed','The selected PPTX could not be written.',e)}return {method:'file-system-access',deliveryConfirmed:true,fileName:safeName(name)}}
async function viaShare(blob,name,file){try{await navigator.share({files:[file],title:safeName(name)})}catch(e){if(e?.name==='AbortError')fail('cancelled','Share cancelled.',e);fail('share-blocked','System file sharing was blocked.',e)}return {method:'web-share',deliveryConfirmed:false,fileName:safeName(name)}}
async function share(blob,name){const file=toFile(blob,name);if(!canShare(file))fail('share-unavailable','System file sharing is unavailable in this host.');return viaShare(blob,name,file)}
async function download(blob,name){if(!(global.document&&global.URL&&URL.createObjectURL))fail('download-unavailable','Download is unavailable.');const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=safeName(name);a.hidden=true;document.body.appendChild(a);try{a.click()}finally{a.remove();setTimeout(()=>URL.revokeObjectURL(u),15000)}return {method:'download',deliveryConfirmed:false,fileName:safeName(name)}}
async function deliverOnce(blob,name){const file=toFile(blob,name),local=!!(global.location&&global.location.protocol==='file:');
 if(local){if(canShare(file))return viaShare(blob,name,file);fail('local-delivery-unavailable','This local HTML viewer cannot deliver PPTX files. Open the app in a host with native file sharing enabled.')}
 // Any invoked delivery route is terminal for this Save action. A rejected Web Share promise does not prove that the host produced no file.
 if(isAppleTouchHost()&&canShare(file))return viaShare(blob,name,file)
 if(typeof global.showSaveFilePicker==='function'){try{return await picker(blob,name)}catch(e){if(e.code==='cancelled'||e.code==='write-failed')throw e;if(canShare(file))return viaShare(blob,name,file);return download(blob,name)}}
 if(canShare(file))return viaShare(blob,name,file)
 return download(blob,name)
}
function deliver(blob,name){return singleFlight(()=>deliverOnce(blob,name))}
NS.FileDelivery=Object.freeze({deliver,share,safeName,MIME});
})(globalThis);

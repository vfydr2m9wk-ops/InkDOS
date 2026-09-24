(function(g){'use strict';
const doc=typeof document!=='undefined'?document:null;
function extension(name){const m=String(name||'').toLowerCase().match(/\.([^.\\/]+)$/);return m?m[1]:''}
function extensionsFromAccept(accept){const out=new Set();for(const value of String(accept||'').split(',')){const token=value.trim().toLowerCase();if(token.startsWith('.')&&token.length>1)out.add(token.slice(1))}return out}
function compatibleInput(file){if(!doc)return null;const ext=extension(file&&file.name);for(const input of doc.querySelectorAll('input[type="file"]')){const allowed=extensionsFromAccept(input.accept);if(!allowed.size||(ext&&allowed.has(ext)))return input}return null}
function dispatchError(error){try{doc?.dispatchEvent(new CustomEvent('inkdos:file-launch-error',{detail:{message:String(error?.message||error||'File launch failed')}}))}catch(_){}}
async function injectFile(file){if(!file)return false;const input=compatibleInput(file);if(!input)throw new Error('Unsupported file format for this InkDOS workspace.');if(typeof g.DataTransfer!=='function'||typeof g.File!=='function')throw new Error('This host cannot inject a launched file into the workspace.');const transfer=new DataTransfer();transfer.items.add(file);input.files=transfer.files;input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));return true}
async function openHandle(handle){if(!handle||handle.kind!=='file'||typeof handle.getFile!=='function')return false;return injectFile(await handle.getFile())}
async function consume(params){for(const handle of params?.files||[]){if(await openHandle(handle))return true}return false}
function install(){const queue=g.launchQueue;if(!queue||typeof queue.setConsumer!=='function')return false;queue.setConsumer(params=>consume(params).catch(error=>{console.error('InkDOS launched-file open failed:',error);dispatchError(error)}));return true}
install();
g.InkDOSFileLaunch=Object.freeze({install,consume,openHandle,injectFile,compatibleInput,extensionsFromAccept});
})(globalThis);

(function(g){'use strict';
const doc=typeof document!=='undefined'?document:null;
const perfBootAt=performance.now();\nlet openHandler=null,pendingLaunchFiles=[];
function extension(name){const m=String(name||'').toLowerCase().match(/\.([^.\\/]+)$/);return m?m[1]:''}
function acceptTokens(accept){return String(accept||'').split(',').map(value=>value.trim().toLowerCase()).filter(Boolean)}
function extensionsFromAccept(accept){return new Set(acceptTokens(accept).filter(token=>token.startsWith('.')&&token.length>1).map(token=>token.slice(1)))}
function acceptsFile(input,file){const tokens=acceptTokens(input?.accept);if(!tokens.length)return true;const ext=extension(file?.name),mime=String(file?.type||'').toLowerCase();for(const token of tokens){if(token.startsWith('.')&&ext===token.slice(1))return true;if(token.endsWith('/*')&&mime.startsWith(token.slice(0,-1)))return true;if(token.includes('/')&&mime===token)return true}return false}
function compatibleInput(file){if(!doc)return null;for(const input of doc.querySelectorAll('input[type="file"]'))if(acceptsFile(input,file))return input;return null}
function dispatchError(error){try{doc?.dispatchEvent(new CustomEvent('inkdos:file-launch-error',{detail:{message:String(error?.message||error||'File launch failed')}}))}catch(_){}}
async function injectFile(file,input=compatibleInput(file)){if(!file)return false;if(!input||!acceptsFile(input,file))throw new Error('Unsupported file format for this InkDOS workspace.');if(typeof g.DataTransfer!=='function'||typeof g.File!=='function')throw new Error('This host cannot inject a file into the workspace.');const transfer=new DataTransfer();transfer.items.add(file);input.files=transfer.files;input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));return true}
async function routeFile(file){if(!file)return false;if(openHandler)return !!(await openHandler(file));pendingLaunchFiles.push(file);return true}
async function drainPending(){if(!openHandler||!pendingLaunchFiles.length)return;const files=pendingLaunchFiles.splice(0);for(const file of files){try{await openHandler(file)}catch(error){console.error('InkDOS launched-file open failed:',error);dispatchError(error)}}}
function setOpenHandler(handler){openHandler=typeof handler==='function'?handler:null;if(openHandler)Promise.resolve().then(drainPending);return !!openHandler}
async function openHandle(handle){if(!handle||handle.kind!=='file'||typeof handle.getFile!=='function')return false;return routeFile(await handle.getFile())}
async function consume(params){for(const handle of params?.files||[]){if(await openHandle(handle))return true}return false}
function requestPicker(input){if(!input||typeof g.showOpenFilePicker!=='function')return false;let pending;try{pending=g.showOpenFilePicker({multiple:false})}catch(_){return false}Promise.resolve(pending).then(async handles=>{const handle=handles?.[0];if(!handle)return;const file=await handle.getFile();if(!acceptsFile(input,file))throw new Error('Unsupported file format for this InkDOS workspace.');await injectFile(file,input)}).catch(error=>{if(error?.name==='AbortError')return;console.error('InkDOS File System Access open failed:',error);dispatchError(error)});return true}
function install(){const queue=g.launchQueue;if(!queue||typeof queue.setConsumer!=='function')return false;queue.setConsumer(params=>consume(params).catch(error=>{console.error('InkDOS launched-file open failed:',error);dispatchError(error)}));return true}
install();
g.InkDOSFileLaunch=Object.freeze({install,consume,openHandle,routeFile,injectFile,compatibleInput,acceptsFile,extensionsFromAccept,requestPicker,setOpenHandler});
})(globalThis);

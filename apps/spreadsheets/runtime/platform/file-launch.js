(function(g){'use strict';
const doc=typeof document!=='undefined'?document:null;
let openHandler=null,pendingLaunchFiles=[];
function extension(name){const m=String(name||'').toLowerCase().match(/\.([^.\\/]+)$/);return m?m[1]:''}
function acceptTokens(accept){return String(accept||'').split(',').map(value=>value.trim().toLowerCase()).filter(Boolean)}
function extensionsFromAccept(accept){return new Set(acceptTokens(accept).filter(token=>token.startsWith('.')&&token.length>1).map(token=>token.slice(1)))}
function acceptsFile(input,file){const tokens=acceptTokens(input?.accept);if(!tokens.length)return true;const ext=extension(file?.name),mime=String(file?.type||'').toLowerCase();for(const token of tokens){if(token.startsWith('.')&&ext===token.slice(1))return true;if(token.endsWith('/*')&&mime.startsWith(token.slice(0,-1)))return true;if(token.includes('/')&&mime===token)return true}return false}
function compatibleInput(file){if(!doc)return null;for(const input of doc.querySelectorAll('input[type="file"]'))if(acceptsFile(input,file))return input;return null}
function dispatchError(error){try{doc?.dispatchEvent(new CustomEvent('inkdos:file-launch-error',{detail:{message:String(error?.message||error||'File launch failed')}}))}catch(_){}}
async function injectFile(file,input=compatibleInput(file)){if(!file)return false;if(!input||!acceptsFile(input,file))throw new Error('Unsupported file format for this InkDOS workspace.');if(typeof g.DataTransfer!=='function'||typeof g.File!=='function')throw new Error('This host cannot inject a file into the workspace.');const transfer=new DataTransfer();transfer.items.add(file);input.files=transfer.files;input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));return true}
// Full version (Home engine switch, inkdos2:engine): a file opened from the system goes to the full tools on the
// InkDOS-tools origin (AGENTS.md, origin isolation), framed over this workspace; "Open in the Light version" opens it
// here instead. Word, Excel and PowerPoint files, legacy and OpenDocument ones included, go to the ONLYOFFICE editors
// (/editor?embed=1, which takes orders only from embedOrigin, this origin; the file comes with document:open-file).
// Apple iWork files, PDFs, e-books and plain text go to the InkDOS-tools viewers (pnk, PDF.js, foliate-js,
// CodeMirror) through the viewer protocol (InkDOS-tools viewers/viewer-embed.js: ready, open with the File, loaded).
const OFFICE_ORIGIN='https://inkdos-tools.github.io',OFFICE_EXT=new Set(['docx','doc','odt','rtf','xlsx','xls','ods','csv','pptx','ppt','odp','docm','dotx','dot','fodt','xlsm','xltx','fods','pptm','ppsx','pps','potx','fodp']);
const TOOLS=OFFICE_ORIGIN+'/InkDOS-tools/',VIEWER_PAGE={pages:'pnk/',numbers:'pnk/',key:'pnk/',pdf:'bentopdf/pdfjs-viewer/viewer.html?file=',epub:'epub/',mobi:'epub/',azw3:'epub/',fb2:'epub/',cbz:'epub/',txt:'txt/',md:'txt/',markdown:'txt/',log:'txt/',json:'txt/',yaml:'txt/',yml:'txt/',xml:'txt/',ini:'txt/',toml:'txt/'};
function engineComplete(){try{return g.localStorage?.getItem('inkdos2:engine')==='complete'&&!g.InkDOSDesktop&&doc?.documentElement?.dataset?.inkdosHost!=='tauri'}catch(_){return false}}
function fullEngine(file){return OFFICE_EXT.has(extension(file?.name))&&engineComplete()}
function viewerPage(file){return engineComplete()?VIEWER_PAGE[extension(file?.name)]||'':''}
// the full-screen layer over the workspace: a bar (name, "Open in the Light version") and the tool's frame
function launchShell(file,light,src){
 const pt=/^pt/i.test(String(g.InkDOSLocalization?.currentLanguage||doc.documentElement.lang||g.navigator?.language||'en'));
 const shell=doc.createElement('div');shell.className='inkdos-office-launch';shell.setAttribute('role','dialog');shell.setAttribute('aria-label','InkDOS Office');
 shell.style.cssText='position:fixed;inset:0;z-index:2147483646;display:flex;flex-direction:column;background:#f2f5f8';
 const bar=doc.createElement('div');bar.style.cssText='display:flex;align-items:center;gap:10px;padding:6px 10px;background:#fff;border-bottom:1px solid #e3e8ef;font:600 13px/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#192235';
 const title=doc.createElement('span');title.style.cssText='flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap';title.textContent=(pt?'Versão completa · ':'Full version · ')+file.name;
 const back=doc.createElement('button');back.type='button';back.textContent=pt?'Abrir na versão light':'Open in the Light version';
 back.style.cssText='height:32px;padding:0 12px;border:1px solid #d5dce6;border-radius:9px;background:#f0f2f5;color:#192235;font:inherit;cursor:pointer';
 bar.append(title,back);
 const frame=doc.createElement('iframe');frame.title='InkDOS Office';frame.style.cssText='flex:1;width:100%;border:0;background:#fff';frame.setAttribute('allow','clipboard-read; clipboard-write');frame.src=src;
 shell.append(bar,frame);doc.body.appendChild(shell);
 let onMessage=null;
 const toLight=()=>{if(onMessage)g.removeEventListener('message',onMessage);shell.remove();light(file)};
 back.addEventListener('click',toLight);
 return {frame,toLight,listen(handler){onMessage=handler;g.addEventListener('message',handler)}};
}
function openInOffice(file,light){
 if(!doc?.body)return false;
 const lang=String(g.InkDOSLocalization?.currentLanguage||doc.documentElement.lang||g.navigator?.language||'en');
 const LOCALE={pt:'pt',es:'es',de:'de',ja:'ja',zh:'zh-CN',fr:'fr',ru:'ru'}[lang.toLowerCase().split('-')[0]];
 const url=new URL('/editor',OFFICE_ORIGIN);url.searchParams.set('embed','1');url.searchParams.set('embedOrigin',g.location.origin);if(LOCALE)url.searchParams.set('locale',LOCALE);
 const {frame,toLight,listen}=launchShell(file,light,url.href);
 let sent=false,opened=false;
 listen(async function onMessage(event){
  if(event.origin!==OFFICE_ORIGIN||event.source!==frame.contentWindow||!event.data)return;
  if(event.data.type==='document:error'&&!opened){toLight();return}
  if(event.data.type==='document:opened'){opened=true;return}
  if(event.data.type!=='document:ready'||sent)return;
  sent=true;frame.contentWindow.postMessage({id:'inkdos-launch',type:'document:open-file',payload:{file,fileName:file.name}},OFFICE_ORIGIN);
 });
 return true;
}
function openInViewer(file,light,page){
 if(!doc?.body||!page)return false;
 const url=new URL(page,TOOLS);url.searchParams.set('embed','1');url.searchParams.set('inkdos-theme',doc.documentElement.dataset.theme==='dark'?'dark':'light');
 const {frame,toLight,listen}=launchShell(file,light,url.href);
 let sent=false;
 listen(function onMessage(event){
  if(event.origin!==OFFICE_ORIGIN||event.source!==frame.contentWindow||!event.data)return;
  if(event.data.type==='inkdos-viewer-loaded'&&!event.data.ok){toLight();return}
  if(event.data.type!=='inkdos-viewer-ready'||sent)return;
  sent=true;frame.contentWindow.postMessage({type:'inkdos-viewer-open',file},OFFICE_ORIGIN);
 });
 return true;
}
async function lightRoute(file){if(!file)return false;setCurrentFile(file);if(openHandler)return !!(await openHandler(file));pendingLaunchFiles.push(file);return true}
async function routeFile(file){if(!file)return false;if(fullEngine(file)&&openInOffice(file,lightRoute))return true;if(openInViewer(file,lightRoute,viewerPage(file)))return true;return lightRoute(file)}
async function drainPending(){if(!openHandler||!pendingLaunchFiles.length)return;const files=pendingLaunchFiles.splice(0);for(const file of files){try{await openHandler(file)}catch(error){console.error('InkDOS launched-file open failed:',error);dispatchError(error)}}}
function setOpenHandler(handler){openHandler=typeof handler==='function'?handler:null;if(openHandler)Promise.resolve().then(drainPending);return !!openHandler}
function rememberHandle(file,handle){try{const map=g.InkDOSFileHandles||(g.InkDOSFileHandles=new Map());map.set([file.name,file.size,file.lastModified].join('|'),handle)}catch(_){}}
// The writable original of the document now open (null when it came from a plain picker/drop).
function setCurrentFile(file){try{g.InkDOSCurrentHandle=file?(g.InkDOSFileHandles?.get([file.name,file.size,file.lastModified].join('|'))||null):null}catch(_){g.InkDOSCurrentHandle=null}}
async function openHandle(handle){if(!handle||handle.kind!=='file'||typeof handle.getFile!=='function')return false;const file=await handle.getFile();rememberHandle(file,handle);return routeFile(file)}
async function consume(params){for(const handle of params?.files||[]){if(await openHandle(handle))return true}return false}
function requestPicker(input){if(!input||typeof g.showOpenFilePicker!=='function')return false;let pending;try{pending=g.showOpenFilePicker({multiple:false})}catch(_){return false}Promise.resolve(pending).then(async handles=>{const handle=handles?.[0];if(!handle)return;const file=await handle.getFile();rememberHandle(file,handle);if(!acceptsFile(input,file))throw new Error('Unsupported file format for this InkDOS workspace.');await injectFile(file,input)}).catch(error=>{if(error?.name==='AbortError')return;console.error('InkDOS File System Access open failed:',error);dispatchError(error)});return true}
function install(){if(g.document)g.document.addEventListener('change',e=>{const t=e.target;if(t&&t.type==='file'&&t.files&&t.files[0]&&!/^image\//.test(String(t.accept||'').trim()))setCurrentFile(t.files[0])},true);const queue=g.launchQueue;if(!queue||typeof queue.setConsumer!=='function')return false;queue.setConsumer(params=>consume(params).catch(error=>{console.error('InkDOS launched-file open failed:',error);dispatchError(error)}));return true}
// Home hands a launched file over by storing it in IndexedDB and opening this page with #inkdos-launch=<id>.
function takeHandoff(){const m=/(?:^#|&)inkdos-launch=([A-Za-z0-9-]+)/.exec(g.location?.hash||'');if(!m||!g.indexedDB)return false;const id=m[1];try{g.history.replaceState(g.history.state,'',g.location.pathname+g.location.search)}catch(_){}let req;try{req=g.indexedDB.open('inkdos-launch-handoff',1)}catch(error){dispatchError(error);return false}req.onupgradeneeded=()=>req.result.createObjectStore('files');req.onerror=()=>dispatchError(req.error);req.onsuccess=()=>{const db=req.result;let tx;try{tx=db.transaction('files','readwrite')}catch(error){db.close();dispatchError(error);return}const store=tx.objectStore('files'),get=store.get(id);get.onsuccess=()=>{const v=get.result;store.delete(id);if(!v)return;const file=new File([v.data],v.name,{type:v.type||'',lastModified:v.lastModified||Date.now()});routeFile(file).catch(error=>{console.error('InkDOS launched-file open failed:',error);dispatchError(error)})};tx.oncomplete=tx.onabort=()=>db.close()};return true}
install();
takeHandoff();
g.InkDOSFileLaunch=Object.freeze({install,consume,openHandle,routeFile,injectFile,compatibleInput,acceptsFile,extensionsFromAccept,requestPicker,setOpenHandler});
})(globalThis);

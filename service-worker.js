'use strict';
const CACHE_NAME='inkdesk-shell-v0.20.2.3';
const CACHE_PREFIX='inkdesk-shell-';
const APP_SHELL=[
  './',
  './index.html',
  './manifest.webmanifest',
  './InkDesk.html',
  './Documents.html',
  './Spreadsheets.html',
  './Presentations.html',
  './PDF.html',
  './TXT.html',
  './EPUB.html',
  './modules/module-registry.js',
  './modules/module-loader.js',
  './modules/module-config.json',
  './modules/module-schema.json',
  './shared/hub.css',
  './shared/office-shell.css',
  './shared/office-shell.js',
  './shared/ui/design-tokens.css',
  './shared/ui/components.css',
  './shared/ui/application-shell.js',
  './shared/ui/shell-contract.json',
  './shared/ui/workspace-layout.css',
  './shared/ui/workspace-layout.js',
  './shared/ui/visual-foundation.css',
  './shared/office-runtime.js',
  './shared/file-lifecycle.js',
  './shared/local-recovery.js',
  './shared/file-router.js',
  './shared/hub-open.js',
  './shared/formula-engine.js',
  './shared/safe-dom.js',
  './shared/register-service-worker.js',
  './shared/vendor/jszip.min.js',
  './shared/vendor/pako_inflate.min.js',
  './assets/icons/office.png',
  './assets/icons/documents.png',
  './assets/icons/spreadsheets.png',
  './assets/icons/presentations.png',
  './assets/icons/pdf.png',
  './assets/icons/office.svg',
  './assets/icons/documents.svg',
  './assets/icons/spreadsheets.svg',
  './assets/icons/presentations.svg',
  './assets/icons/pdf.svg',
  './assets/icons/epub.svg',
  './assets/icons/epub.png',
  './assets/icons/txt.svg',
  './assets/icons/txt.png',
  './assets/icons/icon-catalog.json',
  './apps/documents/module.json',
  './apps/documents/index.html',
  './apps/documents/styles.css',
  './apps/documents/docx-parser.js',
  './apps/documents/docx-writer.js',
  './apps/documents/app.js',
  './apps/spreadsheets/module.json',
  './apps/spreadsheets/index.html',
  './apps/spreadsheets/styles.css',
  './apps/spreadsheets/xls-biff8-engine.js',
  './apps/spreadsheets/xlsx-engine.js',
  './apps/spreadsheets/app.js',
  './apps/spreadsheets/formula-reference.css',
  './apps/spreadsheets/formula-reference.js',
  './apps/spreadsheets/formula-editor.css',
  './apps/spreadsheets/formula-editor.js',
  './apps/presentations/module.json',
  './apps/presentations/index.html',
  './apps/presentations/styles.css',
  './apps/presentations/engine/compatibility.js',
  './apps/presentations/ui/inspector-controller.js',
  './apps/presentations/app.js',
  './apps/pdf/module.json',
  './apps/pdf/index.html',
  './apps/pdf/styles.css',
  './apps/pdf/text-selection-review.js',
  './apps/pdf/flatten-export.css',
  './apps/pdf/flatten-export.js',
  './apps/pdf/app.js',
  './apps/txt/module.json',
  './apps/txt/index.html',
  './apps/txt/styles.css',
  './apps/txt/app.js',
  './apps/epub/module.json',
  './apps/epub/index.html',
  './apps/epub/styles.css',
  './apps/epub/epub-parser.js',
  './apps/epub/app.js'
  ,'./shared/vendor/pdfjs/pdf.min.js'
  ,'./shared/vendor/pdfjs/pdf.worker.min.js'
];
const APP_SHELL_URLS=new Set(APP_SHELL.map(path=>new URL(path,self.registration.scope).href));
const NAVIGATION_PATHS=new Set([
  new URL('./index.html',self.registration.scope).pathname,
  new URL('./apps/documents/index.html',self.registration.scope).pathname,
  new URL('./apps/spreadsheets/index.html',self.registration.scope).pathname,
  new URL('./apps/presentations/index.html',self.registration.scope).pathname,
  new URL('./apps/pdf/index.html',self.registration.scope).pathname,
  new URL('./apps/txt/index.html',self.registration.scope).pathname,
  new URL('./apps/epub/index.html',self.registration.scope).pathname
]);
function canonicalCacheKey(request){
  const url=new URL(request.url);
  const canonical=new URL(url.href);
  canonical.search='';
  canonical.hash='';
  if(APP_SHELL_URLS.has(canonical.href)||(request.mode==='navigate'&&NAVIGATION_PATHS.has(canonical.pathname))){
    return new Request(canonical.href,{method:'GET'});
  }
  return request;
}

function isCacheableShellRequest(request){
  const key=canonicalCacheKey(request);
  return APP_SHELL_URLS.has(key.url);
}
async function installAppShell(){
  await caches.delete(CACHE_NAME);
  const cache=await caches.open(CACHE_NAME);
  try{
    await cache.addAll(APP_SHELL);
  }catch(error){
    await caches.delete(CACHE_NAME);
    console.error('InkDesk app-shell installation failed; the incomplete cache was removed.',error);
    throw error;
  }
}
async function removeOldCaches(){
  const keys=await caches.keys();
  await Promise.all(keys.filter(key=>key.startsWith(CACHE_PREFIX)&&key!==CACHE_NAME).map(key=>caches.delete(key)));
}

async function cacheResponse(cache,key,response){
  try{
    await cache.put(key,response);
  }catch(error){
    console.error('InkDesk could not update a cached application asset.',{url:key.url,error});
  }
}
async function respondWithShell(request){
  const key=canonicalCacheKey(request);
  const cache=await caches.open(CACHE_NAME);
  const cached=await cache.match(key);
  if(cached&&!cached.ok){
    await cache.delete(key);
  }
  try{
    const response=await fetch(request);
    if(response&&response.ok&&response.type!=='opaque')await cacheResponse(cache,key,response.clone());
    return response;
  }catch(error){
    const fallback=await cache.match(key);
    if(fallback)return fallback;
    console.error('InkDesk could not load an application asset from the network or cache.',{url:request.url,error});
    throw error;
  }
}
self.addEventListener('install',event=>{
  event.waitUntil(installAppShell().then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>{
  event.waitUntil(removeOldCaches().then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;
  if(!isCacheableShellRequest(request))return;
  event.respondWith(respondWithShell(request));
});
self.addEventListener('message',event=>{
  const data=event.data||{};
  if(data.type!=='inkdesk:clear-app-cache')return;
  event.waitUntil(caches.delete(CACHE_NAME).then(async()=>{
    await installAppShell();
    if(event.source&&typeof event.source.postMessage==='function')event.source.postMessage({type:'inkdesk:app-cache-reset',ok:true});
  }).catch(error=>{
    console.error('InkDesk app-cache recovery failed.',error);
    if(event.source&&typeof event.source.postMessage==='function')event.source.postMessage({type:'inkdesk:app-cache-reset',ok:false});
  }));
});

'use strict';

const CACHE_NAME='inkdesk-shell-v0.19.0-beta';
const APP_SHELL=[
  './',
  './index.html',
  './manifest.webmanifest',
  './shared/hub.css',
  './shared/office-shell.css',
  './shared/office-shell.js',
  './shared/office-runtime.js',
  './shared/register-service-worker.js',
  './shared/vendor/jszip.min.js',
  './shared/vendor/pako_inflate.min.js',
  './assets/icons/office.png',
  './assets/icons/documents.png',
  './assets/icons/spreadsheets.png',
  './assets/icons/presentations.png',
  './apps/documents/index.html',
  './apps/documents/styles.css',
  './apps/documents/docx-parser.js',
  './apps/documents/docx-writer.js',
  './apps/documents/app.js',
  './apps/spreadsheets/index.html',
  './apps/spreadsheets/styles.css',
  './apps/spreadsheets/xls-biff8-engine.js',
  './apps/spreadsheets/xlsx-engine.js',
  './apps/spreadsheets/app.js',
  './apps/presentations/index.html',
  './apps/presentations/styles.css',
  './apps/presentations/engine/compatibility.js',
  './apps/presentations/app.js'
];

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('inkdesk-shell-')&&key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});

self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;
  event.respondWith(caches.match(request,{ignoreSearch:true}).then(cached=>{
    if(cached)return cached;
    return fetch(request).then(response=>{
      if(!response||!response.ok||response.type==='opaque')return response;
      const copy=response.clone();
      caches.open(CACHE_NAME).then(cache=>cache.put(request,copy)).catch(()=>{});
      return response;
    });
  }));
});

(function registerInkDeskServiceWorker(){
'use strict';
if(!navigator.serviceWorker||!/^https?:$/.test(location.protocol))return;
const script=document.currentScript;
if(!script||!script.src)return;
const serviceWorkerUrl=new URL('../service-worker.js',script.src);
const scopeUrl=new URL('../',script.src);
navigator.serviceWorker.register(serviceWorkerUrl.href,{scope:scopeUrl.pathname}).catch(error=>{
  console.warn('InkDOS offline support could not be registered.',error);
});
})();

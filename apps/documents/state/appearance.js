(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{},KEY='inkdos2:documents:appearance',SUITE_KEY='inkdos2:appearance',VALID=new Set(['light','dark','system']);
let mode='system',media=null,listener=null,storageListener=null;
try{const shared=localStorage.getItem(SUITE_KEY),saved=localStorage.getItem(KEY);if(VALID.has(shared))mode=shared;else if(VALID.has(saved))mode=saved}catch(_){mode='system'}
function resolved(){if(mode==='light'||mode==='dark')return mode;return matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}
function apply(){const r=resolved(),root=document.documentElement;root.dataset.appearance=r;root.dataset.appearanceResolved=r;root.dataset.appearanceMode=mode;root.style.colorScheme=r;const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content=r==='dark'?'#16191f':'#f7f8fa';document.querySelectorAll('[data-appearance-choice],.popup-menu [data-appearance]').forEach(b=>{const choice=b.dataset.appearanceChoice||b.dataset.appearance;const active=choice===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active))});return r}
function persist(){try{localStorage.setItem(KEY,mode)}catch(_){}}
function publish(){try{localStorage.setItem(SUITE_KEY,mode)}catch(_){}}
function set(next,options){if(!VALID.has(next))return false;mode=next;persist();apply();if(!options||options.broadcast!==false)publish();return true}
function install(){if(typeof matchMedia==='function'){media=matchMedia('(prefers-color-scheme: dark)');listener=()=>{if(mode==='system')apply()};try{media.addEventListener('change',listener)}catch(_){try{media.addListener(listener)}catch(__){}}}storageListener=e=>{if(e.key===SUITE_KEY&&VALID.has(e.newValue)&&e.newValue!==mode)set(e.newValue,{broadcast:false})};try{global.addEventListener('storage',storageListener)}catch(_){}persist();apply()}
function destroy(){if(media&&listener){try{media.removeEventListener('change',listener)}catch(_){try{media.removeListener(listener)}catch(__){}}}if(storageListener){try{global.removeEventListener('storage',storageListener)}catch(_){}}}
NS.Appearance=Object.freeze({install,destroy,set,apply,get mode(){return mode},get resolved(){return resolved()}});
})(globalThis);

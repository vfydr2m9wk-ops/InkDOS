(function(global){'use strict';
// One InkDOS theme for every workspace (owner, 2026-10-09): the sun sets light or dark in the shared key, every open
// workspace follows it at once (storage event), and nothing follows the system theme.
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{},KEY='inkdos2:appearance',LEGACY_SUITE_KEY='inkdos2:appearance',VALID=new Set(['light','dark']);
let mode='light',media=null,listener=null,storageListener=null;
function suiteNewer(){try{const at=Number(localStorage.getItem(LEGACY_SUITE_KEY+':changedAt'))||0,own=Number(localStorage.getItem(KEY+':changedAt'))||0,m=localStorage.getItem(LEGACY_SUITE_KEY);return at>own&&VALID.has(m)?{mode:m,at}:null}catch(_){return null}}
function adoptSuite(s){try{localStorage.setItem(KEY,s.mode);localStorage.setItem(KEY+':changedAt',String(s.at))}catch(_){}return s.mode}
function read(){const suite=suiteNewer();if(suite)return adoptSuite(suite);try{const saved=localStorage.getItem(KEY);if(VALID.has(saved))return saved;const legacy=localStorage.getItem(LEGACY_SUITE_KEY);if(VALID.has(legacy)){localStorage.setItem(KEY,legacy);return legacy}}catch(_){}return 'light'}
mode=read();
function resolved(){return mode==='dark'?'dark':'light'}
function apply(){const r=resolved(),root=document.documentElement;root.dataset.appearance=r;root.dataset.appearanceResolved=r;root.dataset.appearanceMode=mode;root.dataset.theme=r;root.style.colorScheme=r;const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content=r==='dark'?'#16191f':'#f7f8fa';document.querySelectorAll('[data-appearance-choice],.popup-menu [data-appearance]').forEach(b=>{const choice=b.dataset.appearanceChoice||b.dataset.appearance;const active=choice===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active))});return r}
function persist(){try{localStorage.setItem(KEY,mode)}catch(_){}}
function set(next,{persist:shouldPersist=true}={}){if(!VALID.has(next))return false;mode=next;if(shouldPersist){persist();try{localStorage.setItem(KEY+':changedAt',String(Date.now()))}catch(_){}}apply();return true}
function install(){storageListener=e=>{if(e.key===KEY&&VALID.has(e.newValue)&&e.newValue!==mode)set(e.newValue,{persist:false});else if(e.key===LEGACY_SUITE_KEY+':changedAt'){const suite=suiteNewer();if(suite)set(adoptSuite(suite),{persist:false})}};try{global.addEventListener('storage',storageListener)}catch(_){}persist();apply()}
function destroy(){if(media&&listener){try{media.removeEventListener('change',listener)}catch(_){try{media.removeListener(listener)}catch(__){}}}if(storageListener){try{global.removeEventListener('storage',storageListener)}catch(_){}}}
NS.Appearance=Object.freeze({install,destroy,set,apply,get mode(){return mode},get resolved(){return resolved()}});
})(globalThis);

(function(g){'use strict';
// One InkDOS theme for every workspace (owner, 2026-10-09): the sun sets light or dark in the shared key, every open
// workspace follows it at once (storage event), and nothing follows the system theme.
const NS=g.InkDOS2=g.InkDOS2||{};
const STORAGE_KEY='inkdos2:appearance';
const LEGACY_SUITE_KEY='inkdos2:appearance';
const MODES=new Set(['light','dark']);
function normalize(value){return MODES.has(value)?value:'light'}
function resolve(mode){return mode==='dark'?'dark':'light'}
function suiteNewer(){try{const ls=g.localStorage;if(!ls)return null;const at=Number(ls.getItem(LEGACY_SUITE_KEY+':changedAt'))||0,own=Number(ls.getItem(STORAGE_KEY+':changedAt'))||0,m=ls.getItem(LEGACY_SUITE_KEY);return at>own&&MODES.has(m)?{mode:m,at}:null}catch(_){return null}}
function adoptSuite(s){try{g.localStorage.setItem(STORAGE_KEY,s.mode);g.localStorage.setItem(STORAGE_KEY+':changedAt',String(s.at))}catch(_){}return s.mode}
function stamp(){try{if(g.localStorage)g.localStorage.setItem(STORAGE_KEY+':changedAt',String(Date.now()))}catch(_){}}
function read(){const suite=suiteNewer();if(suite)return adoptSuite(suite);try{const saved=g.localStorage&&g.localStorage.getItem(STORAGE_KEY);if(MODES.has(saved))return saved;const legacy=g.localStorage&&g.localStorage.getItem(LEGACY_SUITE_KEY);if(MODES.has(legacy)){g.localStorage&&g.localStorage.setItem(STORAGE_KEY,legacy);return legacy}return 'light'}catch(_){return 'light'}}
function write(mode){try{if(g.localStorage)g.localStorage.setItem(STORAGE_KEY,mode)}catch(_){}}
let mode=read();
function syncButtons(){for(const b of document.querySelectorAll('[data-appearance-mode],[data-appearance-choice]')){const choice=b.dataset.appearanceMode||b.dataset.appearanceChoice;const active=choice===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',active?'true':'false')}}
function apply(next,{persist=true}={}){mode=normalize(next);const resolved=resolve(mode);document.documentElement.dataset.appearance=resolved;document.documentElement.dataset.appearanceResolved=resolved;document.documentElement.dataset.appearanceMode=mode;document.documentElement.dataset.theme=resolved;document.documentElement.style.colorScheme=resolved;const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.setAttribute('content',resolved==='dark'?'#16191f':'#f7f8fa');syncButtons();if(persist)write(mode);return resolved}
function bind(){for(const b of document.querySelectorAll('[data-appearance-mode]'))b.addEventListener('click',()=>{apply(b.dataset.appearanceMode);stamp()});syncButtons()}
try{g.addEventListener('storage',e=>{if(e.key===STORAGE_KEY&&MODES.has(e.newValue)&&e.newValue!==mode)apply(e.newValue,{persist:false});else if(e.key===LEGACY_SUITE_KEY+':changedAt'){const suite=suiteNewer();if(suite)apply(adoptSuite(suite),{persist:false})}})}catch(_){}
apply(mode,{persist:true});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else bind();
NS.AppearanceController=Object.freeze({get mode(){return mode},get resolved(){return resolve(mode)},apply});
})(globalThis);

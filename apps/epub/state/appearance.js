(function(g){'use strict';
const NS=g.InkDOS2Epub=g.InkDOS2Epub||{};
const STORAGE_KEY='inkdos2:epub:appearance';
const SUITE_KEY='inkdos2:appearance';
const MODES=new Set(['light','dark','system']);
const media=typeof g.matchMedia==='function'?g.matchMedia('(prefers-color-scheme: dark)'):null;
function normalize(value){return MODES.has(value)?value:'system'}
function resolve(mode){return mode==='system'?(media&&media.matches?'dark':'light'):mode}
function read(){try{const shared=g.localStorage&&g.localStorage.getItem(SUITE_KEY);if(MODES.has(shared))return shared;return normalize(g.localStorage&&g.localStorage.getItem(STORAGE_KEY))}catch(_){return 'system'}}
function write(mode){try{if(g.localStorage)g.localStorage.setItem(STORAGE_KEY,mode)}catch(_){}}
function publish(mode){try{if(g.localStorage)g.localStorage.setItem(SUITE_KEY,mode)}catch(_){}}
let mode=read();
function syncButtons(){for(const b of document.querySelectorAll('[data-appearance-mode]')){const active=b.dataset.appearanceMode===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',active?'true':'false')}}
function apply(next,{persist=true,broadcast=true}={}){mode=normalize(next);const resolved=resolve(mode);document.documentElement.dataset.appearance=mode;document.documentElement.dataset.theme=resolved;document.documentElement.style.colorScheme=resolved;const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.setAttribute('content',resolved==='dark'?'#171a20':'#eef1f5');syncButtons();if(persist)write(mode);if(broadcast)publish(mode);return resolved}
function bind(){for(const b of document.querySelectorAll('[data-appearance-mode]'))b.addEventListener('click',()=>apply(b.dataset.appearanceMode));syncButtons()}
if(media){const changed=()=>{if(mode==='system')apply('system',{persist:false,broadcast:false})};if(media.addEventListener)media.addEventListener('change',changed);else if(media.addListener)media.addListener(changed)}
try{g.addEventListener('storage',e=>{if(e.key===SUITE_KEY&&MODES.has(e.newValue)&&e.newValue!==mode)apply(e.newValue,{broadcast:false})})}catch(_){}
apply(mode,{persist:true,broadcast:false});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else bind();
NS.AppearanceController=Object.freeze({get mode(){return mode},get resolved(){return resolve(mode)},apply});
})(globalThis);

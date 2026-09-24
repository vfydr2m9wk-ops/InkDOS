(function(g){'use strict';
const NS=g.InkDOS2Epub=g.InkDOS2Epub||{};
const STORAGE_KEY='inkdos2:epub:appearance';
const LEGACY_SUITE_KEY='inkdos2:appearance';
const MODES=new Set(['light','dark','system']);
const media=typeof g.matchMedia==='function'?g.matchMedia('(prefers-color-scheme: dark)'):null;
function normalize(value){return MODES.has(value)?value:'system'}
function resolve(mode){return mode==='system'?(media&&media.matches?'dark':'light'):mode}
function read(){try{const saved=g.localStorage&&g.localStorage.getItem(STORAGE_KEY);if(MODES.has(saved))return saved;const legacy=g.localStorage&&g.localStorage.getItem(LEGACY_SUITE_KEY);if(MODES.has(legacy)){g.localStorage&&g.localStorage.setItem(STORAGE_KEY,legacy);return legacy}return 'system'}catch(_){return 'system'}}
function write(mode){try{if(g.localStorage)g.localStorage.setItem(STORAGE_KEY,mode)}catch(_){}}
let mode=read();
function syncButtons(){for(const b of document.querySelectorAll('[data-appearance-mode],[data-appearance-choice]')){const choice=b.dataset.appearanceMode||b.dataset.appearanceChoice;const active=choice===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',active?'true':'false')}}
function apply(next,{persist=true}={}){mode=normalize(next);const resolved=resolve(mode);document.documentElement.dataset.appearance=resolved;document.documentElement.dataset.appearanceResolved=resolved;document.documentElement.dataset.appearanceMode=mode;document.documentElement.dataset.theme=resolved;document.documentElement.style.colorScheme=resolved;const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.setAttribute('content',resolved==='dark'?'#16191f':'#f7f8fa');syncButtons();if(persist)write(mode);return resolved}
function bind(){for(const b of document.querySelectorAll('[data-appearance-mode]'))b.addEventListener('click',()=>apply(b.dataset.appearanceMode));syncButtons()}
if(media){const changed=()=>{if(mode==='system')apply('system',{persist:false})};if(media.addEventListener)media.addEventListener('change',changed);else if(media.addListener)media.addListener(changed)}
try{g.addEventListener('storage',e=>{if(e.key===STORAGE_KEY&&MODES.has(e.newValue)&&e.newValue!==mode)apply(e.newValue,{persist:false})})}catch(_){}
apply(mode,{persist:true});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else bind();
NS.AppearanceController=Object.freeze({get mode(){return mode},get resolved(){return resolve(mode)},apply});
})(globalThis);

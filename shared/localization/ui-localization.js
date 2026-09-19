(function(root){'use strict';
const DEFAULT_LANGUAGE='en';
const LANGUAGES=Object.freeze([
 {code:'en',label:'English'},
 {code:'pt-BR',label:'Português'},
 {code:'es',label:'Español'},
 {code:'de',label:'Deutsch'},
 {code:'fr',label:'Français'},
 {code:'zh-CN',label:'中文（简体）'},
 {code:'ja',label:'日本語'},
 {code:'ru',label:'Русский'}
]);
const VALID=new Set(LANGUAGES.map(item=>item.code));
const ALLOWED_ATTRIBUTES=Object.freeze(['title','aria-label','placeholder']);
const EXPLICIT_ROOT_SELECTOR='[data-inkdos-i18n-root]';
const SAFE_ROOT_SELECTORS=Object.freeze(['header.topbar','.formatbar','.start-state','.statusbar','#generalMenu','.zoom-popover','.inkdos-settings-strip','.inkdos-settings-popover','.context-drawer .drawer-head','.context-drawer .sidebar-tabs','.context-drawer .search-box','.context-drawer .search-meta','#inkdosDesktopUpdateModal',EXPLICIT_ROOT_SELECTOR]);
const SKIP_SELECTOR='script,style,textarea,[contenteditable="true"],[data-inkdos-user-content]';
const doc=typeof document!=='undefined'?document:null;
const packages=root.InkDOSLocalePackages=root.InkDOSLocalePackages||Object.create(null);
const originalText=new WeakMap(),originalAttributes=new WeakMap();
let language=DEFAULT_LANGUAGE,dictionary=Object.freeze({}),storageKey=null,observer=null,applyQueued=false;
const base=(function(){if(!doc)return'';const src=doc.currentScript?.src||'';return src?src.slice(0,src.lastIndexOf('/')+1):''})();
function normalizeLanguage(value){return VALID.has(value)?value:DEFAULT_LANGUAGE}
function packagePath(value){const code=normalizeLanguage(value);return code===DEFAULT_LANGUAGE?null:code+'.js'}
function translateValue(source,key,fallback){return source&&Object.prototype.hasOwnProperty.call(source,key)?source[key]:fallback}
function rememberText(node){if(!originalText.has(node))originalText.set(node,node.nodeValue);return originalText.get(node)}
function rememberAttribute(element,name){let saved=originalAttributes.get(element);if(!saved){saved=Object.create(null);originalAttributes.set(element,saved)}if(!(name in saved))saved[name]=element.getAttribute(name);return saved[name]}
function safeRoots(){if(!doc)return[];const roots=[];for(const selector of SAFE_ROOT_SELECTORS){for(const element of doc.querySelectorAll(selector)){if(!roots.includes(element))roots.push(element)}}return roots}
function isSkipped(node,rootElement){const parent=node.parentElement;if(!parent)return true;if(parent.closest(SKIP_SELECTOR))return true;if(parent.closest('.pages-host,.sheet-host,.slides-host,.pdf-pages,.epub-content,.editor-surface'))return true;return !rootElement.contains(parent)}
function interpolate(value,params){const text=String(value??'');if(!params||typeof params!=='object')return text;return text.replace(/\{([A-Za-z0-9_]+)\}/g,(match,key)=>Object.prototype.hasOwnProperty.call(params,key)?String(params[key]):match)}
function t(key,params){const raw=String(key??'');const value=language===DEFAULT_LANGUAGE?raw:translateValue(dictionary,raw,raw);return interpolate(value,params)}
function translatedText(raw,source){if(typeof raw!=='string')return raw;const match=raw.match(/^(\s*)(.*?)(\s*)$/s);if(!match)return raw;const key=match[2];if(!key)return raw;return match[1]+interpolate(translateValue(source,key,key))+match[3]}
function applyText(rootElement,source){if(!doc?.createTreeWalker)return;const walker=doc.createTreeWalker(rootElement,4);let node;while((node=walker.nextNode())){if(isSkipped(node,rootElement))continue;const raw=rememberText(node);node.nodeValue=language===DEFAULT_LANGUAGE?raw:translatedText(raw,source)}}
function applyAttributes(rootElement,source){for(const name of ALLOWED_ATTRIBUTES){for(const element of rootElement.querySelectorAll('['+name+']')){if(element.closest(SKIP_SELECTOR))continue;const raw=rememberAttribute(element,name);if(raw==null)continue;element.setAttribute(name,language===DEFAULT_LANGUAGE?raw:translateValue(source,raw,raw))}if(rootElement.hasAttribute?.(name)){const raw=rememberAttribute(rootElement,name);if(raw!=null)rootElement.setAttribute(name,language===DEFAULT_LANGUAGE?raw:translateValue(source,raw,raw))}}}
function apply(){if(!doc)return language;const source=language===DEFAULT_LANGUAGE?Object.freeze({}):dictionary;for(const rootElement of safeRoots()){applyText(rootElement,source);applyAttributes(rootElement,source)}try{doc.dispatchEvent(new CustomEvent('inkdos:language',{detail:{language}}))}catch(_){}return language}
function scheduleApply(){if(applyQueued)return;applyQueued=true;const run=()=>{applyQueued=false;apply()};if(typeof root.requestAnimationFrame==='function')root.requestAnimationFrame(run);else setTimeout(run,0)}
function observe(){if(!doc||observer||typeof MutationObserver!=='function')return;observer=new MutationObserver(records=>{if(records.some(record=>record.addedNodes&&record.addedNodes.length))scheduleApply()});const start=()=>{if(doc.body)observer.observe(doc.body,{childList:true,subtree:true})};if(doc.body)start();else doc.addEventListener('DOMContentLoaded',start,{once:true})}
function packageFor(code){const item=packages[code];return item&&item.translations?item.translations:null}
function packageElement(code){return doc?.querySelector('script[data-inkdos-locale-package="'+code+'"]')||null}
function purgePackages(keep){for(const item of LANGUAGES){const code=item.code;if(code===DEFAULT_LANGUAGE||code===keep)continue;try{delete packages[code]}catch(_){}packageElement(code)?.remove()}if(keep===DEFAULT_LANGUAGE){for(const item of LANGUAGES){if(item.code===DEFAULT_LANGUAGE)continue;try{delete packages[item.code]}catch(_){}packageElement(item.code)?.remove()}}}
function loadPackage(value){const code=normalizeLanguage(value);if(code===DEFAULT_LANGUAGE)return Promise.resolve(null);purgePackages(code);const existing=packageFor(code);if(existing)return Promise.resolve(existing);if(!doc)return Promise.reject(new Error('Locale package requires a document environment.'));return new Promise((resolve,reject)=>{const prior=packageElement(code);if(prior){prior.addEventListener('load',()=>resolve(packageFor(code)||Object.freeze({})),{once:true});prior.addEventListener('error',()=>reject(new Error('Unable to load locale '+code)),{once:true});return}const script=doc.createElement('script');script.setAttribute('data-inkdos-locale-package',code);script.src=base+'locales/'+packagePath(code);script.async=true;script.addEventListener('load',()=>resolve(packageFor(code)||Object.freeze({})),{once:true});script.addEventListener('error',()=>reject(new Error('Unable to load locale '+code)),{once:true});(doc.head||doc.documentElement).appendChild(script)})}
function persist(code){if(!storageKey)return;try{root.localStorage?.setItem(storageKey,code)}catch(_){}}
async function setLanguage(value,options){const code=normalizeLanguage(value);if(options&&typeof options.storageKey==='string')storageKey=options.storageKey;language=code;persist(code);if(code===DEFAULT_LANGUAGE){purgePackages(DEFAULT_LANGUAGE);dictionary=Object.freeze({});apply();return language}try{dictionary=await loadPackage(code)}catch(_){language=DEFAULT_LANGUAGE;purgePackages(DEFAULT_LANGUAGE);dictionary=Object.freeze({});persist(language)}apply();return language}
function readLanguage(key){storageKey=typeof key==='string'?key:storageKey;if(!storageKey)return DEFAULT_LANGUAGE;try{return normalizeLanguage(root.localStorage?.getItem(storageKey))}catch(_){return DEFAULT_LANGUAGE}}
function install(options){const key=options&&typeof options.storageKey==='string'?options.storageKey:null;if(key)storageKey=key;observe();return setLanguage(readLanguage(storageKey),{storageKey})}
observe();
root.InkDOSLocalization=Object.freeze({DEFAULT_LANGUAGE,ALLOWED_ATTRIBUTES,EXPLICIT_ROOT_SELECTOR,languages:LANGUAGES,normalizeLanguage,packagePath,translateValue,interpolate,t,loadPackage,setLanguage,readLanguage,install,apply,get currentLanguage(){return language},get storageKey(){return storageKey}});
})(globalThis);

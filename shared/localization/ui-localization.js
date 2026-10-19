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
let language=DEFAULT_LANGUAGE,dictionary=Object.freeze({}),storageKey=null,legacyStorageKeys=[],observer=null,applyQueued=false,storageBound=false;
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
function applyText(rootElement,source){if(!doc?.createTreeWalker)return;const walker=doc.createTreeWalker(rootElement,4);let node;while((node=walker.nextNode())){if(isSkipped(node,rootElement))continue;const raw=rememberText(node),next=language===DEFAULT_LANGUAGE?raw:translatedText(raw,source);if(node.nodeValue!==next)node.nodeValue=next}}
function applyAttributes(rootElement,source){for(const name of ALLOWED_ATTRIBUTES){for(const element of rootElement.querySelectorAll('['+name+']')){if(element.closest(SKIP_SELECTOR))continue;const raw=rememberAttribute(element,name);if(raw==null)continue;const next=language===DEFAULT_LANGUAGE?raw:translateValue(source,raw,raw);if(element.getAttribute(name)!==next)element.setAttribute(name,next)}if(rootElement.hasAttribute?.(name)){const raw=rememberAttribute(rootElement,name);if(raw!=null){const next=language===DEFAULT_LANGUAGE?raw:translateValue(source,raw,raw);if(rootElement.getAttribute(name)!==next)rootElement.setAttribute(name,next)}}}}
function apply(){if(!doc)return language;if(doc.documentElement.lang!==language)doc.documentElement.lang=language;const source=language===DEFAULT_LANGUAGE?Object.freeze({}):dictionary;for(const rootElement of safeRoots()){applyText(rootElement,source);applyAttributes(rootElement,source)}try{doc.dispatchEvent(new CustomEvent('inkdos:language',{detail:{language}}))}catch(_){}return language}
function scheduleApply(){if(applyQueued)return;applyQueued=true;const run=()=>{applyQueued=false;apply()};if(typeof root.requestAnimationFrame==='function')root.requestAnimationFrame(run);else setTimeout(run,0)}
function observe(){if(!doc||observer||typeof MutationObserver!=='function')return;observer=new MutationObserver(records=>{if(records.some(record=>record.addedNodes&&record.addedNodes.length))scheduleApply()});const start=()=>{if(doc.body)observer.observe(doc.body,{childList:true,subtree:true})};if(doc.body)start();else doc.addEventListener('DOMContentLoaded',start,{once:true})}
function packageFor(code){const item=packages[code];return item&&item.translations?item.translations:null}
function packageElement(code){return doc?.querySelector('script[data-inkdos-locale-package="'+code+'"]')||null}
function purgePackages(keep){for(const item of LANGUAGES){const code=item.code;if(code===DEFAULT_LANGUAGE||code===keep)continue;try{delete packages[code]}catch(_){}packageElement(code)?.remove()}if(keep===DEFAULT_LANGUAGE){for(const item of LANGUAGES){if(item.code===DEFAULT_LANGUAGE)continue;try{delete packages[item.code]}catch(_){}packageElement(item.code)?.remove()}}}
function loadPackage(value){const code=normalizeLanguage(value);if(code===DEFAULT_LANGUAGE)return Promise.resolve(null);purgePackages(code);const existing=packageFor(code);if(existing)return Promise.resolve(existing);if(!doc)return Promise.reject(new Error('Locale package requires a document environment.'));return new Promise((resolve,reject)=>{const prior=packageElement(code);if(prior){prior.addEventListener('load',()=>resolve(packageFor(code)||Object.freeze({})),{once:true});prior.addEventListener('error',()=>reject(new Error('Unable to load locale '+code)),{once:true});return}const script=doc.createElement('script');script.setAttribute('data-inkdos-locale-package',code);script.src=base+'locales/'+packagePath(code);script.async=true;script.addEventListener('load',()=>resolve(packageFor(code)||Object.freeze({})),{once:true});script.addEventListener('error',()=>reject(new Error('Unable to load locale '+code)),{once:true});(doc.head||doc.documentElement).appendChild(script)})}
function persist(code){if(!storageKey)return;try{root.localStorage?.setItem(storageKey,code);root.localStorage?.setItem(storageKey+':changedAt',String(Date.now()))}catch(_){}}
async function setLanguage(value,options){const code=normalizeLanguage(value);if(options&&typeof options.storageKey==='string')storageKey=options.storageKey;const shouldPersist=options?.persist!==false;language=code;if(shouldPersist)persist(code);if(code===DEFAULT_LANGUAGE){purgePackages(DEFAULT_LANGUAGE);if(shouldPersist)dropCachedPackages();dictionary=Object.freeze({});apply();return language}try{dictionary=await loadPackage(code)}catch(_){language=DEFAULT_LANGUAGE;purgePackages(DEFAULT_LANGUAGE);dictionary=Object.freeze({});if(shouldPersist)persist(language)}apply();return language}
function readLanguage(key,legacyKeys=legacyStorageKeys){storageKey=typeof key==='string'?key:storageKey;if(!storageKey)return DEFAULT_LANGUAGE;try{const ls=root.localStorage;/* Home is the master: a Home language change newer than this app's own choice wins. */for(const legacyKey of legacyKeys||[]){if(!ls||!legacyKey||legacyKey===storageKey)continue;const at=Number(ls.getItem(legacyKey+':changedAt'))||0,v=ls.getItem(legacyKey);if(v!=null&&at>(Number(ls.getItem(storageKey+':changedAt'))||0)){const code=normalizeLanguage(v);ls.setItem(storageKey,code);ls.setItem(storageKey+':changedAt',String(at));return code}}const saved=root.localStorage?.getItem(storageKey);if(saved!=null)return normalizeLanguage(saved);for(const legacyKey of legacyKeys||[]){if(!legacyKey||legacyKey===storageKey)continue;const legacy=root.localStorage?.getItem(legacyKey);if(legacy!=null){const migrated=normalizeLanguage(legacy);root.localStorage?.setItem(storageKey,migrated);return migrated}}}catch(_){}return DEFAULT_LANGUAGE}
function bindStorage(){if(storageBound||typeof root.addEventListener!=='function')return;storageBound=true;root.addEventListener('storage',event=>{if(!storageKey||event.key!==storageKey)return;setLanguage(event.newValue,{storageKey,persist:false}).catch(()=>{})})}
function install(options){const key=options&&typeof options.storageKey==='string'?options.storageKey:null;if(key)storageKey=key;legacyStorageKeys=Array.isArray(options?.legacyStorageKeys)?options.legacyStorageKeys.filter(x=>typeof x==='string'&&x):[];observe();bindStorage();return setLanguage(readLanguage(storageKey,legacyStorageKeys),{storageKey})}
/* Language packages are optional downloads: English is built in and only one package stays on the device
   (the service worker caches a package when it is first used and removes the previous one). Before switching,
   chooseLanguage() shows the same notice everywhere: what is translated, what stays in English and the space used. */
const PACKAGE_BYTES=Object.freeze({"pt-BR":34445,"es":34514,"de":34869,"fr":35992,"zh-CN":30763,"ja":38152,"ru":46936});
function dropCachedPackages(){try{root.navigator?.serviceWorker?.controller?.postMessage('inkdos:drop-locales')}catch(_){}}
function sizeLabel(bytes){const kb=Math.max(1,Math.round(bytes/1024));return kb.toLocaleString(language)+' KB'}
const NOTICE_CSS='.inkdos-language-notice{position:fixed;inset:0;z-index:10100;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(10,14,20,.45);font:14px/1.4 system-ui,-apple-system,sans-serif}'+
 '.inkdos-language-notice[hidden]{display:none!important}'+
 '.inkdos-language-notice-box{width:min(420px,100%);max-height:calc(100vh - 32px);overflow:auto;box-sizing:border-box;padding:16px;border:1px solid var(--line,var(--frame-line,#d7dce2));border-radius:14px;background:var(--chrome,var(--frame-chrome,#fff));color:var(--text,var(--frame-text,#202124));overflow-wrap:anywhere}'+
 '.inkdos-language-notice h2{margin:0 0 8px;font-size:17px}.inkdos-language-notice h3{margin:12px 0 4px;font-size:14px}.inkdos-language-notice ul{margin:0;padding:0 0 0 18px}.inkdos-language-notice p{margin:8px 0}'+
 '.inkdos-language-notice-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:14px}'+
 '.inkdos-language-notice button{font:inherit;padding:8px 12px;border-radius:9px;border:1px solid var(--line,var(--frame-line,#d7dce2));background:transparent;color:inherit;cursor:pointer}'+
 '.inkdos-language-notice button[data-language-confirm]{background:#1a73e8;border-color:#1a73e8;color:#fff;font-weight:600}';
function noticeElement(tag,text){const el=doc.createElement(tag);if(text!=null)el.textContent=text;return el}
function noticeList(items){const list=doc.createElement('ul');for(const item of items)list.appendChild(noticeElement('li',item));return list}
function showNotice(code){
 return new Promise(resolve=>{
  if(!doc?.body){resolve(true);return}
  if(!doc.querySelector('style[data-inkdos-language-notice]')){const style=doc.createElement('style');style.dataset.inkdosLanguageNotice='';style.textContent=NOTICE_CSS;(doc.head||doc.documentElement).appendChild(style)}
  const label=LANGUAGES.find(item=>item.code===code)?.label||code,currentLabel=LANGUAGES.find(item=>item.code===language)?.label||language;
  const layer=noticeElement('div'),box=noticeElement('div');layer.className='inkdos-language-notice';box.className='inkdos-language-notice-box';
  box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label',label);box.lang=code;layer.appendChild(box);
  box.appendChild(noticeElement('h2',label));
  const current=PACKAGE_BYTES[language]||0;
  if(code===DEFAULT_LANGUAGE){
   box.appendChild(noticeElement('p',t('English is built in, so nothing is downloaded.')));
   box.appendChild(noticeElement('p',t('The {name} package will be removed from this device, freeing {size}.',{name:currentLabel,size:sizeLabel(current)})));
  }else{
   box.appendChild(noticeElement('h3',t('Translated')));
   box.appendChild(noticeList([t('The InkDOS home screen'),t('Menus, buttons and messages of Documents, Spreadsheets, Presentations, PDF, Plain text and EPUB reader')]));
   box.appendChild(noticeElement('h3',t('Stays in English')));
   box.appendChild(noticeList([t('Style and font names, and some less common messages'),t('The content of your files (it is never translated)')]));
   box.appendChild(noticeElement('h3',t('Space')));
   const size=PACKAGE_BYTES[code]||0,diff=size-current;
   box.appendChild(noticeElement('p',t('Download: {size}.',{size:sizeLabel(size)})));
   box.appendChild(noticeElement('p',diff>=0?t('This device will use {size} more than now.',{size:sizeLabel(diff)}):t('This device will use {size} less than now.',{size:sizeLabel(-diff)})));
   if(language!==DEFAULT_LANGUAGE)box.appendChild(noticeElement('p',t('The {name} package will be removed. Only one language package is kept at a time.',{name:currentLabel})));
  }
  const actions=noticeElement('div'),cancel=noticeElement('button',t('Cancel')),confirm=noticeElement('button',code===DEFAULT_LANGUAGE?t('Switch to English'):t('Download and switch'));
  actions.className='inkdos-language-notice-actions';cancel.type=confirm.type='button';confirm.dataset.languageConfirm='';actions.append(cancel,confirm);box.appendChild(actions);
  const finish=answer=>{layer.remove();doc.removeEventListener('keydown',onKey,true);resolve(answer)};
  const onKey=event=>{if(event.key==='Escape'){event.preventDefault();finish(false)}};
  cancel.addEventListener('click',()=>finish(false));confirm.addEventListener('click',()=>finish(true));
  layer.addEventListener('click',event=>{if(event.target===layer)finish(false)});doc.addEventListener('keydown',onKey,true);
  doc.body.appendChild(layer);confirm.focus?.();
 });
}
async function chooseLanguage(value,options){
 const code=normalizeLanguage(value);
 if(code===language)return language;
 if(!await showNotice(code))return language;
 const result=await setLanguage(code,options);
 if(result!==code&&doc?.defaultView?.alert){try{doc.defaultView.alert(t('The language package could not be downloaded. Check the internet connection and try again.'))}catch(_){}}
 return result;
}
observe();
root.InkDOSLocalization=Object.freeze({DEFAULT_LANGUAGE,ALLOWED_ATTRIBUTES,EXPLICIT_ROOT_SELECTOR,languages:LANGUAGES,packageBytes:PACKAGE_BYTES,normalizeLanguage,packagePath,translateValue,interpolate,t,loadPackage,setLanguage,chooseLanguage,readLanguage,install,apply,get currentLanguage(){return language},get storageKey(){return storageKey}});
})(globalThis);

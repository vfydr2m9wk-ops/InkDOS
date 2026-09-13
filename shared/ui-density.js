(function(root){'use strict';
const STORAGE_KEY='inkdos2:ui-density',VALID=new Set(['auto','desktop','mobile']),THRESHOLD=900,POINTER_QUERY='(hover: hover) and (pointer: fine)',ATTR='data-ui-density',PREF_ATTR='data-ui-density-preference';
const doc=typeof document!=='undefined'?document:null;
function normalize(value){return VALID.has(value)?value:'auto'}
function currentEnvironment(){const width=doc?.documentElement?.clientWidth||Number(root.innerWidth)||0;let finePointer=false;try{finePointer=typeof root.matchMedia==='function'&&root.matchMedia(POINTER_QUERY).matches}catch(_){}return{width,finePointer}}
function resolve(value='auto',environment={}){const preference=normalize(value);if(preference==='desktop'||preference==='mobile')return preference;const fallback=currentEnvironment(),width=Number(environment.width??fallback.width)||0,finePointer=environment.finePointer==null?!!fallback.finePointer:!!environment.finePointer;return width>=THRESHOLD&&finePointer?'desktop':'mobile'}
function read(){try{return normalize(root.localStorage?.getItem(STORAGE_KEY))}catch(_){return'auto'}}
let preference=read(),effective=resolve(preference);
function apply(value=preference,environment){preference=normalize(value);effective=resolve(preference,environment||currentEnvironment());const element=doc?.documentElement;if(element){element.setAttribute(ATTR,effective);element.setAttribute(PREF_ATTR,preference)}syncControls();return effective}
function write(value){try{root.localStorage?.setItem(STORAGE_KEY,value)}catch(_){}}
function announce(){try{doc?.dispatchEvent?.(new CustomEvent('inkdos:ui-density',{detail:{preference,effective}}))}catch(_){}}
function set(value){preference=normalize(value);write(preference);apply(preference);announce();return effective}
function syncControls(){if(!doc)return;for(const button of doc.querySelectorAll('[data-inkdos-density-mode]')){const active=button.dataset.inkdosDensityMode===preference;button.setAttribute('aria-checked',String(active));button.classList.toggle('active',active)}}
function buttonFor(mode,label){const button=doc.createElement('button');button.type='button';button.dataset.inkdosDensityMode=mode;button.setAttribute('role','menuitemradio');button.textContent=label;button.addEventListener('click',()=>set(mode));return button}
function installControl(host,{home=false}={}){if(!doc||!host||host.querySelector('[data-inkdos-density-control]'))return null;const wrap=doc.createElement('div');wrap.dataset.inkdosDensityControl='';wrap.className='inkdos-density-control'+(home?' home-density-control':'');if(home){const divider=doc.createElement('div');divider.className='inkdos-density-divider';divider.setAttribute('role','separator');const label=doc.createElement('div');label.className='inkdos-density-label';label.textContent='Interface';host.append(divider,label,wrap)}else{const label=doc.createElement('div');label.className='drawer-section-label inkdos-density-label';label.textContent='Interface';host.append(label,wrap)}wrap.append(buttonFor('auto','Auto'),buttonFor('desktop','Desktop'),buttonFor('mobile','Mobile'));syncControls();return wrap}
function autoInstall(){if(!doc)return;const home=doc.getElementById('appearanceMenu');if(home){installControl(home,{home:true});return}const drawer=doc.getElementById('generalMenu')||doc.querySelector('.drawer');if(drawer)installControl(drawer)}
if(doc?.documentElement)apply(preference);
if(doc){if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',autoInstall,{once:true});else autoInstall()}
if(typeof root.addEventListener==='function')root.addEventListener('storage',event=>{if(event.key!==STORAGE_KEY)return;preference=normalize(event.newValue);apply(preference);announce()});
root.InkDOSUiDensity=Object.freeze({STORAGE_KEY,THRESHOLD,POINTER_QUERY,resolve,apply,set,installControl,get preference(){return preference},get effective(){return effective}});
})(globalThis);

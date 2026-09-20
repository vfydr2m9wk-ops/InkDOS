(function(root){'use strict';
const doc=typeof document!=='undefined'?document:null,LANGUAGE_KEY='inkdos2:language';
function option(language,api){const button=doc.createElement('button');button.type='button';button.setAttribute('role','menuitemradio');button.dataset.homeLanguage=language.code;button.textContent=language.label;button.addEventListener('click',async()=>{await api.setLanguage(language.code,{storageKey:LANGUAGE_KEY});sync(api)});return button}
function sync(api){for(const item of doc.querySelectorAll('[data-home-language]'))item.setAttribute('aria-checked',String(item.dataset.homeLanguage===api.currentLanguage))}
async function install(){if(!doc)return false;const menu=doc.getElementById('appearanceMenu'),api=root.InkDOSLocalization;if(!menu||!api)return false;await api.install({storageKey:LANGUAGE_KEY});if(!menu.querySelector('[data-home-language-section]')){const divider=doc.createElement('div');divider.className='inkdos-density-divider';divider.setAttribute('role','separator');const label=doc.createElement('div');label.className='inkdos-density-label';label.dataset.homeLanguageSection='';label.textContent='Language';menu.append(divider,label);for(const language of api.languages)menu.appendChild(option(language,api))}sync(api);api.apply();return true}
function boot(){install().catch(()=>{})}
if(doc){if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',boot,{once:true});else boot()}
root.InkDOSHomeSettings=Object.freeze({install,LANGUAGE_KEY});
})(globalThis);

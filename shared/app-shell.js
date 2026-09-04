(function (global) {
'use strict';
const doc=global.document;
if(!doc)return;
const THEMES=new Set(['system','light','dark']),THEME_KEY='inkdos.theme';
let activeSurface=null,lastTrigger=null;
const boundTriggers=new WeakSet();
function modules(){return global.InkDOSModules||null;
}
function rootPrefix(){return /\/apps\/[^/]+\//.test(String(global.location&&global.location.pathname||''))?'../../':'./';
}
function asset(path){return rootPrefix()+String(path||'').replace(/^\.\//,'');
}
function currentAppId(){return String(doc.body&&doc.body.dataset&&doc.body.dataset.inkdosApp||'home');
}
function storedTheme(){try{return global.localStorage&&global.localStorage.getItem(THEME_KEY)||'system';
}catch(error){return'system';
}}
function systemDark(){return Boolean(global.matchMedia&&global.matchMedia('(prefers-color-scheme: dark)').matches);
}
function applyTheme(value,persist=true){const preference=THEMES.has(value)?value:'system',resolved=preference==='system'?(systemDark()?'dark':'light'):preference;
doc.documentElement.dataset.theme=preference;
doc.documentElement.dataset.resolvedTheme=resolved;
doc.documentElement.style.colorScheme=preference==='system'?'light dark':preference;
if(persist){try{if(global.localStorage)global.localStorage.setItem(THEME_KEY,preference);
}catch(error){console.debug('InkDOS theme preference is unavailable.',error);
}}doc.querySelectorAll('[data-global-theme-option]').forEach(control=>{control.checked=control.value===preference;
});
return preference;
}
function bindSystemTheme(){if(!global.matchMedia)return;
const media=global.matchMedia('(prefers-color-scheme: dark)'),update=()=>{if(storedTheme()==='system')applyTheme('system',false);
};
if(typeof media.addEventListener==='function')media.addEventListener('change',update);
else if(typeof media.addListener==='function')media.addListener(update);
}
function surfaceHeader(titleText,closeLabel){const header=doc.createElement('header'),title=doc.createElement('strong'),close=doc.createElement('button');
title.textContent=titleText;
close.type='button';
close.className='inkdos-global-close';
close.dataset.closeGlobalSurface='';
close.setAttribute('aria-label',closeLabel);
close.textContent='×';
header.append(title,close);
return header;
}
function launcherIcon(module){const wrap=doc.createElement('span');
wrap.className='inkdos-app-launcher-icon';
wrap.style.setProperty('--app-accent',module.accent);
const image=doc.createElement('img');
image.src=asset(module.icon);
image.alt='';
image.setAttribute('aria-hidden','true');
wrap.appendChild(image);
return wrap;
}
function makeLauncher(){const surface=doc.createElement('section');
surface.className='inkdos-global-surface inkdos-app-launcher';
surface.hidden=true;
surface.dataset.appLauncher='';
surface.setAttribute('role','dialog');
surface.setAttribute('aria-modal','true');
surface.setAttribute('aria-label','Apps');
surface.appendChild(surfaceHeader('Apps','Close apps'));
const grid=doc.createElement('div');
grid.className='inkdos-app-launcher-grid';
grid.dataset.appLauncherGrid='';
surface.appendChild(grid);
const runtime=modules();
if(runtime)runtime.listEnabled().forEach(module=>{const link=doc.createElement('a');
link.className='inkdos-app-launcher-item';
link.href=asset(module.route);
link.dataset.appId=module.id;
link.style.setProperty('--app-accent',module.accent);
if(module.id===currentAppId())link.setAttribute('aria-current','page');
link.appendChild(launcherIcon(module));
const label=doc.createElement('span');
label.textContent=module.label;
link.appendChild(label);
link.addEventListener('keydown',event=>{if(event.key===' '){event.preventDefault();
link.click();
}});
if(module.id===currentAppId())link.addEventListener('click',event=>{event.preventDefault();
closeSurface();
});
grid.appendChild(link);
});
return surface;
}
function makeSettings(){const surface=doc.createElement('section');
surface.className='inkdos-global-surface inkdos-settings-sheet';
surface.hidden=true;
surface.dataset.settingsSheet='';
surface.setAttribute('role','dialog');
surface.setAttribute('aria-modal','true');
surface.setAttribute('aria-label','Settings');
surface.appendChild(surfaceHeader('Settings','Close settings'));
const group=doc.createElement('fieldset');
group.className='inkdos-theme-options';
const legend=doc.createElement('legend');
legend.textContent='Theme';
group.appendChild(legend);
[['system','System'],['light','Light'],['dark','Dark']].forEach(([value,text])=>{const label=doc.createElement('label'),input=doc.createElement('input'),copy=doc.createElement('span');
input.type='radio';
input.name='inkdos-global-theme';
input.value=value;
input.dataset.globalThemeOption='';
input.checked=storedTheme()===value;
input.addEventListener('change',()=>{if(input.checked)applyTheme(value);
});
copy.textContent=text;
label.append(input,copy);
group.appendChild(label);
});
surface.appendChild(group);
const about=doc.createElement('div');
about.className='inkdos-settings-about';
about.innerHTML='<strong>InkDOS</strong><span>Ink Desk Offline Suite</span><small>Local. Offline. Private.</small>';
surface.appendChild(about);
const links=doc.createElement('nav');
links.setAttribute('aria-label','Project links');
const projectLinks=[
['Source','https://github.com/vfydr2m9wk-ops/InkDOS'],
['Status',asset('docs/PROJECT_STATUS.md')],
['Limitations',asset('docs/KNOWN_LIMITATIONS.md')],
['Contribute',asset('CONTRIBUTING.md')]
];
projectLinks.forEach(([text,href])=>{const link=doc.createElement('a');
link.href=href;
link.textContent=text;
if(/^https:/.test(href)){link.target='_blank';
link.rel='noopener';
}links.appendChild(link);
});
surface.appendChild(links);
return surface;
}
function makeBackdrop(){const button=doc.createElement('button');
button.type='button';
button.className='inkdos-global-backdrop';
button.hidden=true;
button.setAttribute('aria-label','Close overlay');
button.addEventListener('click',()=>closeSurface());
return button;
}
function focusables(surface){return Array.from(surface.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter(node=>!node.hidden);
}
function openSurface(surface,trigger){if(activeSurface)closeSurface(false);
activeSurface=surface;
lastTrigger=trigger||doc.activeElement;
surface.hidden=false;
backdrop.hidden=false;
if(trigger)trigger.setAttribute('aria-expanded','true');
const items=focusables(surface);
if(items[0])items[0].focus();
}
function closeSurface(restore=true){if(!activeSurface)return;
const trigger=lastTrigger;
doc.querySelectorAll('[data-app-launcher-trigger],[data-settings-trigger]').forEach(node=>node.setAttribute('aria-expanded','false'));
activeSurface.hidden=true;
backdrop.hidden=true;
activeSurface=null;
lastTrigger=null;
if(restore&&trigger&&typeof trigger.focus==='function')trigger.focus();
}
function onKeydown(event){if(!activeSurface)return;
if(event.key==='Escape'){event.preventDefault();
closeSurface();
return;
}if(event.key!=='Tab')return;
const items=focusables(activeSurface);
if(!items.length)return;
const first=items[0],last=items[items.length-1];
if(event.shiftKey&&doc.activeElement===first){event.preventDefault();
last.focus();
}else if(!event.shiftKey&&doc.activeElement===last){event.preventDefault();
first.focus();
}}
function gridIcon(){return'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/></svg>';
}
function settingsIcon(){return'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.5"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/></svg>';
}
function makeTrigger(kind){const button=doc.createElement('button');
button.type='button';
button.className='icon-btn inkdos-global-trigger';
button.setAttribute('aria-haspopup','dialog');
button.setAttribute('aria-expanded','false');
if(kind==='launcher'){button.dataset.appLauncherTrigger='';
button.setAttribute('aria-label','Open apps');
button.innerHTML=gridIcon();
}else{button.dataset.settingsTrigger='';
button.setAttribute('aria-label','Open settings');
button.innerHTML=settingsIcon();
}return button;
}
function bindTrigger(node,surface){if(!node||boundTriggers.has(node))return;
boundTriggers.add(node);
node.addEventListener('click',()=>openSurface(surface,node));
}
function ensureTriggers(){const launchers=Array.from(doc.querySelectorAll('[data-app-launcher-trigger]')),settings=Array.from(doc.querySelectorAll('[data-settings-trigger]'));
if(!launchers.length||!settings.length){const bar=doc.querySelector('header[data-inkdos-shell-region="titlebar"],header.topbar,header.titlebar,.txt-titlebar,.epub-titlebar');
if(bar){let host=bar.querySelector('.inkdos-global-actions');
if(!host){host=doc.createElement('div');
host.className='inkdos-global-actions';
const left=bar.querySelector('.left,.left-tools,.title-actions,.txt-title-actions,.titlebar-left')||bar;
left.appendChild(host);
}if(!launchers.length)host.appendChild(makeTrigger('launcher'));
if(!settings.length)host.appendChild(makeTrigger('settings'));
}}doc.querySelectorAll('[data-app-launcher-trigger]').forEach(node=>bindTrigger(node,appLauncher));
doc.querySelectorAll('[data-settings-trigger]').forEach(node=>bindTrigger(node,settingsSheet));
}
function configureAppInput(){const runtime=modules(),appId=currentAppId();
if(!runtime||appId==='home')return;
const module=runtime.get(appId);
if(!module||!module.openAction)return;
const input=doc.getElementById(module.openAction);
if(input&&input.type==='file')input.accept=runtime.buildAcceptFor(module);
}
function init(){applyTheme(storedTheme(),false);
bindSystemTheme();
doc.body.append(backdrop,appLauncher,settingsSheet);
ensureTriggers();
configureAppInput();
doc.querySelectorAll('[data-close-global-surface]').forEach(node=>node.addEventListener('click',()=>closeSurface()));
doc.addEventListener('keydown',onKeydown);
}
const backdrop=makeBackdrop(),appLauncher=makeLauncher(),settingsSheet=makeSettings();
global.InkDOSAppShell=Object.freeze({
version:'1',applyTheme,storedTheme,
openLauncher:trigger=>openSurface(appLauncher,trigger),
openSettings:trigger=>openSurface(settingsSheet,trigger),
close:closeSurface,currentAppId,
refreshTriggers:ensureTriggers
});
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});
else init();
})(typeof window!=='undefined'?window:globalThis);

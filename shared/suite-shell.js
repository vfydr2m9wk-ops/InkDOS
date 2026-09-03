(function(global){
'use strict';
const product=global.InkDOSProduct||{name:'InkDOS',longName:'Ink Desk Offline Suite',tagline:'Local. Offline. Private.'};
const recentKey='inkdos.recent.v1';
const themes=new Set(['system','light','dark']);
function readRecent(){try{return JSON.parse(global.localStorage.getItem(recentKey)||'[]')}catch(error){return []}}
  function writeRecent(items){try{global.localStorage.setItem(recentKey,JSON.stringify(items.slice(0,12)))}catch(error){console.debug('InkDOS recent metadata is unavailable.',error)}}
function addRecent(file,module){if(!file||!file.name)return;const items=readRecent().filter(item=>item.name!==file.name);items.unshift({name:file.name,size:Number(file.size||0),module,module,openedAt:Date.now()});writeRecent(items)}
function route(file){return global.InkDeskFileRouter.routeForFile(file)}
function open(file){const resolved=route(file);addRecent(file,resolved.extension);return global.InkDeskFileRouter.openFromHub(file)}
  function applyTheme(value){
    const theme=themes.has(value)?value:'system';
    document.documentElement.dataset.theme=theme;
    document.documentElement.style.colorScheme=theme==='system'?'light dark':theme;
    try{global.localStorage.setItem('inkdos.theme',theme)}catch(error){console.debug('InkDOS theme preference is unavailable.',error)}
    return theme;
  }
function storedTheme(){try{return global.localStorage.getItem('inkdos.theme')||'system'}catch(error){return 'system'}}
function moduleOptions(){return global.InkDeskModules?global.InkDeskModules.listEnabled().filter(module=>module.capabilities.includes('new')):[]}
function makeDialog(){
  const dialog=document.createElement('dialog');dialog.className='suite-dialog';dialog.setAttribute('aria-labelledby','createTitle');
  dialog.innerHTML='<form method="dialog" class="suite-dialog-card">'
    +'<button class="suite-dialog-close" value="cancel" aria-label="Close">×</button>'
    +'<h2 id="createTitle">Create</h2><p>Select a workspace</p>'
    +'<div class="create-options"></div></form>';
  const options=dialog.querySelector('.create-options');
  moduleOptions().forEach(module=>{
    const button=document.createElement('button');
    button.type='button';button.className='create-option';
    button.dataset.moduleId=module.id;button.textContent=module.name;
    button.addEventListener('click',()=>global.location.assign('./'+module.entryPoint));
    options.appendChild(button);
  });
  return dialog;
}
function init(){
  const root=document.documentElement;document.title=product.name+' — '+product.longName;
  document.querySelectorAll('[data-product-name]').forEach(node=>node.textContent=product.name);
  document.querySelectorAll('[data-product-long-name]').forEach(node=>node.textContent=product.longName);
  document.querySelectorAll('[data-release-badge],[data-release-version]').forEach(node=>node.textContent='v'+product.version);
  const input=document.querySelector('#suiteOpenInput');const openButton=document.querySelector('[data-suite-action="open"]');const createButton=document.querySelector('[data-suite-action="create"]');
  if(input){input.accept=global.InkDeskModules?global.InkDeskModules.buildAccept():'';input.addEventListener('change',()=>{const file=input.files&&input.files[0];if(!file)return;try{open(file)}catch(error){global.alert(error.message)}})}
  if(openButton&&input)openButton.addEventListener('click',()=>input.click());
  if(createButton){const dialog=makeDialog();document.body.appendChild(dialog);createButton.addEventListener('click',()=>dialog.showModal())}
  const theme=applyTheme(storedTheme());document.querySelectorAll('[data-theme-choice]').forEach(control=>{control.value=theme;control.addEventListener('change',()=>applyTheme(control.value))});
  const menu=document.querySelector('#suiteSidebar');const menuButton=document.querySelector('[data-suite-action="menu"]');const closeButton=document.querySelector('[data-suite-action="close-menu"]');
  if(menu&&menuButton){
    const backdrop=document.createElement('button');backdrop.type='button';backdrop.className='suite-backdrop';backdrop.setAttribute('aria-label','Close suite navigation');backdrop.hidden=true;document.body.appendChild(backdrop);
    let previousFocus=null;
    const close=()=>{menu.classList.remove('is-open');menu.hidden=true;backdrop.hidden=true;menuButton.setAttribute('aria-expanded','false');if(previousFocus)previousFocus.focus()};
    menuButton.addEventListener('click',()=>{
      previousFocus=document.activeElement;
      menu.hidden=false;menu.classList.add('is-open');
      backdrop.hidden=false;
      menuButton.setAttribute('aria-expanded','true');
      if(closeButton)closeButton.focus();
    });
    if(closeButton)closeButton.addEventListener('click',close);
    backdrop.addEventListener('click',close);
    menu.addEventListener('click',event=>{if(event.target===menu)close()});
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!menu.hidden)close()});
  }
  const clear=document.querySelector('[data-suite-action="clear-recent"]');if(clear)clear.addEventListener('click',()=>{writeRecent([]);renderRecent()});renderRecent();
}
  function renderRecent(){
    const target=document.querySelector('[data-recent-list]');if(!target)return;
    target.replaceChildren();
    const items=readRecent().slice(0,5);
    if(!items.length){const empty=document.createElement('li');empty.className='recent-empty';empty.textContent='No recent files yet';target.appendChild(empty)}
    items.forEach(item=>{
      const node=document.createElement('li');node.textContent=item.name;
      target.appendChild(node);
    });
  }
global.InkDOSSuite=Object.freeze({product,open,route,readRecent,clearRecent:()=>writeRecent([]),applyTheme,moduleOptions});
if(typeof document!=='undefined'){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init()}
})(typeof window!=='undefined'?window:globalThis);

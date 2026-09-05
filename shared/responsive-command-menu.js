(function (global) {
'use strict';
const doc=global.document;
if(!doc)return;
const appId=String(doc.body&&doc.body.dataset&&doc.body.dataset.inkdosApp||'home');
if(appId==='home')return;

const selectors=Object.freeze({
  save:'#saveBtn,#saveButton,#savePdfBtn,#downloadBtn,#exportBtn,[data-action="save"],[data-command="save"],button[aria-label*="save" i]',
  new:'#newBtn,#newSmall,#newEmptyBtn,#newStartBtn,[data-app-home-action="create"],[data-action="new"],[data-command="new"],button[aria-label^="new" i]',
  undo:'#undoBtn,[data-action="undo"],[data-command="undo"],button[aria-label="undo" i]',
  redo:'#redoBtn,[data-action="redo"],[data-command="redo"],button[aria-label="redo" i]',
  share:'#shareBtn,[data-action="share"],[data-command="share"],button[aria-label*="share" i]'
});
let menu=null,backdrop=null,trigger=null;
function rootPrefix(){return /\/apps\/[^/]+\//.test(String(global.location&&global.location.pathname||''))?'../../':'./';}
function findControl(name){const selector=selectors[name];return selector?doc.querySelector(selector):null;}
function closeMenu(){
  if(!menu)return;
  menu.hidden=true;
  if(backdrop)backdrop.hidden=true;
  if(trigger)trigger.setAttribute('aria-expanded','false');
}
function syncDisabled(){
  if(!menu)return;
  for(const name of ['save','new','undo','redo']){
    const item=menu.querySelector('[data-inkdos-command="'+name+'"]');
    const target=findControl(name);
    if(item)item.disabled=!target||Boolean(target.disabled);
  }
}
function invokeControl(name){
  const target=findControl(name);
  if(!target||target.disabled)return false;
  if(typeof target.click==='function'){target.click();return true;}
  return false;
}
async function shareCurrent(){
  if(invokeControl('share'))return;
  const payload={title:doc.title||'InkDOS',text:'InkDOS',url:String(global.location&&global.location.href||'')};
  try{
    if(global.navigator&&typeof global.navigator.share==='function'){await global.navigator.share(payload);return;}
    if(global.navigator&&global.navigator.clipboard&&typeof global.navigator.clipboard.writeText==='function'){
      await global.navigator.clipboard.writeText(payload.url);
      global.dispatchEvent(new CustomEvent('inkdos:share-link-copied',{detail:{url:payload.url}}));
    }
  }catch(error){
    if(error&&error.name!=='AbortError')console.debug('InkDOS share action was unavailable.',error);
  }
}
function runCommand(name){
  closeMenu();
  if(name==='home'){global.location.href=rootPrefix()+'index.html';return;}
  if(name==='share'){void shareCurrent();return;}
  invokeControl(name);
}
function makeItem(name,label){
  const button=doc.createElement('button');
  button.type='button';
  button.className='inkdos-command-menu-item';
  button.dataset.inkdosCommand=name;
  button.textContent=label;
  button.addEventListener('click',()=>runCommand(name));
  return button;
}
function buildMenu(){
  const surface=doc.createElement('section');
  surface.className='inkdos-command-menu';
  surface.hidden=true;
  surface.setAttribute('role','dialog');
  surface.setAttribute('aria-modal','true');
  surface.setAttribute('aria-label','Document menu');
  const heading=doc.createElement('div');
  heading.className='inkdos-command-menu-heading';
  const title=doc.createElement('strong');
  title.textContent='Document';
  const close=doc.createElement('button');
  close.type='button';
  close.className='inkdos-command-menu-close';
  close.setAttribute('aria-label','Close document menu');
  close.textContent='×';
  close.addEventListener('click',closeMenu);
  heading.append(title,close);
  surface.append(heading);
  [
    ['home','Home'],
    ['save','Save'],
    ['new','New document'],
    ['share','Share'],
    ['undo','Undo'],
    ['redo','Redo']
  ].forEach(([name,label])=>surface.appendChild(makeItem(name,label)));
  return surface;
}
function buildBackdrop(){
  const node=doc.createElement('button');
  node.type='button';
  node.className='inkdos-command-backdrop';
  node.hidden=true;
  node.setAttribute('aria-label','Close document menu');
  node.addEventListener('click',closeMenu);
  return node;
}
function titlebar(){
  return doc.querySelector('header[data-inkdos-shell-region="titlebar"],header.topbar,header.titlebar,.txt-titlebar,.epub-titlebar');
}
function init(){
  const bar=titlebar();
  if(!bar)return;
  doc.body.classList.add('inkdos-responsive-workspace');
  bar.classList.add('inkdos-compact-titlebar');
  trigger=doc.createElement('button');
  trigger.type='button';
  trigger.className='inkdos-command-trigger';
  trigger.dataset.inkdosCommandTrigger='';
  trigger.setAttribute('aria-haspopup','dialog');
  trigger.setAttribute('aria-expanded','false');
  trigger.setAttribute('aria-label','Open document menu');
  for(let index=0;index<3;index+=1){
    const line=doc.createElement('span');
    line.setAttribute('aria-hidden','true');
    trigger.appendChild(line);
  }
  menu=buildMenu();
  backdrop=buildBackdrop();
  trigger.addEventListener('click',()=>{
    syncDisabled();
    menu.hidden=false;
    backdrop.hidden=false;
    trigger.setAttribute('aria-expanded','true');
    const first=menu.querySelector('button:not([disabled])');
    if(first)first.focus();
  });
  bar.appendChild(trigger);
  doc.body.append(backdrop,menu);
  doc.addEventListener('keydown',event=>{if(event.key==='Escape'&&!menu.hidden){event.preventDefault();closeMenu();}});
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});
else init();
})(typeof window!=='undefined'?window:globalThis);

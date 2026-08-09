(function(global){
'use strict';

const ID_RE=/^[a-z][a-z0-9-]*$/;
const HEX_RE=/^#[0-9a-f]{6}$/i;
const EXT_RE=/^[a-z0-9]+$/;

function cloneModule(raw){
  if(!raw||typeof raw!=='object')throw new Error('Module entry is not an object.');
  const module={
    schemaVersion:Number(raw.schemaVersion),
    id:String(raw.id||''),
    name:String(raw.name||''),
    description:String(raw.description||''),
    version:String(raw.version||''),
    enabled:raw.enabled===true,
    optional:raw.optional===true,
    order:Number(raw.order),
    entryPoint:String(raw.entryPoint||''),
    icon:String(raw.icon||''),
    badge:String(raw.badge||''),
    themeClass:String(raw.themeClass||''),
    accent:String(raw.accent||''),
    extensions:Array.isArray(raw.extensions)?raw.extensions.map(value=>String(value).toLowerCase()):[],
    mimeTypes:Array.isArray(raw.mimeTypes)?raw.mimeTypes.map(String):[],
    capabilities:Array.isArray(raw.capabilities)?raw.capabilities.map(String):[]
  };
  if(module.schemaVersion!==1)throw new Error('Unsupported module schema.');
  if(!ID_RE.test(module.id)||!ID_RE.test(module.themeClass))throw new Error('Invalid module identifier.');
  if(!module.name||!module.description||!module.entryPoint||!module.icon||!module.badge)throw new Error('Incomplete module metadata.');
  if(!Number.isInteger(module.order)||module.order<0)throw new Error('Invalid module order.');
  if(!HEX_RE.test(module.accent))throw new Error('Invalid module accent.');
  if(!module.extensions.length||module.extensions.some(value=>!EXT_RE.test(value)))throw new Error('Invalid module extensions.');
  return Object.freeze(module);
}

function createRuntime(source){
  const errors=[];
  const modules=[];
  const ids=new Set();
  const extensions=new Map();
  const rawModules=source&&Array.isArray(source.modules)?source.modules:[];
  rawModules.forEach((raw,index)=>{
    try{
      const module=cloneModule(raw);
      if(ids.has(module.id))throw new Error('Duplicate module ID.');
      module.extensions.forEach(extension=>{
        if(extensions.has(extension))throw new Error('Duplicate module extension.');
      });
      ids.add(module.id);
      module.extensions.forEach(extension=>extensions.set(extension,module));
      modules.push(module);
    }catch(error){
      errors.push({index,message:error&&error.message?error.message:'Invalid module.'});
    }
  });
  modules.sort((a,b)=>a.order-b.order||a.name.localeCompare(b.name)||a.id.localeCompare(b.id));
  const byId=new Map(modules.map(module=>[module.id,module]));
  const missing=source&&Array.isArray(source.missingModules)?source.missingModules.slice():[];

  function list(){return modules.slice()}
  function listEnabled(){return modules.filter(module=>module.enabled)}
  function get(id){return byId.get(String(id||''))||null}
  function isEnabled(id){const module=get(id);return Boolean(module&&module.enabled)}
  function resolveExtension(extension){
    const normalized=String(extension||'').trim().toLowerCase().replace(/^\./,'');
    const module=extensions.get(normalized)||null;
    return module&&module.enabled?module:null;
  }
  function extensionOf(name){
    const match=String(name||'').trim().toLowerCase().match(/\.([a-z0-9]+)$/);
    return match?match[1]:'';
  }
  function resolveFile(file){
    const extension=extensionOf(file&&file.name);
    const registered=extensions.get(extension)||null;
    if(!registered)throw new Error('This file type is not registered in InkDesk.');
    if(!registered.enabled)throw new Error(registered.name+' is currently disabled.');
    return registered;
  }
  function buildAccept(){
    const values=[];
    listEnabled().forEach(module=>{
      module.extensions.forEach(extension=>values.push('.'+extension));
      module.mimeTypes.forEach(type=>{if(type&&!values.includes(type))values.push(type)});
    });
    return values.join(',');
  }
  return Object.freeze({
    schemaVersion:1,
    registryVersion:String(source&&source.registryVersion||''),
    list,
    listEnabled,
    get,
    isEnabled,
    resolveExtension,
    resolveFile,
    buildAccept,
    errors:Object.freeze(errors),
    missingModules:Object.freeze(missing)
  });
}

function appendTextElement(parent,tag,className,text){
  const element=document.createElement(tag);
  if(className)element.className=className;
  element.textContent=text;
  parent.appendChild(element);
  return element;
}

function createCard(module){
  const link=document.createElement('a');
  link.className='workspace-card app-card '+module.themeClass;
  link.href='./'+module.entryPoint.replace(/^\.?\//,'');
  link.dataset.moduleId=module.id;
  link.style.setProperty('--accent',module.accent);
  link.style.setProperty('--tint',module.accent);
  link.setAttribute('aria-label','Open '+module.name);

  const iconWrap=document.createElement('span');
  iconWrap.className='app-icon has-image';
  const iconImage=document.createElement('img');
  iconImage.src='./'+module.icon.replace(/^\.?\//,'');
  iconImage.alt='';
  iconImage.setAttribute('aria-hidden','true');
  iconImage.loading='eager';
  iconImage.decoding='async';
  iconWrap.appendChild(iconImage);
  link.appendChild(iconWrap);
  const arrow=appendTextElement(link,'span','open-arrow','›');
  arrow.setAttribute('aria-hidden','true');
  const copy=document.createElement('span');
  copy.className='workspace-copy card-copy';
  appendTextElement(copy,'h2','',module.name);
  appendTextElement(copy,'p','',module.description);
  link.appendChild(copy);
  return link;
}

function renderLauncher(runtime,root){
  const scope=root||document;
  const grid=scope.querySelector('[data-module-grid]');
  if(!grid)return false;
  const enabled=runtime.listEnabled();
  if(!enabled.length)return false;
  const fragment=document.createDocumentFragment();
  enabled.forEach(module=>fragment.appendChild(createCard(module)));
  grid.replaceChildren(fragment);
  grid.dataset.moduleRegistry='ready';
  return true;
}

function reportStatus(runtime,root){
  const scope=root||document;
  const status=scope.getElementById?scope.getElementById('moduleRegistryStatus'):document.getElementById('moduleRegistryStatus');
  if(!status)return;
  const issueCount=runtime.errors.length+runtime.missingModules.length;
  if(!issueCount){
    status.hidden=true;
    status.textContent='';
    return;
  }
  status.hidden=false;
  status.textContent='Some optional InkDesk modules are unavailable. The remaining workspaces can still be opened.';
}

const runtime=createRuntime(global.InkDeskModuleRegistry||{schemaVersion:1,modules:[]});
global.InkDeskModules=runtime;
global.InkDeskCreateModuleRuntime=createRuntime;

function initialize(){
  try{
    renderLauncher(runtime,document);
    reportStatus(runtime,document);
  }catch(error){
    console.error('InkDesk module launcher initialization failed.',error);
  }
}
if(typeof document!=='undefined'){
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
  else initialize();
}
})(typeof window!=='undefined'?window:globalThis);

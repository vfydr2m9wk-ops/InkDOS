(function (global) {
'use strict';
const ID_RE=/^[a-z][a-z0-9-]*$/;
const HEX_RE=/^#[0-9a-f]{6}$/i;
const EXT_RE=/^[a-z0-9]+$/;
function cloneModule(raw){
if(!raw||typeof raw!=='object')throw new Error('Module entry is not an object.');
const capabilities=Array.isArray(raw.capabilities)?raw.capabilities.map(String):[];
const module={
schemaVersion:Number(raw.schemaVersion),id:String(raw.id||''),name:String(raw.name||''),
label:String(raw.label||raw.name||''),shortLabel:String(raw.shortLabel||raw.label||raw.name||''),
description:String(raw.description||''),version:String(raw.version||''),enabled:raw.enabled===true,
optional:raw.optional===true,order:Number(raw.order),entryPoint:String(raw.entryPoint||''),
route:String(raw.route||raw.entryPoint||''),icon:String(raw.icon||''),badge:String(raw.badge||''),
themeClass:String(raw.themeClass||''),accent:String(raw.accent||''),
extensions:Array.isArray(raw.extensions)?raw.extensions.map(v=>String(v).toLowerCase()):[],
mimeTypes:Array.isArray(raw.mimeTypes)?raw.mimeTypes.map(String):[],capabilities,
createAction:raw.createAction==null?null:String(raw.createAction),
openAction:raw.openAction==null?null:String(raw.openAction),
createLabel:raw.createLabel==null?null:String(raw.createLabel),
openLabel:raw.openLabel==null?'Open file':String(raw.openLabel),
};
if(module.schemaVersion!==1)throw new Error('Unsupported module schema.');
if(!ID_RE.test(module.id)||!ID_RE.test(module.themeClass))throw new Error('Invalid module identifier.');
if(!module.name||!module.label||!module.shortLabel||!module.description||!module.entryPoint||!module.route||!module.icon||!module.badge)throw new Error('Incomplete module metadata.');
if(module.route!==module.entryPoint)throw new Error('Module route and entry point diverge.');
if(!Number.isInteger(module.order)||module.order<0)throw new Error('Invalid module order.');
if(!HEX_RE.test(module.accent))throw new Error('Invalid module accent.');
if(!module.extensions.length||module.extensions.some(value=>!EXT_RE.test(value)))throw new Error('Invalid module extensions.');
module.capabilityFlags=Object.freeze({
create:capabilities.includes('new')&&Boolean(module.createAction),
open:capabilities.includes('open')&&Boolean(module.openAction),
edit:capabilities.some(value=>value==='edit'||value.startsWith('edit-')),
save:capabilities.some(value=>value==='save'||value.includes('export')),
});
return Object.freeze(module);
}
function createRuntime(source){
const errors=[],modules=[],ids=new Set(),extensions=new Map();
const rawModules=source&&Array.isArray(source.modules)?source.modules:[];
rawModules.forEach((raw,index)=>{try{
const module=cloneModule(raw);
if(ids.has(module.id))throw new Error('Duplicate module ID.');
module.extensions.forEach(extension=>{if(extensions.has(extension))throw new Error('Duplicate module extension.');
});
ids.add(module.id);
module.extensions.forEach(extension=>extensions.set(extension,module));
modules.push(module);
}catch(error){errors.push({index,message:error&&error.message?error.message:'Invalid module.'});
}});
modules.sort((a,b)=>a.order-b.order||a.label.localeCompare(b.label)||a.id.localeCompare(b.id));
const byId=new Map(modules.map(module=>[module.id,module]));
const missing=source&&Array.isArray(source.missingModules)?source.missingModules.slice():[];
const list=()=>modules.slice();
const listEnabled=()=>modules.filter(module=>module.enabled);
const get=id=>byId.get(String(id||''))||null;
function extensionOf(name){const match=String(name||'').trim().toLowerCase().match(/\.([a-z0-9]+)$/);
return match?match[1]:'';
}
function resolveExtension(extension){const normalized=String(extension||'').trim().toLowerCase().replace(/^\./,'');
const module=extensions.get(normalized)||null;
return module&&module.enabled?module:null;
}
function resolveFile(file){const extension=extensionOf(file&&file.name),registered=extensions.get(extension)||null;
if(!registered)throw new Error('This file type is not registered in InkDOS.');
if(!registered.enabled)throw new Error(registered.label+' is currently disabled.');
return registered;
}
function buildAcceptFor(moduleOrId){const module=typeof moduleOrId==='string'?get(moduleOrId):moduleOrId;
if(!module||!module.enabled)return'';
const values=module.extensions.map(extension=>'.'+extension);
module.mimeTypes.forEach(type=>{if(type&&!values.includes(type))values.push(type);
});
return values.join(',');
}
function buildAccept(moduleId){if(moduleId)return buildAcceptFor(moduleId);
const values=[];
listEnabled().forEach(module=>buildAcceptFor(module).split(',').filter(Boolean).forEach(value=>{if(!values.includes(value))values.push(value);
}));
return values.join(',');
}
function routeFor(moduleOrId){const module=typeof moduleOrId==='string'?get(moduleOrId):moduleOrId;
return module&&module.enabled?module.route:null;
}
return Object.freeze({
schemaVersion:1,
registryVersion:String(source&&source.registryVersion||''),
list,listEnabled,get,
isEnabled:id=>Boolean(get(id)&&get(id).enabled),
extensionOf,resolveExtension,resolveFile,
buildAccept,buildAcceptFor,routeFor,
errors:Object.freeze(errors),
missingModules:Object.freeze(missing)
});
}
global.InkDOSModules=createRuntime(global.InkDOSModuleRegistry||{schemaVersion:1,modules:[]});
global.InkDOSCreateModuleRuntime=createRuntime;
})(typeof window!=='undefined'?window:globalThis);

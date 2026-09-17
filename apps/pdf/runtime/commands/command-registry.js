(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
function create(){
  const commands=new Map(),bindings=new Map();
  function normalizeSpec(spec){if(typeof spec==='function')return{execute:spec};return spec&&typeof spec==='object'?spec:{}}
  function register(id,spec){id=String(id||'').trim();if(!id)throw new Error('Command ID required.');spec=normalizeSpec(spec);if(typeof spec.execute!=='function')throw new Error(`Command ${id} requires execute().`);commands.set(id,spec);sync(id);return id}
  function unregister(id){commands.delete(id);sync(id)}
  function state(id){const spec=commands.get(id);if(!spec)return Object.freeze({registered:false,enabled:false,checked:false});let enabled=true,checked=false;try{if(typeof spec.isEnabled==='function')enabled=!!spec.isEnabled();if(typeof spec.isChecked==='function')checked=!!spec.isChecked()}catch(e){console.error('PDF command state failed',id,e);enabled=false}return Object.freeze({registered:true,enabled,checked})}
  async function execute(id,...args){const spec=commands.get(id),s=state(id);if(!spec||!s.enabled)return false;try{return await spec.execute(...args)}finally{sync(id)}}
  function bindElement(el,id){if(!el)return false;id=String(id||el.dataset.command||'').trim();if(!id)return false;const previous=bindings.get(el);if(previous?.handler)el.removeEventListener('click',previous.handler);el.dataset.command=id;const handler=e=>{e.preventDefault();execute(id,e).catch(err=>console.error('PDF command failed',id,err))};el.addEventListener('click',handler);bindings.set(el,{id,handler});sync(id);return true}
  function unbindElement(el){const b=bindings.get(el);if(!b)return;el.removeEventListener('click',b.handler);bindings.delete(el)}
  function bind(root=document){for(const el of root.querySelectorAll('[data-command]'))bindElement(el,el.dataset.command)}
  function sync(id=null){for(const[el,b]of [...bindings]){if(!el.isConnected){unbindElement(el);continue}if(id&&b.id!==id)continue;const s=state(b.id);el.disabled=!s.enabled;el.classList.toggle('active',!!s.checked);el.setAttribute('aria-disabled',String(!s.enabled));if(s.checked)el.setAttribute('aria-pressed','true');else if(el.hasAttribute('aria-pressed'))el.setAttribute('aria-pressed','false')}}
  function inspect(){return Object.freeze({commands:Object.freeze([...commands.keys()].sort()),bindings:Object.freeze([...bindings.values()].map(x=>x.id).sort())})}
  return Object.freeze({register,unregister,state,execute,bind,bindElement,unbindElement,sync,inspect})
}
NS.CommandRegistry=Object.freeze({create});
})(globalThis);

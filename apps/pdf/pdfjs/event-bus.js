(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
class PdfjsEventBus{
  constructor(){this.listeners=new Map()}
  _on(name,fn,options){if(typeof fn!=='function')return;const signal=options?.signal;if(signal?.aborted)return;(this.listeners.get(name)||this.listeners.set(name,new Set()).get(name)).add(fn);signal?.addEventListener('abort',()=>this._off(name,fn),{once:true})}
  on(name,fn,options){this._on(name,fn,options)}
  _off(name,fn){this.listeners.get(name)?.delete(fn)}
  off(name,fn){this._off(name,fn)}
  dispatch(name,data={}){for(const fn of [...(this.listeners.get(name)||[])]){try{fn(data)}catch(e){console.error('PDF.js event listener failed',name,e)}}}
  clear(){this.listeners.clear()}
}
NS.PdfjsEventBus=PdfjsEventBus;})(globalThis);
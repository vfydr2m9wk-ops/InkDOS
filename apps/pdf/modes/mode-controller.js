(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
function create({editor,extensions,pageLayers,chrome}={}){let mode='view',tool='none';const listeners=new Set();
 function inspect(){return Object.freeze({mode,tool})}
 function notify(){pageLayers?.setInteractionState({mode,tool});const snapshot=inspect();for(const fn of [...listeners])try{fn(snapshot)}catch(e){console.error('PDF mode subscriber failed',e)}}
 function nativeAndExtension(nextTool){if(nextTool==='text'||nextTool==='pen'){extensions?.setTool('none');editor.setTool(nextTool)}else{editor.setTool('none');extensions?.setTool(['highlight','underline','comment'].includes(nextTool)?nextTool:'none')}}
 function setMode(next){if(next!=='annotate')extensions?.closeComment();mode=next==='annotate'?'annotate':'view';tool=mode==='annotate'?'select':'none';editor.setMode(mode);nativeAndExtension(tool);notify();chrome.status(mode==='view'?'View mode · read only':'Annotate · Select');return inspect()}
 function setTool(next){const allowed=['select','text','pen','highlight','underline','comment'];mode='annotate';tool=allowed.includes(next)?next:'select';editor.setMode('annotate');nativeAndExtension(tool);notify();const labels={select:'Annotate · Select / form fields',text:'Annotate · Text',pen:'Annotate · Pen',highlight:'Annotate · Highlight · select text',underline:'Annotate · Underline · select text',comment:'Annotate · Comment · select text or tap'};chrome.status(labels[tool]||'Annotate');return inspect()}
 function subscribe(fn){if(typeof fn!=='function')return()=>{};listeners.add(fn);fn(inspect());return()=>listeners.delete(fn)}
 function install(){editor.setMode('view');nativeAndExtension('none');notify()}
 function destroy(){listeners.clear();extensions?.closeComment();extensions?.setTool('none');editor.setMode('view')}
 return Object.freeze({install,destroy,setMode,setTool,subscribe,get mode(){return mode},get tool(){return tool},inspect})
}
NS.ModeController=Object.freeze({create});})(globalThis);

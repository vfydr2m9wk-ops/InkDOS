(function(g){'use strict';
const NS=g.InkDOS2=g.InkDOS2||{};
function create({state,editor,files,requestOpen}={}){
  if(!state||!editor||!files)throw new Error('TxtCommands requires state, editor and files');
  const registry=new Map();
  function register(id,handler,isEnabled=()=>true){if(!id||typeof handler!=='function')throw new TypeError('Invalid Plain Text command');registry.set(id,Object.freeze({handler,isEnabled}));return id}
  function has(id){return registry.has(id)}
  function isEnabled(id){const command=registry.get(id);return !!command&&command.isEnabled()!==false}
  function execute(id,...args){const command=registry.get(id);if(!command)throw new Error('TXT_COMMAND_NOT_REGISTERED: '+id);if(command.isEnabled()===false)return false;return command.handler(...args)}
  register('file.new',()=>files.newDoc());
  register('file.open.request',()=>{if(typeof requestOpen!=='function')return false;requestOpen();return true});
  register('file.open',file=>files.openFile(file));
  register('file.save',()=>files.save(),()=>state.loaded);
  register('file.share',()=>files.shareCurrent(),()=>state.loaded);
  register('history.undo',()=>editor.doUndo(),()=>state.history.canUndo);
  register('history.redo',()=>editor.doRedo(),()=>state.history.canRedo);
  register('view.wrap.toggle',()=>editor.setWrap(!state.wrap));
  register('view.font.set',value=>editor.setViewFont(value));
  register('view.font.adjust',delta=>editor.adjustFont(delta));
  register('outline.indent',delta=>editor.changeIndent(delta));
  register('outline.list',family=>editor.applyListFamily(family));
  register('selection.all',()=>editor.selectAll());
  register('clipboard.copy',()=>editor.copySelection());
  register('clipboard.paste',()=>editor.pasteClipboard());
  return Object.freeze({register,execute,isEnabled,has,list:()=>[...registry.keys()]});
}
NS.TxtCommands=Object.freeze({create});
})(globalThis);

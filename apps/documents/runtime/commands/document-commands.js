(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
const FORMAT_COMMANDS=Object.freeze(['bold','italic','underline','outdent','indent','insertUnorderedList','insertOrderedList']);
function create({fileOpen,saveController,editor,navigation}={}){
 const registry=new Map();
 let installed=false;
 function register(id,handler){if(!id||typeof handler!=='function')throw new TypeError('Invalid Documents command');registry.set(id,handler);return id}
 function execute(id,...args){const handler=registry.get(id);if(!handler)throw new Error('DOCUMENTS_COMMAND_NOT_REGISTERED: '+id);return handler(...args)}
 function install(){if(installed)return;installed=true;register('file.new',()=>fileOpen.requestNew());register('file.open',()=>fileOpen.requestOpen());register('file.save',()=>saveController.save());register('file.share',()=>saveController.share());register('edit.undo',()=>editor.restoreHistory(editor.historyIndex-1));register('edit.redo',()=>editor.restoreHistory(editor.historyIndex+1));FORMAT_COMMANDS.forEach(cmd=>register('format.'+cmd,()=>editor.cmd(cmd)));register('format.fontName',value=>editor.cmd('fontName',value));register('format.fontSize',value=>editor.cmd('fontSize',value));register('format.block',value=>editor.cmd('formatBlock',value));register('format.alignment',value=>{if(value)editor.cmd(value)});register('format.lineSpacing',value=>editor.applyLineSpacing(value));register('edit.alphaList',()=>{editor.cmd('insertOrderedList');const ol=editor.selectionBlock()?.closest('ol');if(ol)ol.style.listStyleType='upper-alpha'});register('insert.table',()=>editor.insertTable());register('insert.row',()=>editor.addRow());register('insert.column',()=>editor.addColumn());register('insert.image',file=>editor.insertImage(file));register('panel.search',()=>navigation.openPanel('searchPanel'))}
 return Object.freeze({install,register,execute,has:id=>registry.has(id),list:()=>[...registry.keys()]});
}
NS.DocumentCommands=Object.freeze({create,FORMAT_COMMANDS});
})(globalThis);

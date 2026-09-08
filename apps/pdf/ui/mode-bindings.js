(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
const COMMANDS=Object.freeze({view:'pdf.mode.view',annotate:'pdf.mode.annotate',select:'pdf.tool.select',text:'pdf.tool.text',pen:'pdf.tool.pen',highlight:'pdf.tool.highlight',underline:'pdf.tool.underline',comment:'pdf.tool.comment'});
function create({registry,modeController,root=document.documentElement}={}){const bound=[],guards=[];let unsubscribe=null;
 function register(){registry.register(COMMANDS.view,{isChecked:()=>modeController.mode==='view',execute:()=>modeController.setMode('view')});registry.register(COMMANDS.annotate,{isChecked:()=>modeController.mode==='annotate',execute:()=>modeController.setMode('annotate')});for(const tool of ['select','text','pen','highlight','underline','comment'])registry.register(COMMANDS[tool],{isChecked:()=>modeController.mode==='annotate'&&modeController.tool===tool,execute:()=>modeController.setTool(tool)})}
 function bind(){for(const el of document.querySelectorAll('[data-pdf-mode]')){const id=COMMANDS[el.dataset.pdfMode];if(!id)continue;el.dataset.command=id;registry.bindElement(el,id);bound.push(el)}for(const el of document.querySelectorAll('[data-annotate-tool]')){const tool=el.dataset.annotateTool,id=COMMANDS[tool];if(!id)continue;el.dataset.command=id;registry.bindElement(el,id);bound.push(el);if(['highlight','underline','comment'].includes(tool)){const guard=e=>e.preventDefault();el.addEventListener('pointerdown',guard);guards.push([el,guard])}}}
 function project(snapshot){root.dataset.pdfMode=snapshot.mode;root.dataset.annotateTool=snapshot.tool;registry.sync()}
 function install(){register();bind();unsubscribe=modeController.subscribe(project);registry.sync()}
 function destroy(){unsubscribe?.();for(const[el,fn]of guards)el.removeEventListener('pointerdown',fn);for(const el of bound)registry.unbindElement(el);for(const id of Object.values(COMMANDS))registry.unregister(id);delete root.dataset.pdfMode;delete root.dataset.annotateTool;bound.length=0;guards.length=0}
 return Object.freeze({install,destroy,project,inspect:()=>Object.freeze({commands:{...COMMANDS},bound:bound.map(el=>el.id||el.dataset.command)})})
}
NS.ModeBindings=Object.freeze({create,COMMANDS});})(globalThis);

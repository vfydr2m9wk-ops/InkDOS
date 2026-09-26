(function(g){'use strict';
const NS=g.InkDOS2;let t1=null,t2=null;const controls=NS.TxtControls.create(),E=controls.elements;
const frameMenu=NS.AppFrame.bindDrawer({trigger:E.menuBtn,drawer:E.menu,backdrop:E.backdrop,closeButton:E.closeMenu,beforeOpen:()=>{controls.closeListMenu();t1?.closeTools();t2?.close()}});NS.AppFrame.bindHorizontalScroller(E.toolbar);NS.AppFrame.installToolbarRail(E.toolbar);
const state=NS.TxtState.create(),editor=NS.TxtEditorController.create({elements:E,state}),files=NS.TxtFileController.create({elements:E,state,editor}),commands=NS.TxtCommands.create({state,editor,files,requestOpen:()=>{if(g.InkDOSFileLaunch?.requestPicker?.(E.fileInput))return true;E.fileInput.click();return true}});g.InkDOSFileLaunch?.setOpenHandler?.(file=>files.openFile(file));
document.addEventListener('inkdos:file-launch-error',e=>editor.setStatus('Open failed: '+(e.detail?.message||'The selected file could not be opened.'),'state-error'));
editor.setCheckpointHandler(files.checkpoint);new NS.ContentViewportAdapter(document.querySelector('.content-viewport'),editor.setMetrics);
t1=NS.TxtT1Essentials.create({elements:E,state,editor,commands,beforeOpen:()=>{controls.closeListMenu();t2?.close()}});t1.install();t2=NS.TxtT2XmlTools.create({elements:E,state,editor,commands,beforeOpen:()=>t1?.closeTools()});t2.install();controls.bind({editor,files,state,commands},frameMenu,{beforeListOpen:()=>{t1?.closeTools();t2?.close()}});NS.TxtAppDebug=Object.freeze({state,commands,...editor.debug(),...files.debug(),txtT1:t1.debug(),txtT2:t2.debug()});files.initialize();
})(globalThis);

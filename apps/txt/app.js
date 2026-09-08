(function(g){'use strict';
const NS=g.InkDOS2;let t1=null,t2=null;const controls=NS.TxtControls.create(),E=controls.elements;
const frameMenu=NS.AppFrame.bindDrawer({trigger:E.menuBtn,drawer:E.menu,backdrop:E.backdrop,closeButton:E.closeMenu,beforeOpen:()=>{controls.closeListMenu();t1?.closeTools();t2?.close()}});NS.AppFrame.bindHorizontalScroller(E.toolbar);NS.AppFrame.installToolbarRail(E.toolbar);
const state=NS.TxtState.create(),editor=NS.TxtEditorController.create({elements:E,state}),files=NS.TxtFileController.create({elements:E,state,editor}),commands=NS.TxtCommands.create({state,editor,files,requestOpen:()=>E.fileInput.click()});
editor.setCheckpointHandler(files.checkpoint);new NS.ContentViewportAdapter(document.querySelector('.content-viewport'),editor.setMetrics);
t1=NS.TxtT1Essentials.create({elements:E,state,editor,commands,beforeOpen:()=>{controls.closeListMenu();t2?.close()}});t1.install();t2=NS.TxtT2XmlTools.create({elements:E,state,editor,commands,beforeOpen:()=>t1?.closeTools()});t2.install();controls.bind({editor,files,state,commands},frameMenu,{beforeListOpen:()=>{t1?.closeTools();t2?.close()}});NS.TxtAppDebug=Object.freeze({state,commands,...editor.debug(),...files.debug(),txtT1:t1.debug(),txtT2:t2.debug()});files.initialize();
})(globalThis);

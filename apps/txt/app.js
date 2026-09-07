(function(g){'use strict';
const NS=g.InkDOS2,controls=NS.TxtControls.create(),E=controls.elements;let t1=null,t2=null;
const frameMenu=NS.AppFrame.bindDrawer({trigger:E.menuBtn,drawer:E.menu,backdrop:E.backdrop,closeButton:E.closeMenu,beforeOpen:()=>{controls.closeListMenu();t1?.closeTools();t2?.close()}});NS.AppFrame.bindHorizontalScroller(E.toolbar);
const state=NS.TxtState.create(),editor=NS.TxtEditorController.create({elements:E,state}),files=NS.TxtFileController.create({elements:E,state,editor});
editor.setCheckpointHandler(files.checkpoint);new NS.ContentViewportAdapter(document.querySelector('.content-viewport'),editor.setMetrics);
controls.bind({editor,files,state},frameMenu);t1=NS.TxtT1Essentials.create({elements:E,state,editor,files,controls});t1.install();t2=NS.TxtT2XmlTools.create({elements:E,state,editor,files});t2.install();NS.TxtAppDebug=Object.freeze({state,...editor.debug(),...files.debug(),txtT1:t1.debug(),txtT2:t2.debug()});files.initialize();
})(globalThis);

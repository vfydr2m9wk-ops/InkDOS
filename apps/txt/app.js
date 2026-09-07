(function(g){'use strict';
const NS=g.InkDOS2,controls=NS.TxtControls.create(),E=controls.elements;
const frameMenu=NS.AppFrame.bindDrawer({trigger:E.menuBtn,drawer:E.menu,backdrop:E.backdrop,closeButton:E.closeMenu,beforeOpen:controls.closeListMenu});NS.AppFrame.bindHorizontalScroller(E.toolbar);
const state=NS.TxtState.create(),editor=NS.TxtEditorController.create({elements:E,state}),files=NS.TxtFileController.create({elements:E,state,editor});
editor.setCheckpointHandler(files.checkpoint);new NS.ContentViewportAdapter(document.querySelector('.content-viewport'),editor.setMetrics);
controls.bind({editor,files,state},frameMenu);NS.TxtAppDebug=Object.freeze({state,...editor.debug(),...files.debug()});files.initialize();
})(globalThis);

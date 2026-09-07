(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{},$=id=>document.getElementById(id);
NS.PdfWorker.configure();
const session=new NS.PdfSession();
const chrome=NS.ChromeController.create({session});
const scheduler=new NS.PageScheduler(9);
let commands=null;
const editor=new NS.PdfjsEditorAdapter({container:$('contentViewport'),viewer:$('pdfStack'),session,chrome,onState:()=>commands?.syncEditor()});
const pageLayers=new NS.PdfjsPageLayers({editor});
const extensions=new NS.ReviewAnnotations({editor,session,chrome});
const layout=new NS.PageLayout({viewport:$('contentViewport'),stack:$('pdfStack'),onPageChange:n=>commands?.syncPage(),onScaleChange:s=>editor.setScale(s),onPageRendered:async info=>{await pageLayers.onPageRendered(info);extensions.onPageRendered(info)},onPageUnmount:n=>{extensions.onPageUnmount(n);pageLayers.onPageUnmount(n)}});
const adapter=new NS.ContentViewportAdapter($('contentViewport'),m=>layout.setMetrics(m));
const zoom=new NS.ZoomController(layout,()=>{});
const zoomControls=NS.ZoomControls.create({zoom,select:$('zoomSelect')});
const navigation=NS.NavigationController.create({layout,chrome});
const modeController=NS.ModeController.create({editor,extensions,pageLayers,chrome});
const fileOpen=NS.FileOpenController.create({session,fileInput:$('fileInput'),scheduler,layout,chrome,
  prepareToReplace:()=>{editor.commit();return editor.doc?.annotationStorage.serializable.hash},canReplace:()=>!save.saving,
  onBeforeReplace:async()=>{layout.clearDocument();extensions.setDocument(null);pageLayers.setDocument(null);navigation.close()},
  onDocumentOpened:async info=>{pageLayers.setDocument(info.pdfDocument);extensions.setDocument(info.pdfDocument);await navigation.setDocument(info.pdfDocument,info.pageCount);modeController.setMode('view')}
});
const save=NS.SaveController.create({session,getDocument:()=>fileOpen.pdfDocument,editor,chrome});
commands=NS.CommandController.create({session,chrome,fileOpen,save,layout,editor,navigation,modeController});
NS.Appearance.install();
fileOpen.install();
zoomControls.install();
navigation.install();
extensions.install();
modeController.install();
commands.install();
global.addEventListener('beforeunload',e=>{editor.commit();if(session.dirty){e.preventDefault();e.returnValue=''}});
adapter.measure();
chrome.title();chrome.dirty();chrome.page(1,0);
})(globalThis);

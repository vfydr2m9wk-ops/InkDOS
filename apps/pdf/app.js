(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{},$=id=>document.getElementById(id);
function loadReaderTools(){if(NS.ReaderTools)return Promise.resolve();return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='ui/reader-tools.js';s.onload=resolve;s.onerror=()=>reject(new Error('PDF_READER_TOOLS_LOAD_FAILED'));document.head.appendChild(s)})}
async function boot(){await loadReaderTools();NS.PdfWorker.configure();
const session=new NS.PdfSession();
const chrome=NS.ChromeController.create({session});
const scheduler=new NS.PageScheduler(9);
let commands=null,readerTools=null;
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
  onBeforeReplace:async()=>{readerTools?.resetDocument();layout.clearDocument();extensions.setDocument(null);pageLayers.setDocument(null);navigation.close()},
  onDocumentOpened:async info=>{pageLayers.setDocument(info.pdfDocument);extensions.setDocument(info.pdfDocument);await navigation.setDocument(info.pdfDocument,info.pageCount);modeController.setMode('view');readerTools?.resetDocument();readerTools?.syncEnabled()}
});
const save=NS.SaveController.create({session,getDocument:()=>fileOpen.pdfDocument,editor,chrome});
readerTools=NS.ReaderTools.create({session,getDocument:()=>fileOpen.pdfDocument,layout,chrome});
commands=NS.CommandController.create({session,chrome,fileOpen,save,layout,editor,navigation,modeController,readerTools});
NS.Appearance.install();
fileOpen.install();
zoomControls.install();
navigation.install();
extensions.install();
modeController.install();
readerTools.install();
commands.install();
global.addEventListener('beforeunload',e=>{editor.commit();if(session.dirty){e.preventDefault();e.returnValue=''}});
adapter.measure();
chrome.title();chrome.dirty();chrome.page(1,0);
NS.ReaderCompletionDebug=Object.freeze({readerTools,layout});
}
boot().catch(e=>{console.error(e);const status=$('statusText');if(status)status.textContent='Reader tools failed to load'});
})(globalThis);

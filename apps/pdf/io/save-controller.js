(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
function create({session,getDocument,editor,chrome}={}){
 let saving=false;
 async function save(){
  if(!session.active||saving)return null;
  const doc=getDocument?.();if(!doc)return null;
  editor.commit();if(!session.dirty){chrome.status('Nothing to save');return null}
  saving=true;document.documentElement.dataset.saveState='saving';
  // PDF.js resets its modified flag while serializing, before delivery succeeds.
  // Only an acknowledged filesystem write may clear the app's unsaved state.
  try{
   const snapshotHash=doc.annotationStorage.serializable.hash;
   const result=await NS.PdfjsSaveAdapter.createCopy({pdfDocument:doc,sourceBytes:session.sourceBytes,fileName:session.fileName,onProgress:phase=>{document.documentElement.dataset.saveState=phase;chrome.status(phase==='writing'?'Writing PDF…':phase==='validating'?'Validating PDF…':'Preparing PDF…')}});
   document.documentElement.dataset.saveState='delivering';chrome.status('PDF ready · choose where to save');
   const receipt=await NS.FileDelivery.deliver(result.blob,result.fileName);
   if(getDocument()===doc){
    editor.commit();
    const unchanged=doc.annotationStorage.serializable.hash===snapshotHash;
    if(receipt.method==='file-system-access'&&unchanged){doc.annotationStorage.resetModified?.();session.markSaved()}
    else session.markDirty();
    chrome.dirty();
    chrome.status(!unchanged?'Copy exported · newer edits remain unsaved':receipt.method==='file-system-access'?'Saved copy · file-system-access':receipt.method==='web-share'?'Export handed to system · storage not verified':'Download requested · storage not verified');
   }
   document.documentElement.dataset.saveState='completed';return result;
  }catch(e){
   if(getDocument()===doc){session.markDirty();chrome.dirty()}
   document.documentElement.dataset.saveState=e?.name==='AbortError'?'cancelled':'failed';
   if(e?.name==='AbortError'){chrome.status('Save cancelled');return null}
   console.error(e);chrome.error(e);chrome.status('Save failed');return null;
  }finally{saving=false;setTimeout(()=>{if(['completed','cancelled','failed'].includes(document.documentElement.dataset.saveState))document.documentElement.dataset.saveState='idle'},1200)}
 }
 return Object.freeze({save,get saving(){return saving}});
}
NS.SaveController=Object.freeze({create});})(globalThis);

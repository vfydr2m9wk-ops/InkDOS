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
 async function saveForReplacement(){
  if(!session.active||!session.dirty)return true;
  if(saving)return false;
  const doc=getDocument?.();if(!doc)return false;
  editor.commit();const snapshotHash=doc.annotationStorage.serializable.hash;
  saving=true;document.documentElement.dataset.saveState='saving';
  try{
   const result=await NS.PdfjsSaveAdapter.createCopy({pdfDocument:doc,sourceBytes:session.sourceBytes,fileName:session.fileName,onProgress:phase=>chrome.status(phase==='writing'?'Writing PDF before navigation…':phase==='validating'?'Validating PDF before navigation…':'Preparing PDF before navigation…')});
   document.documentElement.dataset.saveState='delivering';chrome.status('Save PDF before continuing…');
   await NS.FileDelivery.deliver(result.blob,result.fileName);
   if(getDocument()!==doc)return false;
   editor.commit();
   if(doc.annotationStorage.serializable.hash!==snapshotHash){session.markDirty();chrome.dirty();chrome.status('PDF changed while saving — navigation cancelled');return false}
   doc.annotationStorage.resetModified?.();session.markSaved();chrome.dirty();chrome.status('PDF saved — continuing');document.documentElement.dataset.saveState='completed';return true;
  }catch(e){
   if(getDocument()===doc){session.markDirty();chrome.dirty()}
   document.documentElement.dataset.saveState=e?.name==='AbortError'||e?.code==='cancelled'?'cancelled':'failed';
   chrome.status(document.documentElement.dataset.saveState==='cancelled'?'Save cancelled — navigation cancelled':'Save failed — navigation cancelled');return false;
  }finally{saving=false;setTimeout(()=>{if(['completed','cancelled','failed'].includes(document.documentElement.dataset.saveState))document.documentElement.dataset.saveState='idle'},1200)}
 }
 async function share(){
  if(!session.active||saving)return null;
  const doc=getDocument?.();if(!doc)return null;
  editor.commit();const wasDirty=session.dirty;saving=true;document.documentElement.dataset.saveState='sharing';
  try{
   let result;
   if(wasDirty){
    result=await NS.PdfjsSaveAdapter.createCopy({pdfDocument:doc,sourceBytes:session.sourceBytes,fileName:session.fileName,onProgress:phase=>chrome.status(phase==='writing'?'Preparing PDF to share…':phase==='validating'?'Validating PDF…':'Preparing PDF to share…')});
   }else{
    result={blob:new Blob([session.sourceBytes],{type:'application/pdf'}),fileName:NS.FileDelivery.safeName(session.fileName)};
   }
   const receipt=await NS.FileDelivery.share(result.blob,result.fileName);
   if(getDocument()===doc){editor.commit();if(wasDirty)session.markDirty();chrome.dirty();chrome.status(wasDirty?'PDF sent to Share Sheet · edits remain unsaved':'PDF sent to Share Sheet')}
   document.documentElement.dataset.saveState='completed';return {...result,receipt};
  }catch(e){
   if(getDocument()===doc&&wasDirty){session.markDirty();chrome.dirty()}
   document.documentElement.dataset.saveState=e?.name==='AbortError'?'cancelled':'failed';
   if(e?.name==='AbortError'){chrome.status('Share cancelled');return null}
   console.error(e);chrome.error(e);chrome.status('Share failed');return null;
  }finally{saving=false;setTimeout(()=>{if(['completed','cancelled','failed'].includes(document.documentElement.dataset.saveState))document.documentElement.dataset.saveState='idle'},1200)}
 }
 return Object.freeze({save,saveForReplacement,share,get saving(){return saving}});
}
NS.SaveController=Object.freeze({create});})(globalThis);

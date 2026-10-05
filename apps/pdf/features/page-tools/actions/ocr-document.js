(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
// OCR (web edition): adds an invisible text layer to scanned pages through the page-tools mutation path,
// so the result is verified, replaces the open document and stays unsaved until a copy is saved.
const available=()=>!global.InkDOSDesktop;
function create(runtime){return Object.freeze({available,isEnabled:()=>{const s=runtime.state();return available()&&s.active&&!s.busy},execute:async()=>{if(!available())return false;const s=runtime.state();if(!s.active||s.busy)return false;
  let bytes;try{bytes=await runtime.snapshotCurrent()}catch(e){runtime.chromeError(e);return false}
  if(NS.PdfOcrEngine.isSigned(bytes)){runtime.status('This PDF is digitally signed: adding a text layer would invalidate the signature.');runtime.chromeStatus('OCR not applied · signed PDF');return false}
  const need=await NS.PdfOcrEngine.pagesNeedingText(bytes);if(!need.todo.length){runtime.status('Every page already has text: nothing to recognize.');runtime.chromeStatus('OCR not needed');return false}
  let summary=null;
  const ok=await runtime.applyMutation({message:`Recognizing text on ${need.todo.length} page(s)…`,nextPage:s.currentPage,work:async source=>{const r=await NS.PdfOcrEngine.run(source,{onProgress:p=>{if(p.phase==='load')runtime.status('Loading OCR…');else if(p.phase==='recognize')runtime.status(`Recognizing text: page ${p.done} of ${p.total}`);else if(p.phase==='write')runtime.status('Writing the text layer…')}});summary=r;return {bytes:r.bytes,pageCount:r.pageCount}}});
  if(ok&&summary){runtime.status(`Text recognized on ${summary.pages} page(s) · save a copy to keep it.`);runtime.chromeStatus('OCR applied · unsaved')}
  return ok}})}
NS.PdfOcrAction=Object.freeze({create});
})(globalThis);

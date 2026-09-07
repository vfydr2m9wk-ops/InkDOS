(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function create({session,pagesHost,chrome}={}){
 function closeSavePanel(){document.getElementById('saveReadyPanel')?.remove()}
 function offerSave(result,snapshotRevision){closeSavePanel();const p=document.createElement('div');p.id='saveReadyPanel';p.className='error-overlay';p.innerHTML='<div class="error-card"><h2>Save a copy</h2><p>The original file is never overwritten.</p><p class="muted">The next action uses the best file-delivery method available in this host.</p><div class="error-actions"><button id="closeSave">Cancel</button><button id="deliverCopy" class="retry-open">Save copy</button></div></div>';document.body.appendChild(p);p.querySelector('#closeSave').onclick=closeSavePanel;p.querySelector('#deliverCopy').onclick=async()=>{const b=p.querySelector('#deliverCopy');b.disabled=true;try{chrome.status('Handing DOCX to the system…');const receipt=await NS.FileDelivery.deliver(result.blob,chrome.normalizeDocxName(result.fileName));session.markSaved(snapshotRevision);chrome.syncDirty();chrome.status(receipt.method==='web-share'?'DOCX handed to system share':'DOCX save requested');closeSavePanel()}catch(e){b.disabled=false;if(e?.code==='cancelled'){chrome.status('Save cancelled');return}console.error(e);chrome.errorPanel(e,{name:chrome.normalizeDocxName(result.fileName)});chrome.status('Save copy could not be delivered')}}}
 async function save(){if(!session.active)return;const snap=session.saveSnapshot();try{chrome.status('Preparing DOCX copy…');const result=await NS.DocxWriter.save(pagesHost,chrome.displayName(),session.sourceBuffer,session.sourceContext);offerSave(result,snap.revision);chrome.status('Copy ready — choose Save copy')}catch(e){console.error(e);chrome.errorPanel(e,{name:chrome.displayName()});chrome.status('Save copy failed')}}
 return Object.freeze({save,offerSave,closeSavePanel});
}
NS.SaveController=Object.freeze({create});
})(globalThis);

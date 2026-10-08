(function(global){'use strict';
// Preview: the open document shown with the layout of the Word file (pages, headers, footers, tables,
// images) by the docx-preview viewer published by InkDOS-tools, read only. The document is written to
// DOCX exactly as Save copy would write it and handed to the embedded viewer (io/external-viewer.js);
// nothing is uploaded. The viewer is loaded only when Preview is pressed. Pressing Preview again, or
// opening or creating a document, returns to editing.
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function create({session,pagesHost,chrome}={}){
 const $=id=>document.getElementById(id);
 const button=$('docPreviewBtn'),bar=$('formatbar'),viewport=$('viewport');
 let viewer=null,watch=null,busy=false;
 function available(){return !!(session.active&&session.kind!=='view'&&NS.ExternalViewer&&NS.DocxWriter)}
 function sync(){if(!button)return;const on=!!viewer?.active;button.setAttribute('aria-pressed',on?'true':'false');bar?.classList.toggle('is-previewing',on)}
 function close(){watch?.disconnect();watch=null;viewer?.close();sync()}
 async function open(){
  if(busy)return;
  if(!available()){chrome.status(session.kind==='view'?'Preview is for Word documents':'Open a document to preview it');return}
  busy=true;
  try{
   const name=String(chrome.displayName?.()||session.fileName||'Document').replace(/\.(docx|doc|rtf)$/i,'')+'.docx',docx=session.kind==='docx';
   chrome.status('Preparing preview…');
   const result=await NS.DocxWriter.save(pagesHost,name,docx?session.sourceBuffer:null,docx?session.sourceContext:null);
   const file=new File([result.blob],name,{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'});
   viewer=viewer||NS.ExternalViewer.create({host:viewport,cover:[pagesHost]});
   const shown=viewer.show(file,{viewer:'docx',label:'Word preview'});
   // another document (open, new, recovery) or another viewer replaces the page content: back to editing
   watch=new MutationObserver(()=>close());watch.observe(pagesHost,{childList:true});
   sync();
   await shown;busy=false;
   chrome.status('Preview · layout of the Word file · view only');
  }catch(e){
   busy=false;
   if(e?.message==='closed'){sync();return}
   console.error(e);close();chrome.status('Preview could not be shown');
   chrome.errorPanel(e,{name:session.fileName||'Document'},{title:'Preview could not be shown',retry:false});
  }
 }
 function toggle(){if(viewer?.active){close();chrome.status('Editing');return}open()}
 function install(){
  if(!button)return;
  button.addEventListener('click',toggle);
  new MutationObserver(m=>{if(viewer?.active&&m.some(r=>[...r.addedNodes].some(n=>n.classList?.contains('external-viewer')&&!n.querySelector('iframe[title="Word preview (view only)"]'))))close();sync()}).observe(viewport,{childList:true});
  sync();
 }
 return Object.freeze({install,open,close,toggle,get active(){return !!viewer?.active}});
}
NS.DocxPreview=Object.freeze({create});
})(globalThis);

(function(global){'use strict';
// Preview: the open presentation shown with the layout of the PowerPoint file (slides with their
// shapes, text, tables, charts and images) by the pptx-renderer viewer published by InkDOS-tools,
// read only. The deck is written to PPTX exactly as Save copy would write it and handed to the
// embedded viewer (io/external-viewer.js); nothing is uploaded. The viewer is loaded only when Preview
// is pressed. Pressing Preview again, or opening or creating a presentation, returns to editing.
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,save,chrome,host}={}){
 const $=id=>document.getElementById(id);
 const button=$('pptPreviewBtn'),bar=$('editbar'),canvas=$('slideCanvas');
 let viewer=null,watch=null,busy=false;
 function available(){return !!(session.active&&session.sourceKind!=='view'&&NS.ExternalViewer&&save?.buildCopy&&host)}
 function sync(){if(!button)return;const on=!!viewer?.active;button.setAttribute('aria-pressed',on?'true':'false');bar?.classList.toggle('is-previewing',on)}
 function close(){watch?.disconnect();watch=null;viewer?.close();sync()}
 async function open(){
  if(busy)return;
  if(!available()){chrome.status(session.sourceKind==='view'?'Preview is for PowerPoint presentations':'Open a presentation to preview it');return}
  busy=true;
  try{
   const result=await save.buildCopy(false);
   const name=String(result.fileName||'Presentation.pptx');
   const file=new File([result.blob],name,{type:result.blob.type||'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
   viewer=viewer||NS.ExternalViewer.create({host,cover:[...host.children]});
   const shown=viewer.show(file,{viewer:'pptx',label:'PowerPoint preview'});
   // another presentation (open, new, recovery) re-renders the slide: back to editing
   if(canvas){watch=new MutationObserver(()=>close());watch.observe(canvas,{childList:true})}
   sync();chrome.status('Opening preview…');
   await shown;busy=false;
   chrome.status('Preview · layout of the PowerPoint file · view only');
  }catch(e){
   busy=false;
   if(e?.message==='closed'){sync();return}
   console.error(e);close();chrome.status('Preview could not be shown');
  }
 }
 function toggle(){if(viewer?.active){close();chrome.status('Editing');return}open()}
 function install(){
  if(!button)return;
  button.addEventListener('click',toggle);
  // another embedded viewer (.odp / .key) replaces this one
  new MutationObserver(m=>{if(viewer?.active&&m.some(r=>[...r.addedNodes].some(n=>n.classList?.contains('external-viewer')&&n.dataset.viewer!=='pptx')))close();sync()}).observe(host,{childList:true});
  sync();
 }
 return Object.freeze({install,open,close,toggle,get active(){return !!viewer?.active}});
}
NS.PptxPreview=Object.freeze({create});
})(globalThis);

(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
// Selectable PDF text while reading (copy/paste to other apps), independent of the deferred editing tools.
// Pages that already carry the editing text layer are left to PdfjsPageLayers.
class PdfjsViewText{
  constructor(){this.mounts=new Map()}
  async onPageRendered({pageNumber,shell,record,policy}={}){if(!shell||!record?.page||!policy)return;let m=this.mounts.get(pageNumber);
    if(m&&m.shell!==shell){this.onPageUnmount(pageNumber);m=null}
    if(!m){if(shell.querySelector('.pdf-select-text-layer'))return;const div=document.createElement('div');div.className='pdf-select-text-layer';div.dataset.page=String(pageNumber);div.dataset.viewText='true';div.setAttribute('aria-label',`Selectable PDF text on page ${pageNumber}`);shell.append(div);m={pageNumber,shell,div,layer:null,token:null};this.mounts.set(pageNumber,m)}
    const viewport=record.page.getViewport({scale:policy.scale,rotation:policy.rotation}),token={};m.token=token;m.layer?.cancel?.();m.layer=null;m.div.replaceChildren();m.div.style.setProperty('--scale-factor',String(policy.scale));
    try{const content=await record.page.getTextContent({includeMarkedContent:true});if(m.token!==token||!m.div.isConnected)return;const layer=m.layer=new pdfjsLib.TextLayer({textContentSource:content,container:m.div,viewport});await layer.render()}catch(e){if(e?.name!=='AbortException')console.warn('PDF text layer failed',e)}}
  onPageUnmount(pageNumber){const m=this.mounts.get(pageNumber);if(!m)return;m.token=null;m.layer?.cancel?.();m.div.remove();this.mounts.delete(pageNumber)}
  clear(){for(const n of [...this.mounts.keys()])this.onPageUnmount(n)}
  inspect(){return Object.freeze({pages:Object.freeze([...this.mounts.keys()].sort((a,b)=>a-b))})}
}
NS.PdfjsViewText=PdfjsViewText;})(globalThis);

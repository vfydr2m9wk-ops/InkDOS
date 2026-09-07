(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
class PdfjsPageLayers{
  constructor({editor}={}){this.editor=editor;this.doc=null;this.mounts=new Map();this.formNativeState=new WeakMap();this.interaction={mode:'view',tool:'none'}}
  setDocument(doc){this.clear();this.doc=doc||null;this.editor.attachDocument(this.doc)}
  setInteractionState({mode,tool}={}){this.interaction={mode:mode==='annotate'?'annotate':'view',tool:String(tool||'none')};for(const m of this.mounts.values())this.applyInteraction(m)}
  async onPageRendered({pageNumber,shell,record,policy}){if(!this.doc||!record?.page||!shell)return;const page=record.page,viewport=page.getViewport({scale:policy.scale});shell.style.setProperty('--scale-factor',String(policy.scale));let m=this.mounts.get(pageNumber);
    if(m&&m.shell===shell){m.viewport=viewport;m.scale=policy.scale;m.annotationLayer.update({viewport});this.editor.updateLayer(pageNumber,viewport);await this.renderText(m);this.applyInteraction(m);return}
    if(m)this.onPageUnmount(pageNumber);
    const text=document.createElement('div');text.className='pdf-select-text-layer';text.dataset.page=String(pageNumber);text.setAttribute('aria-label',`Selectable PDF text on page ${pageNumber}`);
    const annDiv=document.createElement('div');annDiv.className='annotationLayer';annDiv.dataset.page=String(pageNumber);
    const editorDiv=document.createElement('div');editorDiv.className='annotationEditorLayer';editorDiv.dataset.page=String(pageNumber);
    shell.append(text,annDiv,editorDiv);
    const annotationLayer=new pdfjsLib.AnnotationLayer({div:annDiv,accessibilityManager:null,annotationCanvasMap:null,l10n:NS.PdfjsEnvironment.l10n,page,viewport});
    const annotations=await page.getAnnotations({intent:'display'});if(this.doc!==this.editor.doc||!shell.isConnected)return;
    let hasJSActions=false,fieldObjects=null;try{hasJSActions=await this.doc.hasJSActions()}catch(_){}try{fieldObjects=await this.doc.getFieldObjects()}catch(_){}
    await annotationLayer.render({annotations,linkService:NS.PdfjsEnvironment.linkService,downloadManager:NS.PdfjsEnvironment.downloadManager,imageResourcesPath:'',renderForms:true,annotationStorage:this.doc.annotationStorage,enableScripting:false,hasJSActions,fieldObjects});
    m={pageNumber,shell,page,scale:policy.scale,viewport,text,annDiv,editorDiv,annotationLayer};this.mounts.set(pageNumber,m);this.editor.createLayer({pageNumber,div:editorDiv,annotationLayer,viewport});await this.renderText(m);this.applyInteraction(m)}
  rememberControl(el){if(this.formNativeState.has(el))return this.formNativeState.get(el);const s={disabled:!!el.disabled,readOnly:'readOnly' in el?!!el.readOnly:false,tabIndex:el.tabIndex};this.formNativeState.set(el,s);return s}
  applyInteraction(m){const formsEditable=this.interaction.mode==='annotate'&&['select','none'].includes(this.interaction.tool);for(const el of m.annDiv.querySelectorAll('input,textarea,select,button')){const original=this.rememberControl(el);const textLike=el.matches('textarea,input:not([type]),input[type="text"],input[type="number"],input[type="date"],input[type="time"],input[type="email"],input[type="url"],input[type="tel"],input[type="search"],input[type="password"]');if(formsEditable){el.disabled=original.disabled;if('readOnly' in el)el.readOnly=original.readOnly;el.tabIndex=original.tabIndex}else{if(textLike&&'readOnly' in el){el.readOnly=true;el.disabled=original.disabled}else el.disabled=true;el.tabIndex=-1}}m.annDiv.dataset.formsEditable=formsEditable?'true':'false'}
  async renderText(m){const token={};m.textToken=token;m.text.replaceChildren();m.text.style.setProperty('--scale-factor',String(m.scale));try{const content=await m.page.getTextContent({includeMarkedContent:true});if(m.textToken!==token||!m.text.isConnected)return;const task=pdfjsLib.renderTextLayer({textContentSource:content,container:m.text,viewport:m.viewport,textDivs:[]});if(task?.promise)await task.promise;else if(task?.then)await task}catch(e){console.warn('PDF text layer failed',e)}}
  onPageUnmount(pageNumber){const m=this.mounts.get(pageNumber);if(!m)return;this.editor.removeLayer(pageNumber);m.text?.remove();m.annDiv?.remove();m.editorDiv?.remove();this.mounts.delete(pageNumber)}
  clear(){for(const n of [...this.mounts.keys()])this.onPageUnmount(n);this.mounts.clear();this.formNativeState=new WeakMap()}
  inspect(){return Object.freeze({pages:Object.freeze([...this.mounts.keys()].sort((a,b)=>a-b)),forms:Object.freeze([...this.mounts.values()].map(m=>m.annDiv.querySelectorAll('input,textarea,select').length)),interaction:Object.freeze({...this.interaction})})}
}
NS.PdfjsPageLayers=PdfjsPageLayers;})(globalThis);

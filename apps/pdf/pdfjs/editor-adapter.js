(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
class PdfjsEditorAdapter{
  constructor({container,viewer,session,chrome,onState}={}){
    this.container=container;this.viewer=viewer;this.session=session;this.chrome=chrome;this.onState=onState||(()=>{});
    this.doc=null;this.eventBus=new NS.PdfjsEventBus();this.uiManager=null;this.layers=new Map();this.mode='view';this.tool='none';
    this.state={hasSomethingToUndo:false,hasSomethingToRedo:false,hasSelectedEditor:false,isEditing:false,isEmpty:true};this.params={};
    this._states=e=>{this.state={...this.state,...(e?.details||{})};this.onState(this.inspect())};
    this._params=e=>{for(const item of e?.details||[]){if(Array.isArray(item)&&item.length>=2)this.params[item[0]]=item[1]}this.onState(this.inspect())};
    this.eventBus._on('editingstateschanged',this._states);
    this.eventBus._on('annotationeditorstateschanged',this._states);
    this.eventBus._on('annotationeditorparamschanged',this._params)
  }
  attachDocument(doc){this.destroyManager();this.doc=doc||null;this.lastScale=null;this.state={hasSomethingToUndo:false,hasSomethingToRedo:false,hasSelectedEditor:false,isEditing:false,isEmpty:true};this.onState(this.inspect());if(!doc)return;const alt=NS.PdfjsEnvironment.altTextManager();this.uiManager=new pdfjsLib.AnnotationEditorUIManager(this.container,this.viewer,alt,this.eventBus,doc,null);const storage=doc.annotationStorage;storage.onSetModified=()=>{this.session.markDirty();this.chrome.dirty();this.onState(this.inspect())};storage.onResetModified=()=>{this.session.markDirty();this.chrome.dirty();this.onState(this.inspect())};this.applyMode()}
  destroyManager(){for(const layer of this.layers.values())try{layer.destroy()}catch(_){}this.layers.clear();if(this.uiManager)try{this.uiManager.destroy()}catch(_){}this.uiManager=null;this.doc=null}
  createLayer({pageNumber,div,annotationLayer,viewport}){if(!this.uiManager)throw new Error('PDF editor manager not ready.');const existing=this.layers.get(pageNumber);if(existing){this.updateLayer(pageNumber,viewport);return existing}const layer=new pdfjsLib.AnnotationEditorLayer({uiManager:this.uiManager,pageIndex:pageNumber-1,div,accessibilityManager:null,annotationLayer,viewport,l10n:NS.PdfjsEnvironment.l10n});layer.render({viewport});this.layers.set(pageNumber,layer);this.applyMode();return layer}
  updateLayer(pageNumber,viewport){const layer=this.layers.get(pageNumber);if(!layer)return;const previous=layer.viewport;if(previous&&['scale','rotation','width','height'].every(key=>previous[key]===viewport[key]))return;layer.update({viewport})}
  removeLayer(pageNumber){const layer=this.layers.get(pageNumber);if(!layer)return;try{layer.destroy()}catch(_){}this.layers.delete(pageNumber)}
  setCurrentPage(pageNumber){this.eventBus.dispatch('pagechanging',{source:this,pageNumber:Number(pageNumber)||1})}
  setScale(scale){scale=Number(scale)||1;if(this.lastScale===scale)return;this.lastScale=scale;this.eventBus.dispatch('scalechanging',{source:this,scale})}
  setMode(mode){this.mode=mode==='annotate'?'annotate':'view';if(this.mode==='view'){this.tool='none';this.commit();this.unselect();const a=document.activeElement;if(a?.closest?.('.annotationEditorLayer'))try{a.blur()}catch(_){}}this.applyMode();this.onState(this.inspect())}
  setTool(tool){if(this.mode!=='annotate')this.mode='annotate';this.tool=['text','pen'].includes(tool)?tool:'none';if(this.tool==='none'){this.commit();this.unselect()}this.applyMode();this.onState(this.inspect())}
  applyMode(){if(!this.uiManager)return;let t=pdfjsLib.AnnotationEditorType.NONE;if(this.mode==='annotate'&&this.tool==='text')t=pdfjsLib.AnnotationEditorType.FREETEXT;else if(this.mode==='annotate'&&this.tool==='pen')t=pdfjsLib.AnnotationEditorType.INK;this.uiManager.updateMode(t)}
  setTextSize(v){this.uiManager?.updateParams(pdfjsLib.AnnotationEditorParamsType.FREETEXT_SIZE,Math.max(6,Math.min(72,Number(v)||14)))}
  setTextColor(v){this.uiManager?.updateParams(pdfjsLib.AnnotationEditorParamsType.FREETEXT_COLOR,String(v||'#202124'))}
  setPenColor(v){this.uiManager?.updateParams(pdfjsLib.AnnotationEditorParamsType.INK_COLOR,String(v||'#202124'))}
  setPenThickness(v){this.uiManager?.updateParams(pdfjsLib.AnnotationEditorParamsType.INK_THICKNESS,Math.max(1,Math.min(20,Number(v)||2)))}
  setPenOpacity(v){this.uiManager?.updateParams(pdfjsLib.AnnotationEditorParamsType.INK_OPACITY,Math.max(1,Math.min(100,Number(v)||100)))}
  addCommand(command){if(!this.uiManager||!command)return false;this.uiManager.addCommands(command);return true}
  undo(){this.uiManager?.undo()}
  redo(){this.uiManager?.redo()}
  deleteSelected(){this.uiManager?.delete()}
  commit(){this.uiManager?.commitOrRemove()}
  unselect(){this.uiManager?.unselectAll()}
  inspect(){return Object.freeze({mode:this.mode,tool:this.tool,state:Object.freeze({...this.state}),storageSize:this.doc?.annotationStorage?.size||0,layerPages:Object.freeze([...this.layers.keys()].sort((a,b)=>a-b))})}
  destroy(){this.destroyManager();this.eventBus.clear()}
}
NS.PdfjsEditorAdapter=PdfjsEditorAdapter;})(globalThis);

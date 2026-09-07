(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
class PdfSession{
  constructor(){this.active=false;this.fileName='Untitled.pdf';this.sourceBytes=new Uint8Array();this.pageCount=0;this.pdfVersion=null;this.pageGeometry=Object.freeze([]);this._dirty=false;this.savedAt=0}
  replaceDocument({fileName,sourceBytes,pageCount,pdfVersion,pageGeometry}){this.active=true;this.fileName=fileName||'document.pdf';this.sourceBytes=new Uint8Array(sourceBytes||[]);this.pageCount=Number(pageCount)||0;this.pdfVersion=pdfVersion||null;this.pageGeometry=Object.freeze((pageGeometry||[]).map(x=>Object.freeze({...x})));this._dirty=false;this.savedAt=0}
  markDirty(){this._dirty=true}
  markSaved(){this._dirty=false;this.savedAt=Date.now()}
  get dirty(){return this.active&&this._dirty}
}
NS.PdfSession=PdfSession;})(globalThis);
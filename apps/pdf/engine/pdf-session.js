(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
class PdfSession{
  constructor(){this.active=false;this.fileName='Untitled.pdf';this.sourceBytes=new Uint8Array();this.sourceFile=null;this.sourcePromise=null;this.pageCount=0;this.pdfVersion=null;this.pageGeometry=Object.freeze([]);this._dirty=false;this.savedAt=0}
  replaceDocument({fileName,sourceBytes,sourceFile,pageCount,pdfVersion,pageGeometry}){this.active=true;this.fileName=fileName||'document.pdf';this.sourceBytes=new Uint8Array(sourceBytes||[]);this.sourceFile=this.sourceBytes.length?null:(sourceFile||null);this.sourcePromise=null;this.pageCount=Number(pageCount)||0;this.pdfVersion=pdfVersion||null;this.pageGeometry=Object.freeze((pageGeometry||[]).map(x=>Object.freeze({...x})));this._dirty=false;this.savedAt=0}
  async ensureSourceBytes(){if(this.sourceBytes.length||!this.sourceFile)return this.sourceBytes;if(this.sourcePromise)return this.sourcePromise;const file=this.sourceFile;this.sourcePromise=file.arrayBuffer().then(buffer=>{if(this.sourceFile!==file)return this.sourceBytes;this.sourceBytes=new Uint8Array(buffer);this.sourceFile=null;return this.sourceBytes}).catch(error=>{if(this.sourceFile===file)this.sourcePromise=null;throw error});return this.sourcePromise}
  markDirty(){this._dirty=true}
  markSaved(){this._dirty=false;this.savedAt=Date.now()}
  get dirty(){return this.active&&this._dirty}
  get sourcePending(){return!!(this.active&&this.sourceFile&&!this.sourceBytes.length)}
}
NS.PdfSession=PdfSession;})(globalThis);

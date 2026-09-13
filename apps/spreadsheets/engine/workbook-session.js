(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
function safeName(name,sourceKind='xlsx'){let n=String(name||'Untitled.xlsx').trim()||'Untitled.xlsx';n=n.replace(/\.(xls|xlsx|csv|tsv)$/i,'');const ext=sourceKind==='csv'?'.csv':sourceKind==='tsv'?'.tsv':'.xlsx';return(n||'Untitled')+ext}
class WorkbookSession{
 constructor(){this.book=null;this.fileName='Untitled.xlsx';this.dirty=false;this.revision=0;this.operationId=0;this.documentId='';this.sourceKind='new'}
 beginOperation(){return++this.operationId}
 isCurrent(id){return id===this.operationId}
 commitCandidate(candidate,id){if(!this.isCurrent(id))return false;this.book=candidate.book;this.sourceKind=candidate.sourceKind||'xlsx';this.fileName=safeName(candidate.fileName||candidate.book?.fileName,this.sourceKind);this.book.fileName=this.fileName;this.documentId=candidate.documentId||('book-'+Date.now());this.dirty=false;this.revision++;return true}
 newBook(book){this.operationId++;this.book=book;book.loaded=true;book.fileName='Untitled.xlsx';this.fileName='Untitled.xlsx';this.documentId='new-'+Date.now();this.sourceKind='new';this.dirty=false;this.revision++}
 rename(name){const next=safeName(name,this.sourceKind);if(next!==this.fileName){this.fileName=next;if(this.book)this.book.fileName=next;this.markDirty()}return next}
 markDirty(){this.dirty=true;this.revision++;return this.revision}
 markClean(expectedRevision){if(Number.isInteger(expectedRevision)&&expectedRevision!==this.revision)return false;this.dirty=false;return true}
 activeSheet(){return this.book?.sheets?.[this.book.active||0]||null}
}
NS.WorkbookSession=WorkbookSession;
})(globalThis);

(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
class DocumentSession{
 constructor(){this.operationId=0;this.documentId=0;this.revision=0;this.savedRevision=0;this.fileName='Untitled.docx';this.sourceBuffer=null;this.sourceContext=null;this.mediaUrls={};this.active=false;this.kind='blank'}
 beginOperation(){return ++this.operationId}
 isCurrent(id){return id===this.operationId}
 commitOpen(id,payload){if(!this.isCurrent(id))return false;const {fileName,sourceBuffer,sourceContext,mediaUrls}=payload||{};this.documentId++;this.fileName=fileName||'Document.docx';this.sourceBuffer=sourceBuffer||null;this.sourceContext=sourceContext||null;this.mediaUrls=mediaUrls||{};this.active=true;this.kind=sourceBuffer?'imported':'blank';this.revision=0;this.savedRevision=0;return true}
 markDirty(){this.revision++;return this.revision}
 markSaved(snapshotRevision){if(snapshotRevision!==this.revision)return false;this.savedRevision=this.revision;return true}
 get dirty(){return this.revision!==this.savedRevision}
 saveSnapshot(){return Object.freeze({documentId:this.documentId,revision:this.revision,fileName:this.fileName,sourceBuffer:this.sourceBuffer,sourceContext:this.sourceContext})}
 invalidatePending(){this.operationId++}
}
NS.DocumentSession=DocumentSession;
})(globalThis);

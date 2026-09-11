(function(g){'use strict';
  const NS=g.InkDOS2=g.InkDOS2||{};
  class DocumentSession{
    constructor(init={}){this.sessionId=init.sessionId||cryptoId();this.documentId=init.documentId||cryptoId();this.revision=0;this.operationId=0;this.sourceHash=init.sourceHash||null;this.dirty=false;this.checkpointRevision=null;this.exportRevision=null;}
    beginOperation(){this.operationId+=1;return this.operationId;}
    isCurrentOperation(id){return id===this.operationId;}
    mutate(){this.revision+=1;this.dirty=true;return this.revision;}
    sourceOpened(hash){this.revision=0;this.operationId+=1;this.sourceHash=hash||null;this.dirty=false;this.checkpointRevision=null;this.exportRevision=null;}
    markCheckpoint(rev){if(Number.isInteger(rev)&&rev<=this.revision)this.checkpointRevision=rev;}
    markExport(rev){if(Number.isInteger(rev)&&rev<=this.revision){this.exportRevision=rev;if(rev===this.revision)this.dirty=false;}}
    snapshot(){return Object.freeze({sessionId:this.sessionId,documentId:this.documentId,revision:this.revision,operationId:this.operationId,sourceHash:this.sourceHash,dirty:this.dirty,checkpointRevision:this.checkpointRevision,exportRevision:this.exportRevision});}
  }
  function cryptoId(){if(g.crypto&&g.crypto.randomUUID)return g.crypto.randomUUID();return 'id-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);}
  NS.DocumentSession=DocumentSession;
})(globalThis);
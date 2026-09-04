(function(global){
'use strict';
const STATES=Object.freeze({
  CLEAN:'clean',DIRTY:'dirty',EXPORT_PREPARING:'export-preparing',
  DOWNLOAD_REQUESTED_UNVERIFIED:'download-requested-unverified',
  EXPORT_FAILED:'export-failed',EXPORT_VERIFIED:'export-verified'
});
const LABELS=Object.freeze({
  [STATES.CLEAN]:'No changes',
  [STATES.DIRTY]:'Changes not exported',
  [STATES.EXPORT_PREPARING]:'Preparing copy…',
  [STATES.DOWNLOAD_REQUESTED_UNVERIFIED]:'Download requested — not verified',
  [STATES.EXPORT_FAILED]:'Export failed',
  [STATES.EXPORT_VERIFIED]:'Exported copy reopened successfully'
});
const activeControllers=new Set();
let unloadGuardInstalled=false;

function anyWorkspaceNeedsWarning(){
  for(const controller of activeControllers){
    try{
      if(controller.shouldWarnBeforeUnload())return true;
    }catch(error){
      console.error('File lifecycle guard failed.',error);
    }
  }
  return false;
}

function installUnloadGuard(){
  if(unloadGuardInstalled||!global.addEventListener)return;
  unloadGuardInstalled=true;
  global.addEventListener('beforeunload',event=>{
    if(!anyWorkspaceNeedsWarning())return;
    event.preventDefault();
    event.returnValue='';
  });
}

function create(options={}){
  let state=STATES.CLEAN,revision=0,verifiedRevision=0,lastError=null,lastExport=null;
  const listeners=new Set();
  if(typeof options.onChange==='function')listeners.add(options.onChange);
  function snapshot(){return Object.freeze({state,label:LABELS[state],revision,verifiedRevision,lastError,lastExport,hasUnverifiedChanges:revision!==verifiedRevision,shouldWarnBeforeUnload:revision!==verifiedRevision});}
  function emit(){const value=snapshot();for(const fn of listeners){try{fn(value)}catch(error){console.error('File lifecycle listener failed.',error)}}return value}
  function transition(next,details={}){state=next;if(Object.prototype.hasOwnProperty.call(details,'error'))lastError=details.error||null;if(Object.prototype.hasOwnProperty.call(details,'export'))lastExport=details.export||null;return emit()}
  const controller={
    get state(){return state},get label(){return LABELS[state]},snapshot,
    subscribe(fn){if(typeof fn!=='function')throw new TypeError('Lifecycle listener must be a function.');listeners.add(fn);return()=>listeners.delete(fn)},
    sourceOpened(){revision=0;verifiedRevision=0;lastError=null;lastExport=null;return transition(STATES.CLEAN)},
    markDirty(){revision++;lastError=null;return transition(STATES.DIRTY)},
    beginExport(){return transition(STATES.EXPORT_PREPARING)},
    downloadRequested(metadata={}){return transition(STATES.DOWNLOAD_REQUESTED_UNVERIFIED,{export:Object.freeze(Object.assign({verified:false,sha256:null},metadata))})},
    exportFailed(error){return transition(STATES.EXPORT_FAILED,{error:error instanceof Error?error:new Error(String(error||'Export failed'))})},
    verifyReopened(metadata={}){
      const expected=lastExport||{},actualHash=String(metadata.sha256||''),expectedHash=String(expected.sha256||'');
      if(!expectedHash||!actualHash||actualHash!==expectedHash||Number(metadata.bytes)!==Number(expected.bytes))throw new Error('The reopened file does not match the exported copy fingerprint.');
      verifiedRevision=revision;return transition(STATES.EXPORT_VERIFIED,{error:null,export:Object.freeze(Object.assign({},expected,metadata,{verified:true}))})
    },
    resetClean(){verifiedRevision=revision;return transition(STATES.CLEAN,{error:null,export:null})},
    shouldWarnBeforeUnload(){return revision!==verifiedRevision},
    confirmDiscard(message='You have unsaved changes. Continue and discard them?'){
      return revision===verifiedRevision||global.confirm(message);
    },
    destroy(){activeControllers.delete(controller);listeners.clear()}
  };
  activeControllers.add(controller);
  installUnloadGuard();
  emit();
  return Object.freeze(controller);
}
installUnloadGuard();
global.InkDOSFileLifecycle=Object.freeze({
  version:'0.20.0',
  STATES,
  LABELS,
  create,
  anyWorkspaceNeedsWarning
});
})(window);

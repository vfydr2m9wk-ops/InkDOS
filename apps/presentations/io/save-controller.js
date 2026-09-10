(function(global){'use strict';
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,chrome}={}){
  let busy=false,p1Loader=null,p2Loader=null;
  function loadLocal(src,test,label){if(test())return Promise.resolve();return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=()=>test()?resolve():reject(new Error(label+' did not initialize.'));s.onerror=()=>reject(new Error(label+' could not be loaded locally.'));document.head.appendChild(s)})}
  function ensureP1Writer(){if(NS.PptP1StructureWriter&&NS.PptP1ObjectWriter)return Promise.resolve();if(p1Loader)return p1Loader;p1Loader=(async()=>{await loadLocal('io/ppt-p1-structure-writer.js',()=>!!NS.PptP1StructureWriter,'PPT-P1 structure writer');await loadLocal('io/ppt-p1-object-writer.js',()=>!!NS.PptP1ObjectWriter,'PPT-P1 object writer')})();return p1Loader}
  function ensureP2Package(){if(NS.PptP2Package)return Promise.resolve();if(p2Loader)return p2Loader;p2Loader=loadLocal('io/ppt-p2-package.js',()=>!!NS.PptP2Package,'PPT-P2 package module');return p2Loader}
  function outputName(){const n=String(session.fileName||'Presentation.pptx');return /\.ppt$/i.test(n)?n.replace(/\.ppt$/i,'.pptx'):(/\.pptx$/i.test(n)?n:n+'.pptx')}
  async function buildCopy(sharing=false){
    if(!session.active)throw new Error('No presentation is open.');
    await ensureP1Writer();let bytes,receipt={mode:session.sourceKind==='ppt'?'legacy-ppt-to-editable-pptx':'generated-pptx-home-editing'};
    if(session.sourceKind==='pptx'){
      chrome.status(sharing?'Preparing PPTX to share…':'Preparing PPTX copy…');
      const result=await NS.PptxPreservationWriter.build(session);bytes=result.bytes;receipt=result.receipt;
    }else{
      chrome.status(session.sourceKind==='ppt'?(sharing?'Converting legacy PPT to editable PPTX for sharing…':'Converting legacy PPT to editable PPTX copy…'):(sharing?'Building PPTX to share…':'Building PPTX copy…'));bytes=await NS.PptxWriter.build(session);
    }
    await ensureP2Package();bytes=await NS.PptP2Package.applySlideCompletion(session,bytes,receipt);
    return {bytes,receipt,blob:new Blob([bytes],{type:NS.FileDelivery.MIME}),fileName:outputName()};
  }
  async function save(){
    if(!session.active||busy)return null;busy=true;
    try{
      const {bytes,receipt,blob,fileName}=await buildCopy(false);
      const delivery=await NS.FileDelivery.deliver(blob,fileName);
      if(delivery.deliveryConfirmed){
        if(session.sourceKind==='pptx'){
          session.acceptConfirmedPptx(bytes,receipt);
          for(const slide of session.slides||[]){slide.transitionEdited=false;slide.notesEdited=false}
        }else if(session.sourceKind!=='ppt')session.dirty=false;
        chrome.status(session.sourceKind==='ppt'?'Editable PPTX copy saved · open the .pptx copy to edit':'PPTX copy saved');
      }else chrome.status(session.sourceKind==='ppt'?'Editable PPTX copy generated · delivery requested':'PPTX copy generated · delivery requested');
      chrome.title();return {...delivery,bytes,receipt,fileName};
    }catch(e){if(e?.code!=='cancelled')chrome.showError(e,{name:session.fileName});return null}finally{busy=false}
  }
  async function share(){
    if(!session.active||busy)return null;busy=true;
    try{const {bytes,receipt,blob,fileName}=await buildCopy(true);const delivery=await NS.FileDelivery.share(blob,fileName);chrome.status(session.sourceKind==='ppt'?'Editable PPTX copy sent to Share Sheet':'PPTX sent to Share Sheet');chrome.title();return {...delivery,bytes,receipt,fileName}}
    catch(e){if(e?.code==='cancelled')chrome.status('Share cancelled');else chrome.showError(e,{name:session.fileName});return null}finally{busy=false}
  }
  return Object.freeze({save,share,buildCopy,ensureP1Writer,ensureP2Package,outputName})
}
NS.SaveController=Object.freeze({create});
})(globalThis);

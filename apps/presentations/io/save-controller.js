(function(global){'use strict';
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,chrome}={}){
  let busy=false;
  async function buildCopy(sharing=false){
    if(session.sourceKind==='ppt')throw new Error('Legacy PPT is read-only. Share and Save Copy are available for new presentations and PPTX files.');
    let bytes,receipt={mode:'generated-pptx'};
    if(session.sourceKind==='pptx'){
      chrome.status(sharing?'Preparing PPTX to share…':'Preparing PPTX copy…');
      const result=await NS.PptxPreservationWriter.build(session);bytes=result.bytes;receipt=result.receipt;
    }else{
      chrome.status(sharing?'Building PPTX to share…':'Building PPTX copy…');bytes=await NS.PptxWriter.build(session);
    }
    return {bytes,receipt,blob:new Blob([bytes],{type:NS.FileDelivery.MIME})};
  }
  async function save(){
    if(busy)return null;busy=true;
    try{
      const {bytes,receipt,blob}=await buildCopy(false);
      const delivery=await NS.FileDelivery.deliver(blob,session.fileName);
      if(delivery.deliveryConfirmed){
        if(session.sourceKind==='pptx')session.acceptConfirmedPptx(bytes,receipt);else session.dirty=false;
        chrome.status('PPTX copy saved');
      }else{
        chrome.status('PPTX copy generated · delivery requested');
      }
      chrome.title();
      return {...delivery,bytes,receipt};
    }catch(e){if(e?.code!=='cancelled')chrome.showError(e,{name:session.fileName});return null}
    finally{busy=false}
  }
  async function share(){
    if(busy)return null;busy=true;
    try{
      const {bytes,receipt,blob}=await buildCopy(true);
      const delivery=await NS.FileDelivery.share(blob,session.fileName);
      chrome.status('PPTX sent to Share Sheet');
      chrome.title();
      return {...delivery,bytes,receipt};
    }catch(e){if(e?.code==='cancelled')chrome.status('Share cancelled');else chrome.showError(e,{name:session.fileName});return null}
    finally{busy=false}
  }
  return Object.freeze({save,share})
}
NS.SaveController=Object.freeze({create});
})(globalThis);

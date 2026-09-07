(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
function create({session,setLoading,onStatus,onError,onSessionChanged}={}){let saveId=0;
 async function save(){if(!session.book?.loaded)return false;const id=++saveId,revision=session.revision,fileName=NS.FileDelivery.safeName(session.fileName);try{setLoading?.(true,'Preparing XLSX copy…');NS.FormulaEvaluator.recalculate(session.book);const blob=await root.LocalXLSX.saveCopy(session.book);if(id!==saveId)return false;const result=await NS.FileDelivery.deliver(blob,fileName);if(revision===session.revision&&session.markClean(revision))onSessionChanged?.();onStatus?.(`XLSX copy prepared · ${result.method}`);return result}catch(error){if(error?.code!=='cancelled')onError?.(error);return false}finally{setLoading?.(false)}}
 return Object.freeze({save})}
NS.SaveController=Object.freeze({create});
})(globalThis);

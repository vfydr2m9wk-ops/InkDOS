(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{},session=new NS.WorkbookSession(),dialog=NS.SessionDialog.create(),chrome=NS.ChromeController.create({session,dialog}),actions={};let editorController=null,leaving=false,authorizedUnload=false;
NS.Appearance.install();chrome.sync();
// .ods / .numbers: shown read-only by an embedded open-source viewer (io/external-viewer.js) over the grid
let externalViewer=null;
function viewer(){if(!externalViewer&&NS.ExternalViewer)externalViewer=NS.ExternalViewer.create({host:document.getElementById('contentViewport'),cover:[document.getElementById('gridStage'),document.getElementById('startState')]});return externalViewer}
function onCommitted(info){if(!editorController){editorController=NS.EditorController.create({session,chrome,dialog,actions});chrome.bindEditorControls(editorController.commands)}editorController.activate();chrome.sync();if(info.sourceKind==='view'){const name=info.file?.name||session.fileName;chrome.setStatus(name+' · View only');viewer()?.show(info.file).then(()=>{if(session.fileName===name)chrome.setStatus(name+' · View only · shown without converting')},error=>{if(error?.message==='closed')return;chrome.showError(error);chrome.setStatus(name+' could not be shown')});return}externalViewer?.close();chrome.toast(info.newBook?'New workbook created':`${session.book.sheets.length} worksheet${session.book.sheets.length===1?'':'s'} opened${info.legacy?' · XLS shown view-only':''}`)}
const saveController=NS.SaveController.create({session,dialog,setLoading:chrome.setLoading,onStatus:chrome.toast,onError:error=>chrome.showError(error,{title:'Workbook could not be saved'}),onSessionChanged:chrome.sync});
const openController=NS.FileOpenController.create({session,fileInput:document.getElementById('fileInput'),dialog,saveController,setLoading:chrome.setLoading,onCommitted,onError:chrome.showError});
actions.open=openController.requestOpen;actions.save=saveController.save;actions.new=openController.newWorkbook;
document.addEventListener('inkdos:file-launch-error',e=>chrome.showError(new Error(e.detail?.message||'The selected file could not be opened.')));root.InkDOSFileLaunch?.setOpenHandler?.(file=>openController.handle(file));
NS.FileMenuController.create({chrome,openController,saveController,session});
NS.FrameUI.installToolbarRail(document.getElementById('formatbar'));
const home=document.querySelector('a[aria-label="Home"]');home?.addEventListener('click',async e=>{if(leaving||!session.dirty)return;e.preventDefault();leaving=true;try{if(await openController.requestLeave()){authorizedUnload=true;root.location.href=home.href}}finally{leaving=false}});
window.addEventListener('beforeunload',e=>{if(authorizedUnload){authorizedUnload=false;return}if(!session.dirty)return;e.preventDefault();e.returnValue=''});
// Recovery draft while there are unsaved changes (shared/work-safety.js): the workbook as an XLSX copy.
root.InkDOSWorkSafety?.attachRecovery({app:'spreadsheets',isDirty:()=>!!(session.book&&session.dirty),revision:()=>session.revision,snapshot:async()=>{const base=String(session.fileName||'Workbook').replace(/\.(xlsx|xls|csv|tsv)$/i,'');return{data:await root.LocalXLSX.saveCopy(session.book),name:base+'.xlsx'}},restore:async file=>{await openController.handle(file);session.markDirty();chrome.sync()}});
root.__inkdosSpreadsheetsS1=Object.freeze({get session(){return session},get editor(){return editorController},openController,saveController});
})(globalThis);
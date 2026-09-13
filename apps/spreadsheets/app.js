(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{},session=new NS.WorkbookSession(),dialog=NS.SessionDialog.create(),chrome=NS.ChromeController.create({session}),actions={};let editorController=null,leaving=false,authorizedUnload=false;
NS.Appearance.install();chrome.sync();
function onCommitted(info){if(!editorController){editorController=NS.EditorController.create({session,chrome,dialog,actions});chrome.bindEditorControls(editorController.commands)}editorController.activate();chrome.sync();chrome.toast(info.newBook?'New workbook created':`${session.book.sheets.length} worksheet${session.book.sheets.length===1?'':'s'} opened${info.legacy?' · XLS imported as editable XLSX model':''}`)}
const saveController=NS.SaveController.create({session,dialog,setLoading:chrome.setLoading,onStatus:chrome.toast,onError:chrome.showError,onSessionChanged:chrome.sync});
const openController=NS.FileOpenController.create({session,fileInput:document.getElementById('fileInput'),dialog,saveController,setLoading:chrome.setLoading,onCommitted,onError:chrome.showError});
actions.open=openController.requestOpen;actions.save=saveController.save;actions.new=openController.newWorkbook;
NS.FileMenuController.create({chrome,openController,saveController});
NS.FrameUI.installToolbarRail(document.getElementById('formatbar'));
const home=document.querySelector('a[aria-label="Home"]');home?.addEventListener('click',async e=>{if(leaving||!session.dirty)return;e.preventDefault();leaving=true;try{if(await openController.requestLeave()){authorizedUnload=true;root.location.href=home.href}}finally{leaving=false}});
window.addEventListener('beforeunload',e=>{if(authorizedUnload){authorizedUnload=false;return}if(!session.dirty)return;e.preventDefault();e.returnValue=''});
root.__inkdosSpreadsheetsS1=Object.freeze({get session(){return session},get editor(){return editorController},openController,saveController});
})(globalThis);
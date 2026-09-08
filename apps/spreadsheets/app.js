(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{},session=new NS.WorkbookSession(),dialog=NS.SessionDialog.create(),chrome=NS.ChromeController.create({session}),actions={};let editorController=null;
NS.Appearance.install();chrome.sync();
function onCommitted(info){if(!editorController){editorController=NS.EditorController.create({session,chrome,dialog,actions});chrome.bindEditorControls(editorController.commands)}editorController.activate();chrome.sync();chrome.toast(info.newBook?'New workbook created':`${session.book.sheets.length} worksheet${session.book.sheets.length===1?'':'s'} opened${info.legacy?' · XLS imported as editable XLSX model':''}`)}
const openController=NS.FileOpenController.create({session,fileInput:document.getElementById('fileInput'),dialog,setLoading:chrome.setLoading,onCommitted,onError:chrome.showError});
const saveController=NS.SaveController.create({session,setLoading:chrome.setLoading,onStatus:chrome.toast,onError:chrome.showError,onSessionChanged:chrome.sync});
actions.open=openController.requestOpen;actions.save=saveController.save;actions.new=openController.newWorkbook;
NS.FileMenuController.create({chrome,openController,saveController});
NS.FrameUI.installToolbarRail(document.getElementById('formatbar'));
window.addEventListener('beforeunload',e=>{if(!session.dirty)return;e.preventDefault();e.returnValue=''});
root.__inkdosSpreadsheetsS1=Object.freeze({get session(){return session},get editor(){return editorController},openController,saveController});
})(globalThis);
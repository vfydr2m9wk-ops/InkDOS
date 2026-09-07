(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
function create({chrome,openController,saveController}={}){const $=id=>document.getElementById(id);$('menuNew').onclick=async()=>{chrome.drawer.close();await openController.newWorkbook()};$('menuOpen').onclick=async()=>{chrome.drawer.close();await openController.requestOpen()};$('menuSave').onclick=async()=>{chrome.drawer.close();await saveController.save()};$('startNew').onclick=()=>openController.newWorkbook();$('startOpen').onclick=()=>openController.requestOpen();return Object.freeze({})}
NS.FileMenuController=Object.freeze({create});
})(globalThis);

(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{},$=id=>document.getElementById(id);
function create({session,chrome,fileOpen,save,layout,editor,navigation,modeController}={}){const drawer=NS.FrameUI.bindDrawer({trigger:$('menuBtn'),drawer:$('generalMenu'),backdrop:$('menuBackdrop'),closeButton:$('closeMenuBtn')});
 function syncPage(){const n=layout.currentPage||1;$('pageInput').value=String(n);$('pageCount').textContent='/ '+(layout.pageCount||0);chrome.page(n,layout.pageCount);navigation?.syncCurrent(n);editor.setCurrentPage(n)}
 function syncEditor(){const s=editor.inspect().state;$('undoBtn').disabled=!s.hasSomethingToUndo;$('redoBtn').disabled=!s.hasSomethingToRedo;$('deleteAnnotationBtn').disabled=!s.hasSelectedEditor}
 function install(){
  $('undoBtn').onclick=()=>{editor.undo();syncEditor()};$('redoBtn').onclick=()=>{editor.redo();syncEditor()};$('deleteAnnotationBtn').onclick=()=>{editor.deleteSelected();syncEditor()};
  $('prevPageBtn').onclick=()=>layout.prev();$('nextPageBtn').onclick=()=>layout.next();$('pageInput').addEventListener('change',()=>layout.goToPage(Number($('pageInput').value)));
  $('openMenuBtn').onclick=()=>{drawer.close();fileOpen.chooseFile()};$('saveMenuBtn').onclick=()=>{drawer.close();save.save()};$('saveToolbarBtn').onclick=()=>save.save();
  $('textSize').onchange=e=>editor.setTextSize(e.target.value);$('textColor').onchange=e=>editor.setTextColor(e.target.value);$('penColor').onchange=e=>editor.setPenColor(e.target.value);$('penThickness').onchange=e=>editor.setPenThickness(e.target.value);$('penOpacity').onchange=e=>editor.setPenOpacity(e.target.value);
  document.querySelectorAll('[data-appearance-choice]').forEach(b=>b.onclick=()=>NS.Appearance.set(b.dataset.appearanceChoice));
  document.addEventListener('keydown',e=>{const key=e.key.toLowerCase(),editing=/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName||'')||document.activeElement?.isContentEditable;if((e.metaKey||e.ctrlKey)&&key==='o'){e.preventDefault();fileOpen.chooseFile();return}if((e.metaKey||e.ctrlKey)&&key==='s'){e.preventDefault();save.save();return}if(!editing&&(e.metaKey||e.ctrlKey)&&key==='z'&&modeController.mode==='annotate'){e.preventDefault();e.shiftKey?editor.redo():editor.undo();syncEditor();return}if(!editing&&e.key==='Delete'&&modeController.mode==='annotate'){editor.deleteSelected();syncEditor();return}if(!editing&&e.key==='Escape'){editor.unselect();modeController.setTool('none');syncEditor()}});
  syncEditor();syncPage()}
 return Object.freeze({install,syncEditor,syncPage})}
NS.CommandController=Object.freeze({create});})(globalThis);
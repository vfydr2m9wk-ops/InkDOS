(function(global){'use strict';const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,history,chrome,fileOpen,save,editor,panel,slideshow}={}){
 const $=id=>document.getElementById(id);let drawer=null,zoomPopover=null;
 function sync(){
  chrome.title();chrome.stats();
  const legacy=session.sourceKind==='ppt';
  $('saveMenuBtn').disabled=legacy;
  $('saveMenuBtn').title=legacy?'Legacy PPT is read-only.':'Save PPTX copy';
  $('titleText').readOnly=legacy;
  editor.sync()
 }
 function refresh({thumbs=true,center=true}={}){editor.rerender({thumbs,center});sync()}
 function requestNew(){if(session.dirty&&!confirm('Discard current in-memory changes and create a new presentation?'))return false;session.resetNew();history.reset();refresh();chrome.status('New presentation');drawer?.close();return true}
 function install(){
  drawer=NS.FrameUI.bindDrawer({trigger:$('menuBtn'),drawer:$('generalMenu'),backdrop:$('menuBackdrop'),closeButton:$('closeMenuBtn')});zoomPopover=NS.FrameUI.bindPopover({trigger:$('zoomMenuBtn'),popover:$('zoomPopover')});
  $('newMenuBtn').onclick=requestNew;
  $('openMenuBtn').onclick=()=>{drawer.close({restoreFocus:false});fileOpen.requestOpen()};
  $('saveMenuBtn').onclick=async()=>{if(session.sourceKind==='ppt')return;drawer.close({restoreFocus:false});await save.save();sync()};
  document.querySelectorAll('[data-appearance-choice]').forEach(b=>b.onclick=()=>NS.Appearance.set(b.dataset.appearanceChoice));
  $('titleText').addEventListener('change',e=>{if(session.sourceKind==='ppt'){chrome.title();return}const next=chrome.normalizeName(e.target.value);if(next!==session.fileName){history.transact('Rename presentation',()=>session.fileName=next);sync()}else chrome.title()});
  $('presentBtn').onclick=()=>slideshow.open(false);
  $('presentStartMenuBtn').onclick=()=>{drawer.close({restoreFocus:false});slideshow.open(true)};
  document.addEventListener('keydown',e=>{const mod=e.metaKey||e.ctrlKey;if(!mod)return;const k=e.key.toLowerCase();if(k==='o'){e.preventDefault();fileOpen.requestOpen()}else if(k==='n'){e.preventDefault();requestNew()}else if(k==='s'){e.preventDefault();if(session.sourceKind!=='ppt')save.save()}else if(k==='z'&&!e.shiftKey&&!e.target.isContentEditable){e.preventDefault();$('undoBtn').click()}else if((k==='y'||(k==='z'&&e.shiftKey))&&!e.target.isContentEditable){e.preventDefault();$('redoBtn').click()}});
  sync()
 }
 return Object.freeze({install,sync,refresh,requestNew,get drawer(){return drawer},get zoomPopover(){return zoomPopover}})
}
NS.CommandController=Object.freeze({create});})(globalThis);

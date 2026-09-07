(function(global){'use strict';const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,history,chrome,fileOpen,save,editor,panel,slideshow}={}){
 const $=id=>document.getElementById(id);let drawer=null,zoomPopover=null;
 function installShareAction(){const saveBtn=$('saveMenuBtn');if(!saveBtn||$('shareMenuBtn'))return;const share=document.createElement('button');share.id='shareMenuBtn';share.className='menu-item';share.type='button';share.disabled=true;share.innerHTML='<svg viewBox="0 0 24 24"><path d="M12 15V3"/><path d="m8 7 4-4 4 4"/><path d="M5 11v8a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-8"/></svg><span>Share</span><span class="hint">PPTX</span>';saveBtn.insertAdjacentElement('afterend',share);share.onclick=async()=>{if(!session.active||session.sourceKind==='ppt')return;drawer.close({restoreFocus:false});await save.share();sync()}}
 function sync(){
  chrome.title();chrome.stats();
  const active=session.active,legacy=session.sourceKind==='ppt',canExport=active&&!legacy;
  $('saveMenuBtn').disabled=!canExport;
  $('saveMenuBtn').title=!active?'Create or open a presentation first.':legacy?'Legacy PPT is read-only.':'Save PPTX copy';
  const share=$('shareMenuBtn');if(share){share.disabled=!canExport;share.title=!active?'Create or open a presentation first.':legacy?'Legacy PPT is read-only.':'Share PPTX'}
  $('titleText').readOnly=!active||legacy;
  $('presentBtn').disabled=!active;$('presentStartMenuBtn').disabled=!active;
  editor.sync()
 }
 function refresh({thumbs=true,center=true}={}){editor.rerender({thumbs,center});sync()}
 function requestNew(){if(session.dirty&&!confirm('Discard current in-memory changes and create a new presentation?'))return false;session.resetNew();history.reset();refresh();chrome.status('New presentation');drawer?.close();return true}
 function install(){
  drawer=NS.FrameUI.bindDrawer({trigger:$('menuBtn'),drawer:$('generalMenu'),backdrop:$('menuBackdrop'),closeButton:$('closeMenuBtn')});zoomPopover=NS.FrameUI.bindPopover({trigger:$('zoomMenuBtn'),popover:$('zoomPopover')});
  installShareAction();
  $('newMenuBtn').onclick=requestNew;
  $('openMenuBtn').onclick=()=>{drawer.close({restoreFocus:false});fileOpen.requestOpen()};
  $('saveMenuBtn').onclick=async()=>{if(!session.active||session.sourceKind==='ppt')return;drawer.close({restoreFocus:false});await save.save();sync()};
  document.querySelectorAll('[data-appearance-choice]').forEach(b=>b.onclick=()=>NS.Appearance.set(b.dataset.appearanceChoice));
  $('titleText').addEventListener('change',e=>{if(!session.active||session.sourceKind==='ppt'){chrome.title();return}const next=chrome.normalizeName(e.target.value);if(next!==session.fileName){history.transact('Rename presentation',()=>session.fileName=next);sync()}else chrome.title()});
  $('presentBtn').onclick=()=>{if(session.active)slideshow.open(false)};
  $('presentStartMenuBtn').onclick=()=>{if(!session.active)return;drawer.close({restoreFocus:false});slideshow.open(true)};
  document.addEventListener('keydown',e=>{const mod=e.metaKey||e.ctrlKey;if(!mod)return;const k=e.key.toLowerCase();if(k==='o'){e.preventDefault();fileOpen.requestOpen()}else if(k==='n'){e.preventDefault();requestNew()}else if(k==='s'){e.preventDefault();if(session.active&&session.sourceKind!=='ppt')save.save()}else if(k==='z'&&!e.shiftKey&&!e.target.isContentEditable){e.preventDefault();$('undoBtn').click()}else if((k==='y'||(k==='z'&&e.shiftKey))&&!e.target.isContentEditable){e.preventDefault();$('redoBtn').click()}});
  sync()
 }
 return Object.freeze({install,sync,refresh,requestNew,get drawer(){return drawer},get zoomPopover(){return zoomPopover}})
}
NS.CommandController=Object.freeze({create});})(globalThis);

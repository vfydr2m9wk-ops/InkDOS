(function(global){'use strict';const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,history,selection,chrome,fileOpen,save,editor,panel,slideshow,onStructureChange}={}){
 const $=id=>document.getElementById(id);let drawer=null,zoomPopover=null;const registry=new Map();
 function register(id,handler,isEnabled=()=>true){if(!id||typeof handler!=='function')throw new TypeError('Invalid Presentations command');registry.set(id,Object.freeze({handler,isEnabled}));return id}
 function isEnabled(id){const command=registry.get(id);return !!command&&command.isEnabled()!==false}
 function execute(id,...args){const command=registry.get(id);if(!command)throw new Error('PRESENTATIONS_COMMAND_NOT_REGISTERED: '+id);if(command.isEnabled()===false)return false;return command.handler(...args)}
 function selected(){return selection.getObject(session)}
 function structureEditable(){return session.active&&session.sourceKind!=='ppt'}
 function textEditable(){const o=selected();return !!o&&o.type==='text'&&session.active&&session.sourceKind!=='ppt'}
 function eachRun(o,fn){for(const p of o.paragraphs||[])for(const r of p.runs||[])fn(r,p)}
 function refresh({thumbs=true,center=true}={}){editor.rerender({thumbs,center});sync()}
 function format(label,mutator){const o=selected();if(!o||o.type!=='text')return false;history.transact(label,()=>mutator(o));refresh({thumbs:true,center:false});return true}
 function navigateTo(value){const index=Number(value);if(!Number.isInteger(index)||index<0||index>=session.slides.length||index===session.currentIndex)return false;session.setCurrentByIndex(index);selection.clear();refresh({thumbs:false,center:true});panel.syncActive();return true}
 function installCommands(){
  register('file.new',()=>{if(session.dirty&&!global.confirm('Discard current in-memory changes and create a new presentation?'))return false;session.resetNew();history.reset();onStructureChange?.();refresh();chrome.status('New presentation');return true});
  register('file.open',()=>fileOpen.requestOpen());
  register('file.save',()=>save.save(),()=>session.active);
  register('file.share',()=>save.share(),()=>session.active);
  register('file.rename',value=>{const next=chrome.normalizeName(value);if(next!==session.fileName){history.transact('Rename presentation',()=>session.fileName=next);sync();return true}chrome.title();return false},()=>session.active&&session.sourceKind!=='ppt');
  register('appearance.set',value=>NS.Appearance.set(value));
  register('presentation.present.current',()=>slideshow.open(false),()=>session.active);
  register('presentation.present.start',()=>slideshow.open(true),()=>session.active);
  register('history.undo',()=>{if(!history.undo())return false;selection.clear();refresh({thumbs:true,center:false});return true},()=>history.canUndo);
  register('history.redo',()=>{if(!history.redo())return false;selection.clear();refresh({thumbs:true,center:false});return true},()=>history.canRedo);
  register('panel.toggle',()=>{panel.toggle();editor.sync();return true},()=>session.active);
  register('slide.add',()=>{history.transact('Add slide',()=>session.addSlide());selection.clear();onStructureChange?.();refresh({thumbs:true,center:true});return true},structureEditable);
  register('slide.duplicate',()=>{history.transact('Duplicate slide',()=>session.duplicateCurrent());selection.clear();onStructureChange?.();refresh({thumbs:true,center:true});return true},structureEditable);
  register('slide.delete',()=>{history.transact('Delete slide',()=>session.deleteCurrent());selection.clear();onStructureChange?.();refresh({thumbs:true,center:true});return true},()=>structureEditable()&&session.slides.length>1);
  register('slide.move',delta=>{delta=Number(delta)||0;if(!delta)return false;history.transact(delta<0?'Move slide earlier':'Move slide later',()=>session.moveCurrent(delta));selection.clear();onStructureChange?.();refresh({thumbs:true,center:false});return true},structureEditable);
  register('edit.insertText',()=>{let obj=null;history.transact('Insert text',()=>{obj=session.addText()});selection.select(obj?.id);refresh({thumbs:true,center:false});return obj?.id||true},()=>session.active&&session.sourceKind!=='ppt');
  register('format.fontSize',value=>format('Font size',o=>{const v=Math.max(8,Math.min(96,Number(value)||24));o.fontSizePt=v;eachRun(o,r=>r.fontSizePt=v)}),textEditable);
  register('format.bold',()=>format('Bold',o=>{o.bold=!o.bold;eachRun(o,r=>r.bold=o.bold)}),textEditable);
  register('format.italic',()=>format('Italic',o=>{o.italic=!o.italic;eachRun(o,r=>r.italic=o.italic)}),textEditable);
  register('format.alignment',value=>format('Alignment',o=>{o.align=value;for(const p of o.paragraphs||[])p.align=o.align}),textEditable);
  register('navigation.to',navigateTo,()=>session.active);
  register('navigation.previous',()=>execute('navigation.to',session.currentIndex-1),()=>session.active&&session.currentIndex>0);
  register('navigation.next',()=>execute('navigation.to',session.currentIndex+1),()=>session.active&&session.currentIndex<session.slides.length-1);
 }
 function bindClick(id,command,...args){const node=$(id);if(node){node.dataset.command=command;node.onclick=()=>execute(command,...args)}return node}
 function installShareAction(){const saveBtn=$('saveMenuBtn');if(!saveBtn||$('shareMenuBtn'))return;const share=document.createElement('button');share.id='shareMenuBtn';share.className='menu-item';share.type='button';share.disabled=true;share.dataset.command='file.share';share.innerHTML='<svg viewBox="0 0 24 24"><path d="M12 15V3"/><path d="m8 7 4-4 4 4"/><path d="M5 11v8a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-8"/></svg><span>Share</span><span class="hint">PPTX</span>';saveBtn.insertAdjacentElement('afterend',share);share.onclick=async()=>{drawer.close({restoreFocus:false});await execute('file.share');sync()}}
 function legacyNotice(){let note=$('legacyPptNotice');if(!note){note=document.createElement('div');note.id='legacyPptNotice';note.hidden=true;note.setAttribute('role','status');note.style.cssText='display:flex;align-items:center;justify-content:center;gap:12px;padding:8px 12px;background:#fff3cd;color:#3d3300;border-bottom:1px solid #e5c76a;font:600 13px/1.35 system-ui,-apple-system,sans-serif;position:relative;z-index:24';const text=document.createElement('span');text.textContent='Legacy PowerPoint (.ppt) opened read-only. Save an editable .pptx copy to edit in InkDOS.';const button=document.createElement('button');button.type='button';button.textContent='Save editable PPTX copy';button.style.cssText='border:1px solid currentColor;border-radius:7px;background:transparent;color:inherit;padding:5px 9px;font:inherit;cursor:pointer';button.onclick=()=>execute('file.save');note.append(text,button);const anchor=$('editbar')||document.querySelector('.topbar');if(anchor)anchor.insertAdjacentElement('afterend',note);else document.body.prepend(note)}return note}
 function sync(){
  chrome.title();chrome.stats();
  const active=session.active,legacy=session.sourceKind==='ppt',canExport=isEnabled('file.save');
  const saveBtn=$('saveMenuBtn');if(saveBtn){saveBtn.disabled=!canExport;saveBtn.title=!active?'Create or open a presentation first.':legacy?'Save an editable PPTX copy':'Save PPTX copy'}
  const share=$('shareMenuBtn');if(share){share.disabled=!isEnabled('file.share');share.title=!active?'Create or open a presentation first.':legacy?'Share an editable PPTX copy':'Share PPTX'}
  const notice=legacyNotice();notice.hidden=!(active&&legacy);
  const title=$('titleText');if(title)title.readOnly=!isEnabled('file.rename');
  const present=$('presentBtn');if(present)present.disabled=!isEnabled('presentation.present.current');const presentStart=$('presentStartMenuBtn');if(presentStart)presentStart.disabled=!isEnabled('presentation.present.start');
  editor.sync()
 }
 function install(){
  drawer=NS.FrameUI.bindDrawer({trigger:$('menuBtn'),drawer:$('generalMenu'),backdrop:$('menuBackdrop'),closeButton:$('closeMenuBtn')});zoomPopover=NS.FrameUI.bindPopover({trigger:$('zoomMenuBtn'),popover:$('zoomPopover')});
  installShareAction();
  const newBtn=bindClick('newMenuBtn','file.new');if(newBtn)newBtn.onclick=()=>{const accepted=execute('file.new');if(accepted!==false)drawer.close()};
  const openBtn=bindClick('openMenuBtn','file.open');if(openBtn)openBtn.onclick=()=>{drawer.close({restoreFocus:false});execute('file.open')};
  const saveBtn=bindClick('saveMenuBtn','file.save');if(saveBtn)saveBtn.onclick=async()=>{drawer.close({restoreFocus:false});await execute('file.save');sync()};
  document.querySelectorAll('[data-appearance-choice]').forEach(b=>{b.dataset.command='appearance.set';b.onclick=()=>execute('appearance.set',b.dataset.appearanceChoice)});
  const title=$('titleText');if(title)title.addEventListener('change',e=>{if(!isEnabled('file.rename')){chrome.title();return}execute('file.rename',e.target.value)});
  bindClick('presentBtn','presentation.present.current');const presentStart=bindClick('presentStartMenuBtn','presentation.present.start');if(presentStart)presentStart.onclick=()=>{drawer.close({restoreFocus:false});execute('presentation.present.start')};
  document.addEventListener('keydown',e=>{const mod=e.metaKey||e.ctrlKey;if(!mod)return;const k=e.key.toLowerCase();if(k==='o'){e.preventDefault();execute('file.open')}else if(k==='n'){e.preventDefault();execute('file.new')}else if(k==='s'){e.preventDefault();execute('file.save')}else if(k==='z'&&!e.shiftKey&&!e.target.isContentEditable){e.preventDefault();execute('history.undo')}else if((k==='y'||(k==='z'&&e.shiftKey))&&!e.target.isContentEditable){e.preventDefault();execute('history.redo')}});
  sync()
 }
 installCommands();
 return Object.freeze({install,sync,refresh,requestNew:()=>execute('file.new'),register,execute,isEnabled,has:id=>registry.has(id),list:()=>[...registry.keys()],get drawer(){return drawer},get zoomPopover(){return zoomPopover}})
}
NS.CommandController=Object.freeze({create});})(globalThis);

(function(global){'use strict';
if(global.InkDOS2Presentations?.PptP2TableToolsUi||document.querySelector('script[data-ppt-p2-table-tools-ui]'))return;
const source=document.currentScript?.src;
const script=document.createElement('script');script.src=source?new URL('ppt-p2-table-tools-ui.js',source).href:'ui/ppt-p2-table-tools-ui.js';script.async=false;script.dataset.pptP2TableToolsUi='true';script.onerror=()=>console.error(new Error('PPT-P2 table tools UI could not be loaded locally.'));(document.head||document.documentElement).appendChild(script);
})(globalThis);
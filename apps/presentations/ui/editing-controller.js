(function(global){'use strict';const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,history,selection,surface,panel,zoom,chrome,onStructureChange}={}){
 const $=id=>document.getElementById(id);let commands=null;
 function selected(){return selection.getObject(session)}
 function setDisabled(id,value){const node=$(id);if(node)node.disabled=!!value}
 function setTitle(id,value){const node=$(id);if(node)node.title=value}
 function sync(){
  const active=session.active,o=selected(),textEditable=active&&session.sourceKind!=='ppt',has=!!o&&o.type==='text'&&textEditable,structure=active&&session.sourceKind!=='ppt';
  setDisabled('undoBtn',commands?!commands.isEnabled('history.undo'):!history.canUndo);setDisabled('redoBtn',commands?!commands.isEnabled('history.redo'):!history.canRedo);
  ['fontSize','boldBtn','italicBtn','alignSelect'].forEach(id=>setDisabled(id,commands?!commands.isEnabled(id==='fontSize'?'format.fontSize':id==='boldBtn'?'format.bold':id==='italicBtn'?'format.italic':'format.alignment'):!has));
  setDisabled('slidePanelBtn',commands?!commands.isEnabled('panel.toggle'):!active);setDisabled('prevSlideBtn',commands?!commands.isEnabled('navigation.previous'):!active||session.currentIndex<=0);setDisabled('nextSlideBtn',commands?!commands.isEnabled('navigation.next'):!active||session.currentIndex>=session.slides.length-1);
  setDisabled('addSlideBtn',commands?!commands.isEnabled('slide.add'):!structure);setDisabled('duplicateSlideBtn',commands?!commands.isEnabled('slide.duplicate'):!structure);setDisabled('deleteSlideBtn',commands?!commands.isEnabled('slide.delete'):!structure||session.slides.length<=1);setDisabled('insertTextBtn',commands?!commands.isEnabled('edit.insertText'):!textEditable);
  setDisabled('moveSlideUpBtn',commands?!commands.isEnabled('slide.move')||session.currentIndex<=0:!structure||session.currentIndex<=0);setDisabled('moveSlideDownBtn',commands?!commands.isEnabled('slide.move')||session.currentIndex>=session.slides.length-1:!structure||session.currentIndex>=session.slides.length-1);
  setTitle('addSlideBtn',structure?'New slide':active?'Legacy PPT is read-only':'Create or open a presentation first');setTitle('duplicateSlideBtn',structure?'Duplicate slide':active?'Legacy PPT is read-only':'Create or open a presentation first');setTitle('deleteSlideBtn',structure?'Delete slide':active?'Legacy PPT is read-only':'Create or open a presentation first');setTitle('insertTextBtn',textEditable?'Insert text box':active?'Legacy PPT is read-only':'Create or open a presentation first');
  if(has){const size=$('fontSize'),bold=$('boldBtn'),italic=$('italicBtn'),align=$('alignSelect');if(size)size.value=String(Math.round(o.fontSizePt||24));if(bold)bold.classList.toggle('active',!!o.bold);if(italic)italic.classList.toggle('active',!!o.italic);if(align)align.value=o.align||'left'}
  chrome.title();chrome.stats()
 }
 function rerender({thumbs=false,center=false}={}){surface.render();panel.syncActive({ensureActive:false});if(thumbs)panel.render({ensureActive:false});zoom.apply({preserveFocus:!center});if(center&&session.active)zoom.recenter();sync();chrome.stats()}
 function bindClick(id,command,...args){const node=$(id);if(node){node.dataset.command=command;node.onclick=()=>commands.execute(command,...args)}return node}
 function insertReorderControls(){if($('moveSlideUpBtn'))return;const anchor=$('deleteSlideBtn');if(!anchor)return;const make=(id,title,path,delta)=>{const b=document.createElement('button');b.id=id;b.className='tool-btn icon-only';b.type='button';b.title=title;b.setAttribute('aria-label',title);b.dataset.command='slide.move';b.innerHTML=`<svg viewBox="0 0 24 24"><path d="${path}"/></svg>`;b.onclick=()=>commands.execute('slide.move',delta);return b};const up=make('moveSlideUpBtn','Move slide earlier','m8 15 4-4 4 4M12 11V4M5 20h14',-1),down=make('moveSlideDownBtn','Move slide later','m8 9 4 4 4-4M12 13v7M5 4h14',1);anchor.insertAdjacentElement('afterend',down);anchor.insertAdjacentElement('afterend',up)}
 function install(commandRegistry){
  if(!commandRegistry||typeof commandRegistry.execute!=='function'||typeof commandRegistry.isEnabled!=='function')throw new TypeError('Presentations command registry is required');commands=commandRegistry;
  insertReorderControls();selection.onChange=()=>sync();
  bindClick('undoBtn','history.undo');bindClick('redoBtn','history.redo');bindClick('slidePanelBtn','panel.toggle');bindClick('addSlideBtn','slide.add');bindClick('duplicateSlideBtn','slide.duplicate');bindClick('deleteSlideBtn','slide.delete');bindClick('insertTextBtn','edit.insertText');bindClick('boldBtn','format.bold');bindClick('italicBtn','format.italic');bindClick('prevSlideBtn','navigation.previous');bindClick('nextSlideBtn','navigation.next');
  const font=$('fontSize');if(font){font.dataset.command='format.fontSize';font.onchange=e=>commands.execute('format.fontSize',e.target.value)}const align=$('alignSelect');if(align){align.dataset.command='format.alignment';align.onchange=e=>commands.execute('format.alignment',e.target.value)}
  sync()
 }
 return Object.freeze({install,sync,rerender,moveSlide:delta=>commands?.execute('slide.move',delta)})
}
NS.EditingController=Object.freeze({create});})(globalThis);

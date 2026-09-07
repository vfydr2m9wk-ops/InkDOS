(function(global){'use strict';const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({session,history,selection,surface,panel,zoom,chrome,onStructureChange}={}){
 const $=id=>document.getElementById(id);
 function selected(){return selection.getObject(session)}
 function sync(){
  const active=session.active,o=selected(),textEditable=active&&session.sourceKind!=='ppt',has=!!o&&o.type==='text'&&textEditable,structureEditable=active&&session.sourceKind==='new';
  $('undoBtn').disabled=!history.canUndo;$('redoBtn').disabled=!history.canRedo;
  ['fontSize','boldBtn','italicBtn','alignSelect'].forEach(id=>{if($(id))$(id).disabled=!has});
  $('slidePanelBtn').disabled=!active;$('prevSlideBtn').disabled=!active||session.currentIndex<=0;$('nextSlideBtn').disabled=!active||session.currentIndex>=session.slides.length-1;
  $('addSlideBtn').disabled=!structureEditable;$('duplicateSlideBtn').disabled=!structureEditable;$('deleteSlideBtn').disabled=!structureEditable||session.slides.length<=1;$('insertTextBtn').disabled=!textEditable;
  $('addSlideBtn').title=structureEditable?'New slide':active?'Available for new presentations':'Create or open a presentation first';
  $('duplicateSlideBtn').title=structureEditable?'Duplicate slide':active?'Available for new presentations':'Create or open a presentation first';
  $('deleteSlideBtn').title=structureEditable?'Delete slide':active?'Available for new presentations':'Create or open a presentation first';
  $('insertTextBtn').title=textEditable?'Insert text box':active?'Legacy PPT is read-only':'Create or open a presentation first';
  if(has){$('fontSize').value=String(Math.round(o.fontSizePt||24));$('boldBtn').classList.toggle('active',!!o.bold);$('italicBtn').classList.toggle('active',!!o.italic);$('alignSelect').value=o.align||'left'}
  chrome.title();chrome.stats()
 }
 function rerender({thumbs=false,center=false}={}){surface.render();panel.syncActive({ensureActive:false});if(thumbs)panel.render({ensureActive:false});zoom.apply({preserveFocus:!center});if(center&&session.active)zoom.recenter();sync();chrome.stats()}
 function eachRun(o,fn){for(const p of o.paragraphs||[])for(const r of p.runs||[])fn(r,p)}
 function format(label,mutator){if(!session.active||session.sourceKind==='ppt')return;const o=selected();if(!o||o.type!=='text')return;history.transact(label,()=>mutator(o));rerender({thumbs:true})}
 function install(){
  selection.onChange=()=>sync();
  $('undoBtn').onclick=()=>{if(history.undo()){selection.clear();rerender({thumbs:true})}};
  $('redoBtn').onclick=()=>{if(history.redo()){selection.clear();rerender({thumbs:true})}};
  $('slidePanelBtn').onclick=()=>{if(session.active)panel.toggle()};
  $('addSlideBtn').onclick=()=>{if(!session.active||session.sourceKind!=='new')return;history.transact('Add slide',()=>session.addSlide());selection.clear();onStructureChange?.();rerender({thumbs:true,center:true})};
  $('duplicateSlideBtn').onclick=()=>{if(!session.active||session.sourceKind!=='new')return;history.transact('Duplicate slide',()=>session.duplicateCurrent());selection.clear();onStructureChange?.();rerender({thumbs:true,center:true})};
  $('deleteSlideBtn').onclick=()=>{if(!session.active||session.sourceKind!=='new'||session.slides.length<=1)return;history.transact('Delete slide',()=>session.deleteCurrent());selection.clear();onStructureChange?.();rerender({thumbs:true,center:true})};
  $('insertTextBtn').onclick=()=>{if(!session.active||session.sourceKind==='ppt')return;let obj=null;history.transact('Insert text',()=>{obj=session.addText()});selection.select(obj?.id);rerender({thumbs:true})};
  $('fontSize').onchange=e=>format('Font size',o=>{const v=Math.max(8,Math.min(96,Number(e.target.value)||24));o.fontSizePt=v;eachRun(o,r=>r.fontSizePt=v)});
  $('boldBtn').onclick=()=>format('Bold',o=>{o.bold=!o.bold;eachRun(o,r=>r.bold=o.bold)});
  $('italicBtn').onclick=()=>format('Italic',o=>{o.italic=!o.italic;eachRun(o,r=>r.italic=o.italic)});
  $('alignSelect').onchange=e=>format('Alignment',o=>{o.align=e.target.value;for(const p of o.paragraphs||[])p.align=o.align});
  $('prevSlideBtn').onclick=()=>{if(!session.active)return;session.setCurrentByIndex(session.currentIndex-1);selection.clear();rerender({center:true});panel.syncActive()};
  $('nextSlideBtn').onclick=()=>{if(!session.active)return;session.setCurrentByIndex(session.currentIndex+1);selection.clear();rerender({center:true});panel.syncActive()};
  sync()
 }
 return Object.freeze({install,sync,rerender})
}
NS.EditingController=Object.freeze({create});})(globalThis);

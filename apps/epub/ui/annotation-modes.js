(function(g){'use strict';
const NS=g.InkDOS2Epub=g.InkDOS2Epub||{};
const MODES=new Set(['none','highlight','note','delete']);
function create({reader,session,elements}={}){
 if(!reader||!session||!elements)throw new Error('AnnotationModes requires reader, session and elements');
 let mode='none',color='yellow',selectionTimer=0,pendingNote=null;
 const makeTool=(id,label,path)=>{const b=document.createElement('button');b.id=id;b.className='tool-btn';b.type='button';b.setAttribute('aria-label',label);b.setAttribute('aria-pressed','false');b.title=label;b.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"/></svg>`;return b};
 const noteBtn=makeTool('noteModeBtn','Note mode','M5 5h14v11H9l-4 4z M8 9h8 M8 12h5'),deleteBtn=makeTool('deleteAnnotationModeBtn','Delete annotation mode','M5 7h14 M9 7V4h6v3 M8 10v8 M12 10v8 M16 10v8 M7 7l1 13h8l1-13');
 elements.highlightBtn.after(noteBtn,deleteBtn);elements.highlightBtn.setAttribute('aria-label','Highlight mode');elements.highlightBtn.title='Highlight mode';elements.highlightBtn.dataset.highlightColor=color;
 const backdrop=document.createElement('div');backdrop.className='epub-note-backdrop';backdrop.hidden=true;backdrop.innerHTML='<form class="epub-note-dialog" role="dialog" aria-modal="true" aria-labelledby="epubNoteTitle"><h2 id="epubNoteTitle">Add note</h2><p class="epub-note-quote"></p><textarea maxlength="4000" aria-label="Note text" placeholder="Write a note…"></textarea><div class="epub-note-actions"><button type="button" data-note-cancel>Cancel</button><button type="submit" class="primary">Save note</button></div></form>';document.body.append(backdrop);
 const form=backdrop.querySelector('form'),textarea=backdrop.querySelector('textarea'),quote=backdrop.querySelector('.epub-note-quote'),cancel=backdrop.querySelector('[data-note-cancel]');
 function syncMode(){for(const [button,name] of [[elements.highlightBtn,'highlight'],[noteBtn,'note'],[deleteBtn,'delete']]){const active=mode===name;button.classList.toggle('annotation-active',active);button.setAttribute('aria-pressed',String(active))}elements.highlightBtn.dataset.highlightColor=color;for(const button of document.querySelectorAll('[data-highlight-color]'))button.setAttribute('aria-pressed',String(button.dataset.highlightColor===color))}
 function setMode(next){mode=MODES.has(next)?next:'none';syncMode();return mode}
 function selectionInsideReader(){const sel=g.getSelection?.();if(!sel||sel.isCollapsed||!sel.anchorNode)return false;const node=sel.anchorNode.nodeType===1?sel.anchorNode:sel.anchorNode.parentElement;return !!node&&elements.surface.contains(node)}
 function noteInput(){const s=reader.state(),first=s.selection&&s.selection[0];if(!first||!s.book)return null;for(let i=0;i<s.book.chapters.length;i++){const chapter=s.book.chapters[i],block=chapter.blocks.find(b=>b.id===first.anchor);if(block)return {anchor:first.anchor,start:first.start,end:first.end,chapter:i+1,path:chapter.path,fragment:block.sourceId||'',source:'passage',quote:String(s.selectionQuote||'').slice(0,600)}}return null}
 function overlaps(segment,item){return item&&segment&&item.anchor===segment.anchor&&Number(item.end)>Number(segment.start)&&Number(item.start)<Number(segment.end)}
 function openNote(input){if(!input)return;pendingNote=input;quote.textContent=input.quote||'Selected passage';textarea.value='';backdrop.hidden=false;setTimeout(()=>textarea.focus(),0)}
 function closeNote(){pendingNote=null;backdrop.hidden=true;textarea.value=''}
 function clearBrowserSelection(){try{g.getSelection?.()?.removeAllRanges?.()}catch(_){}}
 function hasPendingNoteDraft(){return !!(pendingNote&&!backdrop.hidden&&String(textarea.value||'').trim())}
 function discardPendingNote(){if(!pendingNote&&backdrop.hidden)return false;closeNote();clearBrowserSelection();return true}
 function commitPendingNote(){const text=String(textarea.value||'').trim(),input=pendingNote;if(!input||backdrop.hidden||!text)return false;const note=session.addNote({...input,text});if(!note){reader.notice('Could not add this note.');return false}closeNote();clearBrowserSelection();session.persist();reader.prepareExport();reader.notice('Note added · preparing edited copy',1800);return true}
 function deleteSelectedAnnotations(){const before=reader.state(),segments=Array.from(before.selection||[]);if(!segments.length)return false;const noteIds=(before.notes||[]).filter(n=>segments.some(s=>overlaps(s,n))).map(n=>n.id),hasHighlight=(before.annotations||[]).some(h=>(h.segments||[]).some(hs=>segments.some(s=>overlaps(s,hs))));for(const id of noteIds)session.removeNote(id);if(hasHighlight){reader.removeHighlight()}else{session.setSelection(null);clearBrowserSelection();if(noteIds.length){reader.prepareExport();reader.notice(noteIds.length===1?'Annotation deleted · preparing edited copy':'Annotations deleted · preparing edited copy',1800)}else reader.notice('No saved annotation overlaps this selection.')}if(noteIds.length)session.persist();return hasHighlight||noteIds.length>0}
 function install(){
  elements.highlightBtn.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();setMode('highlight');elements.appearance.hidden=true;elements.toc.hidden=true;elements.highlight.hidden=false},true);
  for(const button of document.querySelectorAll('[data-highlight-color]'))button.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();color=button.dataset.highlightColor||'yellow';setMode('highlight');elements.highlight.hidden=true;reader.notice('Highlight mode armed',900)},true);
  noteBtn.addEventListener('click',()=>{setMode(mode==='note'?'none':'note');elements.highlight.hidden=true;reader.notice(mode==='note'?'Note mode armed':'Annotation mode off',900)});
  deleteBtn.addEventListener('click',()=>{setMode(mode==='delete'?'none':'delete');elements.highlight.hidden=true;reader.notice(mode==='delete'?'Delete annotation mode armed':'Annotation mode off',900)});
  cancel.addEventListener('click',()=>discardPendingNote());backdrop.addEventListener('click',event=>{if(event.target===backdrop)discardPendingNote()});
  form.addEventListener('submit',event=>{event.preventDefault();if(!pendingNote){closeNote();return}if(!String(textarea.value||'').trim()){reader.notice('Note was not added.');return}commitPendingNote()});
  document.addEventListener('selectionchange',()=>{clearTimeout(selectionTimer);if(mode==='none'||!backdrop.hidden||!selectionInsideReader())return;selectionTimer=setTimeout(()=>{if(mode==='none'||!backdrop.hidden||!selectionInsideReader()||!reader.captureSelection())return;if(mode==='highlight')reader.applyHighlight(color);else if(mode==='note')openNote(noteInput());else if(mode==='delete')deleteSelectedAnnotations()},90)});
  document.addEventListener('inkdos:epub-opened',()=>{closeNote();setMode('none')});syncMode();
 }
 function finalizeLegacySelectionUi(){document.querySelector('.epub-selection-actions')?.remove()}
 return Object.freeze({install,finalizeLegacySelectionUi,hasPendingNoteDraft,commitPendingNote,discardPendingNote,state:()=>Object.freeze({mode,color,noteOpen:!backdrop.hidden,noteDraftDirty:hasPendingNoteDraft()})});
}
NS.AnnotationModes=Object.freeze({create});
})(globalThis);

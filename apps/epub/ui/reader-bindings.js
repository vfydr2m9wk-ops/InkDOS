(function(g){'use strict';
const NS=g.InkDOS2Epub=g.InkDOS2Epub||{};
function create({elements:E,reader,navigation,annotationModes}={}){
 if(!E||!reader||!navigation)throw new Error('ReaderBindings requires elements, reader and navigation');
 let ro=null,touchStart=null,selectionTools=null,unsavedDialog=null;
 function closeSheets(except){for(const p of [E.appearance,E.highlight,E.toc])if(p!==except)p.hidden=true}
 function toggleSheet(panel){const opening=panel.hidden;closeSheets(opening?panel:null);panel.hidden=!opening}
 function state(){return reader.state()}
 function dirty(){const current=state();return !!(current.book&&(current.annotationDirty||annotationModes?.hasPendingNoteDraft()))}
 function closeUnsavedDialog(choice){if(!unsavedDialog)return;const {node,resolve}=unsavedDialog;unsavedDialog=null;node.remove();resolve(choice)}
 function decideUnsaved(message){
  if(!dirty())return Promise.resolve('discard');
  if(unsavedDialog)return Promise.resolve('cancel');
  return new Promise(resolve=>{
   const node=document.createElement('div');node.id='epubUnsavedDialog';node.setAttribute('role','dialog');node.setAttribute('aria-modal','true');node.setAttribute('aria-label','Unsaved changes');node.style.cssText='position:fixed;inset:0;z-index:1000;display:grid;place-items:center;padding:20px;background:rgba(0,0,0,.42)';
   const card=document.createElement('div');card.style.cssText='width:min(420px,100%);border:1px solid rgba(127,127,127,.35);border-radius:14px;padding:18px;background:Canvas;color:CanvasText;box-shadow:0 20px 60px rgba(0,0,0,.3);font:14px/1.45 system-ui,-apple-system,sans-serif';
   const title=document.createElement('h2');title.textContent='Unsaved changes';title.style.margin='0 0 8px';
   const text=document.createElement('p');text.textContent=String(message||'Save your edited EPUB copy before continuing?');text.style.margin='0 0 16px';
   const actions=document.createElement('div');actions.style.cssText='display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap';
   for(const [choice,label] of [['cancel','Cancel'],['discard','Discard'],['save','Save']]){const button=document.createElement('button');button.type='button';button.dataset.choice=choice;button.textContent=label;button.style.cssText='min-height:38px;padding:7px 12px;border-radius:9px;border:1px solid rgba(127,127,127,.45);background:ButtonFace;color:ButtonText';button.onclick=()=>closeUnsavedDialog(choice);actions.append(button)}
   card.append(title,text,actions);node.append(card);unsavedDialog={node,resolve};document.body.append(node);actions.querySelector('[data-choice="cancel"]')?.focus();
  })
 }
 async function saveForReplacement(){
  const before=state();if(!before.book)return true;
  if(annotationModes?.hasPendingNoteDraft()&&!annotationModes?.commitPendingNote())return false;
  const ready=state();if(!ready.annotationDirty)return true;
  const revision=ready.annotationRevision,ok=await reader.saveCopy();if(!ok)return false;
  const after=state();if(after.annotationRevision!==revision){reader.notice('Book changed while saving — navigation cancelled',4000);return false}
  return true
 }
 async function authorizeReplacement(kind){
  if(!dirty())return true;
  const messages={open:'Save your edited EPUB copy before opening another book?',leave:'Save your edited EPUB copy before leaving EPUB Reader?'};
  const decision=await decideUnsaved(messages[kind]||messages.leave);
  if(decision==='discard'){annotationModes?.discardPendingNote();return true}
  if(decision==='cancel')return false;
  if(decision==='save')return await saveForReplacement();
  return false
 }
 async function requestOpen(){if(!(await authorizeReplacement('open')))return false;E.file.click();return true}
 function ensureSelectionTools(){if(selectionTools)return selectionTools;const bar=document.createElement('div');bar.className='epub-selection-actions';bar.hidden=true;bar.setAttribute('role','toolbar');bar.setAttribute('aria-label','Selected text actions');const hi=document.createElement('button');hi.type='button';hi.textContent='Highlight';hi.setAttribute('aria-label','Highlight selected text');const note=document.createElement('button');note.type='button';note.textContent='Note';note.setAttribute('aria-label','Add note to selected text');for(const b of[hi,note])b.addEventListener('pointerdown',e=>e.preventDefault());hi.addEventListener('pointerdown',e=>{e.stopPropagation();reader.openHighlightForSelection();bar.hidden=true});note.addEventListener('pointerdown',e=>{e.stopPropagation();reader.addNoteFromSelection();bar.hidden=true});bar.append(hi,note);document.body.appendChild(bar);selectionTools=bar;return bar}
 function syncSelectionTools(active){const bar=ensureSelectionTools();if(!active){bar.hidden=true;return}const sel=g.getSelection?.();if(!sel||!sel.rangeCount){bar.hidden=true;return}const rect=sel.getRangeAt(0).getBoundingClientRect();if(!rect||(!rect.width&&!rect.height)){bar.hidden=true;return}bar.hidden=false;bar.style.left=Math.max(76,Math.min(g.innerWidth-76,rect.left+rect.width/2))+'px';bar.style.top=Math.max(8,rect.top-10)+'px'}
 function install(){
  ensureSelectionTools();
  E.open.addEventListener('click',()=>requestOpen());
  E.openStart.addEventListener('click',()=>requestOpen());
  E.file.addEventListener('change',()=>{const file=E.file.files&&E.file.files[0];if(file)reader.openFile(file)});
  E.save.addEventListener('click',()=>saveForReplacement());
  E.share.addEventListener('click',()=>reader.shareCopy());
  E.tocBtn.addEventListener('click',()=>{const opened=reader.toggleNavigationSheet();if(opened)navigation.showTab('contents')});
  E.tocClose.addEventListener('click',()=>reader.closeNavigationSheet());
  if(E.bookmarkBtn)E.bookmarkBtn.addEventListener('click',()=>navigation.toggleBookmark());
  if(E.searchBtn)E.searchBtn.addEventListener('click',()=>navigation.openNavigation('search'));
  E.tocList.addEventListener('click',event=>{const button=event.target.closest&&event.target.closest('[data-epub-toc-index]');if(button)reader.openTocEntry(button.dataset.epubTocIndex)});
  E.appearanceBtn.addEventListener('click',()=>toggleSheet(E.appearance));
  E.appearanceClose.addEventListener('click',()=>E.appearance.hidden=true);
  E.highlightBtn.addEventListener('pointerdown',()=>reader.captureSelection());
  E.highlightBtn.addEventListener('click',()=>toggleSheet(E.highlight));
  E.highlightClose.addEventListener('click',()=>E.highlight.hidden=true);
  E.highlightClear.addEventListener('click',()=>reader.removeHighlight());
  for(const button of document.querySelectorAll('[data-highlight-color]'))button.addEventListener('click',()=>reader.applyHighlight(button.dataset.highlightColor));
  E.pagesBtn.addEventListener('click',()=>reader.setFlow('pages'));
  E.scrollBtn.addEventListener('click',()=>reader.setFlow('scroll'));
  E.prev.addEventListener('click',()=>reader.goPage(state().pageIndex-1));
  E.next.addEventListener('click',()=>reader.goPage(state().pageIndex+1));
  E.progress.addEventListener('input',()=>reader.goPage(Number(E.progress.value)-1,'auto'));
  E.fontRange.addEventListener('input',()=>reader.setFont(E.fontRange.value));
  E.fontValue.addEventListener('change',()=>reader.setFont(E.fontValue.value));
  E.fontValue.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();reader.setFont(E.fontValue.value);E.fontValue.blur()}});
  E.fontDown.addEventListener('click',()=>reader.setFont(state().fontPx-1));
  E.fontUp.addEventListener('click',()=>reader.setFont(state().fontPx+1));
  E.fontFamily.addEventListener('change',()=>reader.setFontStyle(E.fontFamily.value));
  for(const button of document.querySelectorAll('[data-theme-choice]'))button.addEventListener('click',()=>reader.setTheme(button.dataset.themeChoice));
  document.addEventListener('selectionchange',()=>syncSelectionTools(reader.captureSelection()));
  E.surface.addEventListener('click',event=>{const link=event.target.closest&&event.target.closest('.reader-link');if(link){event.preventDefault();reader.handleReaderLink(link)}});
  E.surface.addEventListener('keydown',event=>{const link=event.target.closest&&event.target.closest('.reader-link');if(link&&(event.key==='Enter'||event.key===' ')){event.preventDefault();reader.handleReaderLink(link)}});
  E.viewport.addEventListener('scroll',()=>{if(selectionTools)selectionTools.hidden=true;reader.viewportScrolled()},{passive:true});
  E.viewport.addEventListener('touchstart',event=>{const current=state();if(current.flow!=='pages'||event.touches.length!==1)return;touchStart={x:event.touches[0].clientX,y:event.touches[0].clientY}},{passive:true});
  E.viewport.addEventListener('touchend',event=>{const current=state();if(!touchStart||current.flow!=='pages'||!event.changedTouches.length)return;const dx=event.changedTouches[0].clientX-touchStart.x,dy=event.changedTouches[0].clientY-touchStart.y;touchStart=null;if(Math.abs(dx)>48&&Math.abs(dx)>Math.abs(dy)*1.35)reader.goPage(current.pageIndex+(dx<0?1:-1))},{passive:true});
  document.addEventListener('keydown',event=>{if(event.target&&event.target.closest&&event.target.closest('.reader-link'))return;const current=state();if(event.key==='ArrowRight'&&current.flow==='pages'){reader.goPage(current.pageIndex+1);event.preventDefault()}else if(event.key==='ArrowLeft'&&current.flow==='pages'){reader.goPage(current.pageIndex-1);event.preventDefault()}});
  const home=document.querySelector('a[aria-label="Home"]');if(home)home.addEventListener('click',async event=>{if(!dirty())return;event.preventDefault();event.stopPropagation();const href=home.href;if(await authorizeReplacement('leave'))g.location.assign(href)});
  g.addEventListener('beforeunload',event=>{if(!dirty())return;event.preventDefault();event.returnValue=''});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)reader.persistCurrentPosition()});
  addEventListener('pagehide',()=>reader.persistCurrentPosition());
  ro=new ResizeObserver(()=>reader.viewportResized());ro.observe(E.viewport);reader.initialize();
 }
 return Object.freeze({install,requestOpen,authorizeReplacement,saveForReplacement});
}
NS.ReaderBindings=Object.freeze({create});
})(globalThis);

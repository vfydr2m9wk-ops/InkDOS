(function(g){'use strict';
const NS=g.InkDOS2Epub=g.InkDOS2Epub||{},S=NS.AnnotationStore;
function plainAnnotations(v){return Array.from(v||[],h=>({id:h.id,color:h.color,segments:Array.from(h.segments||[],s=>({anchor:s.anchor,start:s.start,end:s.end}))}))}
function locatorExists(book,loc){return !!(book&&loc&&loc.anchor&&book.chapters.some(c=>c.blocks.some(b=>b.id===loc.anchor)))}
function plainBookmarks(v,book){return Array.from(v||[]).slice(0,500).map(b=>({id:String(b.id||''),anchor:String(b.anchor||''),chapter:Number(b.chapter)||1,path:String(b.path||''),fragment:String(b.fragment||''),label:String(b.label||'Bookmark').slice(0,160),createdAt:String(b.createdAt||'')})).filter(b=>b.id&&locatorExists(book,b))}
function create(){
 const state={pkg:null,book:null,fileName:'EPUB Reader',flow:'pages',fontPx:18,fontStyle:'book',theme:'paper',metrics:null,epoch:0,locator:null,pageCount:1,pageIndex:0,operation:0,abort:null,bookKey:null,annotations:[],bookmarks:[],selection:null,annotationRevision:0,annotationDirty:false,exportBlob:null,exportReady:false,exportToken:0,preparing:false,notice:'',noticeTimer:null};
 async function loadCandidate(file){
  const operation=++state.operation;if(state.abort)state.abort.abort();const abort=new AbortController();state.abort=abort;
  const bytes=await file.arrayBuffer(),pkg=await NS.PackageReader.open(bytes,{signal:abort.signal}),book=await NS.BookModel.build(pkg,{signal:abort.signal});if(operation!==state.operation)return null;
  const embedded=await S.readEmbedded(pkg);if(operation!==state.operation)return null;
  const bookKey=await NS.ReadingState.key(pkg,book);if(operation!==state.operation)return null;
  const saved=await NS.ReadingState.load(bookKey);if(operation!==state.operation)return null;
  const flow=saved&&['pages','scroll'].includes(saved.flow)?saved.flow:'pages';
  const fontPx=saved?Math.max(4,Math.min(28,Number(saved.fontPx)||18)):18;
  const fontStyle=saved&&['book','classic','sans','humanist','system'].includes(saved.fontStyle)?saved.fontStyle:'book';
  const theme=saved&&['paper','sepia','sage','night'].includes(saved.theme)?saved.theme:'paper';
  const first=book.chapters[0]&&book.chapters[0].blocks[0]?{anchor:book.chapters[0].blocks[0].id,chapter:1,path:book.chapters[0].path,fragment:''}:null;
  const locator=saved&&locatorExists(book,saved.locator)?saved.locator:first,bookmarks=plainBookmarks(saved&&saved.bookmarks,book);
  return {operation,abort,pkg,book,fileName:file.name||book.title||'Book.epub',annotations:plainAnnotations(embedded.highlights),bookmarks,bookKey,saved,flow,fontPx,fontStyle,theme,locator,resumed:!!(saved&&locatorExists(book,saved.locator))};
 }
 function isCurrent(candidate){return !!candidate&&candidate.operation===state.operation&&candidate.abort===state.abort&&!candidate.abort.signal.aborted}
 function commit(candidate){if(!isCurrent(candidate))return false;Object.assign(state,{pkg:candidate.pkg,book:candidate.book,fileName:candidate.fileName,flow:candidate.flow,fontPx:candidate.fontPx,fontStyle:candidate.fontStyle,theme:candidate.theme,locator:candidate.locator,bookKey:candidate.bookKey,annotations:plainAnnotations(candidate.annotations),bookmarks:plainBookmarks(candidate.bookmarks,candidate.book),selection:null,annotationRevision:0,annotationDirty:false,exportBlob:new Blob([candidate.pkg.sourceBytes],{type:'application/epub+zip'}),exportReady:true,preparing:false});return true}
 function setSelection(selection){state.selection=selection||null;return state.selection}
 function addHighlight(color){if(!state.selection)return false;state.annotations=S.add(state.annotations,state.selection,color);state.annotationRevision++;state.annotationDirty=true;state.selection=null;return true}
 function removeHighlight(){if(!state.selection)return false;const before=state.annotations.length;state.annotations=S.removeOverlapping(state.annotations,state.selection);if(state.annotations.length===before)return false;state.annotationRevision++;state.annotationDirty=true;state.selection=null;return true}
 function toggleBookmark(locator,label){if(!locatorExists(state.book,locator))return null;const at=state.bookmarks.findIndex(b=>b.anchor===locator.anchor);if(at>=0){const removed=state.bookmarks.splice(at,1)[0];return {added:false,bookmark:removed}}const bookmark={id:'bm-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7),anchor:locator.anchor,chapter:Number(locator.chapter)||1,path:locator.path||'',fragment:locator.fragment||'',label:String(label||('Chapter '+(Number(locator.chapter)||1))).slice(0,160),createdAt:new Date().toISOString()};state.bookmarks.push(bookmark);return {added:true,bookmark}}
 function removeBookmark(id){const at=state.bookmarks.findIndex(b=>b.id===id);if(at<0)return false;state.bookmarks.splice(at,1);return true}
 function editedName(){const n=String(state.fileName||'Book.epub').replace(/\.epub$/i,'');if(!state.annotationDirty)return NS.EpubFileDelivery.safeName(state.fileName);return NS.EpubFileDelivery.safeName(n.replace(/-edited$/i,'')+'-edited.epub')}
 async function prepareExport(){
  const token=++state.exportToken;if(!state.book||!state.pkg){state.exportBlob=null;state.exportReady=false;state.preparing=false;return null}state.preparing=true;state.exportReady=false;
  try{let blob;if(!state.annotationDirty)blob=new Blob([state.pkg.sourceBytes],{type:'application/epub+zip'});else{blob=await NS.EpubWriter.build(state.pkg,state.annotations,{signal:state.abort&&state.abort.signal});const check=await NS.PackageReader.open(await blob.arrayBuffer(),{signal:state.abort&&state.abort.signal}),embedded=await S.readEmbedded(check);if(embedded.highlights.length!==state.annotations.length)throw new Error('Annotation verification mismatch')}
   if(token!==state.exportToken)return null;state.exportBlob=blob;state.exportReady=true;state.preparing=false;return blob;
  }catch(err){if(token===state.exportToken){state.exportBlob=null;state.exportReady=false;state.preparing=false}throw err}
 }
 function persist(){return state.bookKey&&state.locator?NS.ReadingState.save(state.bookKey,state):Promise.resolve(false)}
 return Object.freeze({state,loadCandidate,isCurrent,commit,setSelection,addHighlight,removeHighlight,toggleBookmark,removeBookmark,editedName,prepareExport,persist,plainAnnotations,plainBookmarks,locatorExists});
}
NS.BookSession=Object.freeze({create});
})(globalThis);

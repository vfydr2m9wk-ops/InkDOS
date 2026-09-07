(function(g){'use strict';
const NS=g.InkDOS2Epub=g.InkDOS2Epub||{},MAX_RESULTS=200;
function fold(v){return String(v||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase().replace(/\s+/g,' ').trim()}
function blockText(block){return (block&&block.runs||[]).filter(r=>r.kind==='text').map(r=>r.text||'').join(' ').replace(/\s+/g,' ').trim()}
function snippet(text,index,length){const radius=72,start=Math.max(0,index-radius),end=Math.min(text.length,index+length+radius);return (start?'…':'')+text.slice(start,end).trim()+(end<text.length?'…':'')}
function create(book){
 const entries=[];for(let ci=0;ci<(book?.chapters||[]).length;ci++){const chapter=book.chapters[ci];for(const block of chapter.blocks||[]){const text=blockText(block);if(!text)continue;entries.push(Object.freeze({chapter:ci+1,chapterTitle:chapter.title,path:chapter.path,anchor:block.id,fragment:block.sourceId||'',text,folded:fold(text)}))}}
 function search(query,limit=MAX_RESULTS){const q=fold(query);if(!q)return [];const out=[],cap=Math.max(1,Math.min(MAX_RESULTS,Number(limit)||MAX_RESULTS));for(const e of entries){const at=e.folded.indexOf(q);if(at<0)continue;out.push(Object.freeze({chapter:e.chapter,chapterTitle:e.chapterTitle,path:e.path,anchor:e.anchor,fragment:e.fragment,text:e.text,snippet:snippet(e.text,at,q.length)}));if(out.length>=cap)break}return out}
 return Object.freeze({search,size:entries.length});
}
NS.EpubNavigationIndex=Object.freeze({create,fold,blockText,MAX_RESULTS});
})(globalThis);

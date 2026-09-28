(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{},MAX_RESULTS=1000,MAX_INDEX_PAGES=2000;
function create({session,getDocument,layout,chrome,onChange,onStatus}={}){
 let query='',results=[],cursor=-1,searchToken=0,pageTexts=new Map(),printToken=0,printSheet=null;
 function inspect(){return Object.freeze({query,results:Object.freeze(results.map(r=>Object.freeze({...r}))),cursor})}
 function emit(){onChange?.(inspect())}
 function status(text){onStatus?.(String(text||''))}
 function resetDocument(){searchToken++;pageTexts.clear();query='';results=[];cursor=-1;emit();status('')}
 async function pageText(doc,n,token){if(pageTexts.has(n))return pageTexts.get(n);const p=await doc.getPage(n);if(token!==searchToken)throw new DOMException('Search cancelled','AbortError');const tc=await p.getTextContent({normalizeWhitespace:true});const text=(tc.items||[]).map(x=>x.str||'').join(' ').replace(/\s+/g,' ').trim();pageTexts.set(n,text);return text}
 function snippet(text,index,len){const a=Math.max(0,index-55),b=Math.min(text.length,index+len+85);return(a?'…':'')+text.slice(a,b)+(b<text.length?'…':'')}
 async function reveal(index){if(!results.length)return false;cursor=(Number(index)+results.length)%results.length;const r=results[cursor];await layout.goToPage(r.page,{smooth:true});emit();chrome.status(`Match ${cursor+1} of ${results.length} · page ${r.page}`);return true}
 async function search(value){const doc=getDocument?.(),q=String(value||'').trim();query=q;results=[];cursor=-1;emit();status('');if(!q||!doc)return false;const token=++searchToken,indexed=Math.min(doc.numPages,MAX_INDEX_PAGES),needle=q.toLocaleLowerCase();status('Searching…');try{for(let n=1;n<=indexed&&results.length<MAX_RESULTS;n++){const text=await pageText(doc,n,token),low=text.toLocaleLowerCase();let from=0;while(results.length<MAX_RESULTS){const i=low.indexOf(needle,from);if(i<0)break;results.push({page:n,index:i,snippet:snippet(text,i,q.length)});from=i+Math.max(1,needle.length)}if(token!==searchToken)return false;if(n%12===0){status(`Searching… ${n}/${indexed}`);await new Promise(r=>setTimeout(r,0))}}if(token!==searchToken)return false;cursor=results.length?0:-1;emit();status(results.length?`${results.length}${results.length>=MAX_RESULTS?'+':''} match${results.length===1?'':'es'}`:'No matches');if(results.length)await reveal(cursor);return true}catch(e){if(e?.name==='AbortError')return false;console.error(e);status('Search failed');chrome.status('PDF search failed');return false}}
 function step(delta){if(!results.length)return false;return reveal((cursor<0?0:cursor)+Number(delta||0))}
 async function rotate(delta=90){if(!session.active)return false;await layout.rotateView(delta);chrome.status(`View rotated ${layout.rotation}°`);return layout.rotation}
 async function print(){if(!session.active)return false;if(session.dirty&&!(await (chrome.confirm?chrome.confirm({title:'Print without annotations?',message:'Unsaved annotations are not included in browser printing. Print the opened PDF anyway?',confirmLabel:'Print'}):Promise.resolve(global.confirm('Unsaved annotations are not included in browser printing. Print the opened PDF anyway?')))))return false;if(!session.active)return false;const doc=getDocument?.();if(!doc?.numPages)return false;
  // Print from the document itself: render each page to an image in a print-only sheet. A framed blob PDF is
  // blocked by the page CSP (frame-src 'none') and prints only its first page on iPadOS.
  clearPrintSheet();const token=++printToken,sheet=document.createElement('div'),urls=[];sheet.id='pdfPrintSheet';sheet.setAttribute('aria-hidden','true');
  try{for(let n=1;n<=doc.numPages;n++){if(token!==printToken)return false;chrome.status(`Preparing print · page ${n} of ${doc.numPages}`);const page=await doc.getPage(n),base=page.getViewport({scale:1}),scale=Math.min(2,2200/Math.max(base.width,base.height)),vp=page.getViewport({scale}),canvas=document.createElement('canvas');canvas.width=Math.ceil(vp.width);canvas.height=Math.ceil(vp.height);const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);await page.render({canvasContext:ctx,viewport:vp}).promise;const blob=await new Promise(r=>canvas.toBlob(r,'image/jpeg',.92));canvas.width=canvas.height=0;if(!blob)throw new Error('Page image failed');const url=URL.createObjectURL(blob),img=document.createElement('img');urls.push(url);img.src=url;img.alt='';img.className=base.width>base.height?'landscape':'portrait';sheet.appendChild(img)}
   await Promise.all([...sheet.querySelectorAll('img')].map(img=>img.decode?img.decode().catch(()=>{}):null))}
  catch(e){for(const u of urls)URL.revokeObjectURL(u);console.error(e);chrome.status('Browser printing is unavailable');return false}
  if(token!==printToken){for(const u of urls)URL.revokeObjectURL(u);return false}
  printSheet={sheet,urls};document.body.appendChild(sheet);document.documentElement.classList.add('pdf-printing');chrome.status('Print dialog opened');
  global.addEventListener('afterprint',clearPrintSheet,{once:true});
  try{global.print()}catch(e){console.error(e);clearPrintSheet();chrome.status('Browser printing is unavailable');return false}
  return true}
 function clearPrintSheet(){if(!printSheet)return;for(const u of printSheet.urls)URL.revokeObjectURL(u);printSheet.sheet.remove();printSheet=null;document.documentElement.classList.remove('pdf-printing')}
 return Object.freeze({resetDocument,search,reveal,step,rotate,print,inspect,get results(){return results.slice()},get cursor(){return cursor}})
}
NS.ReaderRuntime=Object.freeze({create,MAX_RESULTS,MAX_INDEX_PAGES});
})(globalThis);

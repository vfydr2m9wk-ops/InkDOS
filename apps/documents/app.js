(function(){
'use strict';
const $=id=>document.getElementById(id);
const fileInput=$('fileInput'),viewport=$('viewport'),pagesHost=$('pagesHost'),welcome=$('welcome');
let currentFile=null,currentFileName='Untitled.docx',currentBuffer=null,sourceContext=null,zoom=1,pages=[],hits=[],activeHit=-1,observer=null,mediaUrls={},currentPageSpec=null;
let dirty=false,documentActive=false,history=[],historyIndex=-1,historyTimer=null,restoring=false,savedRange=null,currentPage=1,saveReadyUrl='',recovery=null;
function status(t){$('statusText').textContent=t}
function rangeInsideEditor(r){return !!(r&&pagesHost.contains(r.commonAncestorContainer))}
function rememberSelection(){const sel=getSelection();if(sel&&sel.rangeCount){const r=sel.getRangeAt(0);if(rangeInsideEditor(r))savedRange=r.cloneRange()}}
function restoreSelection(){if(!savedRange)return false;const sel=getSelection();try{sel.removeAllRanges();sel.addRange(savedRange.cloneRange());return true}catch(_){savedRange=null;return false}}
function selectedText(){const sel=getSelection();return sel&&sel.rangeCount&&rangeInsideEditor(sel.getRangeAt(0))?String(sel):''}
function countWords(text){const m=String(text||'').trim().match(/[\p{L}\p{N}]+(?:[’'\-][\p{L}\p{N}]+)*/gu);return m?m.length:0}
function updateStats(){const text=Array.from(pagesHost.querySelectorAll('.page-content')).map(x=>x.innerText).join('\n');const words=countWords(text),chars=text.length,selectedWords=countWords(selectedText());$('pageStatus').textContent='Page '+currentPage+' of '+Math.max(1,pages.length)+' · '+words+' words · '+chars+' characters'+(selectedWords?' · '+selectedWords+' selected':'')}

function displayedFileName(){return currentFileName||'Untitled.docx'}
function setTitleValue(name){$('titleText').value=name||'Untitled.docx';document.title=(name||'Untitled.docx')+(dirty?' •':'')+' — Documents'}
function normalizeDocxName(name){name=String(name||'').trim()||'Untitled.docx';return /\.docx$/i.test(name)?name:name+'.docx'}
function setDirty(v=true){dirty=v;$('dirtyDot').classList.toggle('visible',v);document.title=displayedFileName()+(v?' •':'')+' — Documents';if(v&&recovery)recovery.markDirty()}
function setLoading(text){let x=$('loadingOverlay');if(!x){x=document.createElement('div');x.id='loadingOverlay';x.className='loading';x.innerHTML='<div class="loading-card"></div>';document.body.appendChild(x)}x.querySelector('.loading-card').textContent=text;x.classList.remove('hidden')}
function clearLoading(){const x=$('loadingOverlay');if(x)x.classList.add('hidden')}
function revokeMediaUrls(urls){if(window.InkDeskRuntime)InkDeskRuntime.revokeObjectUrls(Object.values(urls||{}));else Object.values(urls||{}).forEach(u=>URL.revokeObjectURL(u))}
function revokeMedia(){revokeMediaUrls(mediaUrls);mediaUrls={}}
function showOpenError(error,file){
 const message=error&&error.message?error.message:String(error||'Unknown error');let panel=$('openErrorPanel');
 if(!panel){panel=document.createElement('div');panel.id='openErrorPanel';panel.className='error-overlay';panel.innerHTML='<div class="error-card"><div class="error-icon">!</div><h2>Document could not be opened</h2><p id="openErrorMessage"></p><div class="error-details"><span>File</span><code id="openErrorFile"></code><span>Engine</span><code id="openErrorEngine"></code></div><div class="error-actions"><button id="dismissError">Close</button><label for="fileInput" class="retry-open">Choose another file</label></div></div>';document.body.appendChild(panel);panel.querySelector('#dismissError').onclick=()=>panel.classList.add('hidden');panel.querySelector('.retry-open').onclick=()=>panel.classList.add('hidden')}
 panel.querySelector('#openErrorMessage').textContent=message;panel.querySelector('#openErrorFile').textContent=file&&file.name?file.name:'Unknown';panel.querySelector('#openErrorEngine').textContent=(window.pako?'Local Pako ready':'Local Pako missing')+' · '+(window.LocalDocxParser?'Parser ready':'Parser missing');panel.classList.remove('hidden')
}
async function openFile(file){
 if(!file)return;if(!/\.docx$/i.test(file.name)){alert('This document editor currently supports DOCX files.');return}
 const previous={currentFile,currentFileName,currentBuffer,sourceContext,zoom,pages,currentPage,currentPageSpec,dirty,documentActive,history:[...history],historyIndex,mediaUrls,content:pagesHost.innerHTML,outlineItems:Array.from($('outlineList').querySelectorAll('.outline-item')).map(button=>({level:Number((button.className.match(/level-(\d+)/)||[])[1]||1),text:button.textContent,blockIndex:Number(button.dataset.blockIndex)})),title:$('titleText').value,welcomeHidden:welcome.classList.contains('hidden')};
 let parsed=null;
 setLoading('Opening '+file.name+'…');status('Reading document…');
 try{
  if(!window.LocalDocxParser)throw new Error('The DOCX parser did not load. Keep the complete application folder structure intact.');
  if(window.InkDeskRuntime)InkDeskRuntime.validateInputSize(file.size,file.name);
  const nextBuffer=await file.arrayBuffer();parsed=await LocalDocxParser.parse(nextBuffer);
  currentFile=file;currentFileName=file.name;documentActive=true;currentBuffer=nextBuffer;sourceContext=parsed.sourceContext||null;currentPageSpec=parsed.pageSpec||null;mediaUrls=parsed.mediaUrls||{};
  setTitleValue(file.name);welcome.classList.add('hidden');pagesHost.innerHTML='';await paginate(parsed.blocks,currentPageSpec);buildOutline(parsed.outline);buildPageList();bindPageObserver();$('saveBtn').disabled=false;zoom=1;applyZoom();resetHistory();setDirty(false);if(recovery)await recovery.startDocument({documentKey:fileRecoveryKey(file),fileName:file.name,sourceData:nextBuffer,sourceMeta:{kind:'docx'},resetSnapshots:true});revokeMediaUrls(previous.mediaUrls);status(file.name+' opened');parsed=null;
 }catch(e){
  console.error(e);if(parsed&&parsed.mediaUrls)revokeMediaUrls(parsed.mediaUrls);
  currentFile=previous.currentFile;currentFileName=previous.currentFileName;currentBuffer=previous.currentBuffer;sourceContext=previous.sourceContext;zoom=previous.zoom;pages=previous.pages;currentPage=previous.currentPage;currentPageSpec=previous.currentPageSpec;dirty=previous.dirty;documentActive=previous.documentActive;history=previous.history;historyIndex=previous.historyIndex;mediaUrls=previous.mediaUrls;pagesHost.innerHTML=previous.content;Array.from(pagesHost.querySelectorAll('.page')).forEach((page,index)=>{page._pageSpec=previous.pages[index]?.spec||previous.currentPageSpec});buildOutline(previous.outlineItems);buildPageList();$('titleText').value=previous.title;welcome.classList.toggle('hidden',previous.welcomeHidden);setDirty(previous.dirty);if(previous.documentActive){bindPageObserver();applyZoom()}else $('saveBtn').disabled=true;showOpenError(e,file);status('Open failed; previous document preserved');
 }finally{clearLoading();fileInput.value=''}
}
function createBlankDocument(){
 revokeMedia();clearSearch();savedRange=null;currentBuffer=null;sourceContext=null;currentFile=null;currentFileName='Untitled.docx';documentActive=true;
 setTitleValue(currentFileName);welcome.classList.add('hidden');pagesHost.innerHTML='';
 currentPageSpec=defaultPageSpec();
 const page=document.createElement('section');page.className='page';page.dataset.page='1';page.dataset.pageLabel='1 / 1';applyPageSpec(page,currentPageSpec);
 const pc=document.createElement('div');pc.className='page-content';applyContentSpec(pc,currentPageSpec);pc.contentEditable='true';pc.spellcheck=true;
 const p=document.createElement('p');p.innerHTML='<br>';pc.appendChild(p);page.appendChild(pc);pagesHost.appendChild(page);
 pages=[[{index:0,html:'<p><br></p>',text:''}]];currentPage=1;
 buildOutline([]);buildPageList();bindPageObserver();$('saveBtn').disabled=false;zoom=1;applyZoom();resetHistory();setDirty(false);if(recovery)recovery.startDocument({fileName:currentFileName,resetSnapshots:true});updateStats();status('New document created');
 requestAnimationFrame(()=>{pc.focus();const r=document.createRange();r.selectNodeContents(p);r.collapse(true);const sel=getSelection();sel.removeAllRanges();sel.addRange(r);rememberSelection()});
}
function closeNewDocumentDialog(){const panel=$('newDocumentPanel');if(panel)panel.remove()}
function showNewDocumentDialog(){
 closeNewDocumentDialog();
 const panel=document.createElement('div');panel.id='newDocumentPanel';panel.className='error-overlay';
 panel.innerHTML='<div class="error-card new-document-card"><div class="word-badge" style="margin:0 auto 14px;width:38px;height:38px">W</div><h2>New document</h2><p>The current unsaved changes will be discarded.</p><div class="error-actions"><button id="cancelNewDocument" type="button">Cancel</button><button id="confirmNewDocument" type="button" class="primary-dialog-button">Create document</button></div></div>';
 document.body.appendChild(panel);
 panel.querySelector('#cancelNewDocument').addEventListener('click',closeNewDocumentDialog);
 panel.querySelector('#confirmNewDocument').addEventListener('click',()=>{closeNewDocumentDialog();createBlankDocument()});
}
function newDocument(){
 if(dirty){showNewDocumentDialog();return}
 createBlankDocument();
}
function commitTitleRename(){
 if(!documentActive){$('titleText').value='Untitled.docx';return}
 const name=normalizeDocxName($('titleText').value);
 currentFileName=name;
 setTitleValue(name);
 if(recovery){recovery.updateFileName(name);recovery.markDirty()}
 status('File renamed to '+name);
}


function fileRecoveryKey(file){return 'file:'+[file.name,file.size,file.lastModified||0].join(':')}
async function recoveryImageSource(src){
 if(!src||!String(src).startsWith('blob:'))return src;
 try{const response=await fetch(src);if(!response.ok)throw new Error('Image response '+response.status);const blob=await response.blob();return await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result||''));reader.onerror=()=>reject(reader.error||new Error('Image conversion failed'));reader.readAsDataURL(blob)})}catch(error){console.warn('A document image could not be embedded in the recovery snapshot.',error);return ''}
}
async function captureDocumentRecovery(){
 if(!documentActive||!pagesHost.querySelector('.page-content'))return null;
 const clone=pagesHost.cloneNode(true),sourceImages=Array.from(pagesHost.querySelectorAll('img')),cloneImages=Array.from(clone.querySelectorAll('img'));
 for(let index=0;index<cloneImages.length;index++){
  const original=sourceImages[index],copy=cloneImages[index],src=(original&&original.dataset.docxData)||copy.getAttribute('src')||'';
  const stable=await recoveryImageSource(src);if(stable){copy.setAttribute('src',stable);copy.dataset.docxData=stable}else copy.removeAttribute('src');
 }
 return{kind:'documents',schemaVersion:1,fileName:displayedFileName(),html:clone.innerHTML,pageSpecs:Array.from(pagesHost.querySelectorAll('.page')).map(page=>page._pageSpec||currentPageSpec||defaultPageSpec()),currentPageSpec:currentPageSpec||defaultPageSpec(),currentPage,zoom};
}
function recoveredOutline(){
 const out=[];pagesHost.querySelectorAll('.page-content h1,.page-content h2,.page-content h3').forEach((node,index)=>{if(!node.dataset.blockIndex)node.dataset.blockIndex='recovery-'+index;out.push({level:Number(node.tagName.slice(1))||1,text:(node.innerText||node.textContent||'').trim(),blockIndex:node.dataset.blockIndex})});return out.filter(item=>item.text)
}
async function restoreDocumentRecovery(context){
 const payload=context&&context.snapshot&&context.snapshot.payload;if(!payload||payload.kind!=='documents')throw new Error('Unsupported document recovery snapshot.');
 revokeMedia();currentFile=null;currentBuffer=null;sourceContext=null;mediaUrls={};
 if(context.source&&context.source.data){
  const sourceData=context.source.data;const parsed=await LocalDocxParser.parse(sourceData);currentBuffer=sourceData;sourceContext=parsed.sourceContext||null;if(parsed.mediaUrls)revokeMediaUrls(parsed.mediaUrls)
 }
 currentFileName=normalizeDocxName(payload.fileName||'Recovered.docx');documentActive=true;currentPageSpec=normalizedPageSpec(payload.currentPageSpec);currentPage=Math.max(1,Number(payload.currentPage)||1);zoom=Math.max(.35,Math.min(1.8,Number(payload.zoom)||1));
 setTitleValue(currentFileName);welcome.classList.add('hidden');pagesHost.innerHTML=String(payload.html||'');
 const pageElements=Array.from(pagesHost.querySelectorAll('.page'));pageElements.forEach((page,index)=>{page._pageSpec=normalizedPageSpec((payload.pageSpecs||[])[index]||currentPageSpec);page.dataset.page=String(index+1);page.dataset.pageLabel=(index+1)+' / '+Math.max(1,pageElements.length)});pages=pageElements.map(page=>[{index:0,html:page.querySelector('.page-content')?.innerHTML||'',text:page.innerText||'',spec:page._pageSpec}]);
 buildOutline(recoveredOutline());buildPageList();bindPageObserver();$('saveBtn').disabled=false;applyZoom();resetHistory();setDirty(true);updateStats();status('Unsaved document restored from this browser');
}
function defaultPageSpec(){return{widthPx:816,heightPx:1056,marginTopPx:82,marginRightPx:86,marginBottomPx:88,marginLeftPx:86,contentWidthPx:644,contentHeightPx:886,fontFamily:'Calibri',fontSizePt:11,lineHeight:1.15}}
function normalizedPageSpec(spec){const d=defaultPageSpec(),x=Object.assign({},d,spec||{});for(const k of ['widthPx','heightPx','marginTopPx','marginRightPx','marginBottomPx','marginLeftPx','contentWidthPx','contentHeightPx','fontSizePt','lineHeight'])if(!Number.isFinite(Number(x[k]))||Number(x[k])<=0)x[k]=d[k];return x}
function applyPageSpec(page,spec){spec=normalizedPageSpec(spec);page.style.width=spec.widthPx+'px';page.style.height=spec.heightPx+'px';page.style.minHeight=spec.heightPx+'px';page.style.padding=spec.marginTopPx+'px '+spec.marginRightPx+'px '+spec.marginBottomPx+'px '+spec.marginLeftPx+'px';page.style.fontFamily=JSON.stringify(spec.fontFamily||'Calibri')+',Arial,sans-serif';page.style.fontSize=spec.fontSizePt+'pt';page.style.lineHeight=String(spec.lineHeight||1.15);page.style.setProperty('--doc-margin-left',spec.marginLeftPx+'px');page.style.setProperty('--doc-margin-right',spec.marginRightPx+'px')}
function applyContentSpec(content,spec){spec=normalizedPageSpec(spec);content.style.width=spec.contentWidthPx+'px';content.style.height=spec.contentHeightPx+'px';content.style.minHeight=spec.contentHeightPx+'px'}
async function paginate(blocks,pageSpec){
 pages=[];const tolerance=3;let current=[],activeSpec=normalizedPageSpec((blocks[0]&&blocks[0].pageSpec)||pageSpec),measure=null,content=null;
 function sameSpec(a,b){return ['widthPx','heightPx','marginTopPx','marginRightPx','marginBottomPx','marginLeftPx'].every(k=>Math.abs(Number(a[k])-Number(b[k]))<.1)}
 function setupMeasure(spec){if(measure)measure.remove();measure=document.createElement('div');measure.className='page pagination-measure';applyPageSpec(measure,spec);measure.style.cssText+='position:fixed;visibility:hidden;pointer-events:none;left:-20000px;top:0;box-shadow:none;contain:none;overflow:visible;';content=document.createElement('div');content.className='pagination-content-measure';content.style.width=spec.contentWidthPx+'px';content.style.height='auto';content.style.minHeight='0';measure.appendChild(content);document.body.appendChild(measure)}
 function commit(){if(!current.length)return;pages.push({items:current,spec:activeSpec});current=[];content.innerHTML=''}
 setupMeasure(activeSpec);
 for(let i=0;i<blocks.length;i++){
  const block=blocks[i],blockSpec=normalizedPageSpec(block.pageSpec||activeSpec);
  if(block.sectionStart&&!sameSpec(blockSpec,activeSpec)){commit();activeSpec=blockSpec;setupMeasure(activeSpec)}else if(block.sectionStart&&current.length)commit();
  if((block.hardPageBreakBefore||block.softPageBreakBefore)&&current.length)commit();
  const holder=document.createElement('div');holder.dataset.blockIndex=String(i);if(Number.isFinite(block.sourceIndex))holder.dataset.sourceIndex=String(block.sourceIndex);if(Number.isFinite(block.sourceSubIndex))holder.dataset.sourceSubIndex=String(block.sourceSubIndex);holder.innerHTML=block.html;content.appendChild(holder);current.push({index:i,html:block.html,text:block.text,sourceIndex:block.sourceIndex,sourceSubIndex:block.sourceSubIndex});
  const overflow=content.scrollHeight>activeSpec.contentHeightPx+tolerance;
  if(overflow&&current.length>1){current.pop();content.removeChild(holder);commit();content.appendChild(holder);current.push({index:i,html:block.html,text:block.text,sourceIndex:block.sourceIndex,sourceSubIndex:block.sourceSubIndex})}
 }
 commit();if(measure)measure.remove();
 pages.forEach((entry,pi)=>{const spec=entry.spec,page=document.createElement('section');page.className='page';page.dataset.page=String(pi+1);page.dataset.pageLabel=(pi+1)+' / '+pages.length;page._pageSpec=spec;applyPageSpec(page,spec);if(spec.headerText){const header=document.createElement('div');header.className='page-header';header.contentEditable='false';header.textContent=spec.headerText;page.appendChild(header)}const pc=document.createElement('div');pc.className='page-content';applyContentSpec(pc,spec);entry.items.forEach(b=>{const wrap=document.createElement('div');wrap.dataset.blockIndex=String(b.index);if(Number.isFinite(b.sourceIndex))wrap.dataset.sourceIndex=String(b.sourceIndex);if(Number.isFinite(b.sourceSubIndex))wrap.dataset.sourceSubIndex=String(b.sourceSubIndex);wrap.innerHTML=b.html;pc.appendChild(wrap)});pc.contentEditable='true';pc.spellcheck=true;page.appendChild(pc);if(spec.footerText){const footer=document.createElement('div');footer.className='page-footer';footer.contentEditable='false';footer.textContent=spec.footerText;page.appendChild(footer)}pagesHost.appendChild(page)});currentPage=1;currentPageSpec=pages[0]?pages[0].spec:pageSpec;updateStats()
}
function buildPageList(){const list=$('pageList');list.innerHTML='';Array.from(pagesHost.children).forEach((page,i)=>{const b=document.createElement('button');b.className='page-thumb';b.innerHTML='<div class="thumb-sheet">'+escapeHtml(page.querySelector('.page-content').innerText.slice(0,600))+'</div><span class="thumb-label">Page '+(i+1)+'</span>';b.onclick=()=>page.scrollIntoView({behavior:'auto',block:'start'});list.appendChild(b)})}
function buildOutline(items){const list=$('outlineList');list.innerHTML='';if(!items.length){list.innerHTML='<p class="muted">No headings were found.</p>';return}items.forEach(it=>{const b=document.createElement('button');b.className='outline-item level-'+Math.min(3,it.level);b.dataset.blockIndex=String(it.blockIndex);b.textContent=it.text;b.onclick=()=>{const n=pagesHost.querySelector('[data-block-index="'+it.blockIndex+'"]');if(n)n.scrollIntoView({behavior:'auto',block:'center'})};list.appendChild(b)})}
function bindPageObserver(){if(observer)observer.disconnect();observer=new IntersectionObserver(entries=>{let best=null;entries.forEach(e=>{if(e.isIntersecting&&(!best||e.intersectionRatio>best.intersectionRatio))best=e});if(best){const n=+best.target.dataset.page;currentPage=n;currentPageSpec=best.target._pageSpec||currentPageSpec;updateStats();document.querySelectorAll('.page-thumb').forEach((x,i)=>x.classList.toggle('active',i===n-1))}},{root:viewport,threshold:[.15,.35,.6]});document.querySelectorAll('.page').forEach(p=>observer.observe(p))}
function applyZoom(){if(Math.abs(zoom-1)<.001){pagesHost.style.transform='none';pagesHost.style.marginBottom='0px'}else{pagesHost.style.transform='scale('+zoom+')';pagesHost.style.marginBottom=Math.max(0,(zoom-1)*pagesHost.scrollHeight)+'px'}$('zoomLabel').textContent=Math.round(zoom*100)+'%'}
function fitWidth(){const available=viewport.clientWidth-64,width=normalizedPageSpec(currentPageSpec).widthPx;zoom=Math.max(.35,Math.min(1.55,available/width));applyZoom()}
function clearSearch(){pagesHost.querySelectorAll('mark[data-search]').forEach(m=>m.replaceWith(document.createTextNode(m.textContent)));pagesHost.querySelectorAll('.page-content').forEach(x=>x.normalize());hits=[];activeHit=-1}
function search(q){clearSearch();$('searchResults').innerHTML='';q=q.trim();if(!q){$('searchCount').textContent='0 results';$('searchResults').innerHTML='<p class="muted">Type a word or phrase.</p>';return}const needle=q.toLocaleLowerCase(),walker=document.createTreeWalker(pagesHost,NodeFilter.SHOW_TEXT,{acceptNode(n){return n.parentElement&&!['SCRIPT','STYLE','MARK'].includes(n.parentElement.tagName)&&n.nodeValue.toLocaleLowerCase().includes(needle)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT}}),nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);nodes.forEach(node=>{const text=node.nodeValue,low=text.toLocaleLowerCase();let pos=0,found=low.indexOf(needle),frag=document.createDocumentFragment();while(found>=0){frag.append(text.slice(pos,found));const m=document.createElement('mark');m.dataset.search='1';m.textContent=text.slice(found,found+q.length);frag.append(m);hits.push(m);pos=found+q.length;found=low.indexOf(needle,pos)}frag.append(text.slice(pos));node.replaceWith(frag)});$('searchCount').textContent=hits.length+' result'+(hits.length===1?'':'s');hits.forEach((m,i)=>{const p=m.closest('.page'),b=document.createElement('button');b.className='search-result';b.innerHTML='<strong>Page '+p.dataset.page+'</strong><span>'+escapeHtml((m.parentElement.innerText||m.textContent).trim().slice(0,100))+'</span>';b.onclick=()=>focusHit(i);$('searchResults').appendChild(b)});if(hits.length)focusHit(0);else $('searchResults').innerHTML='<p class="muted">No results found.</p>'}
function focusHit(i){if(!hits.length)return;activeHit=(i+hits.length)%hits.length;hits.forEach((m,j)=>m.classList.toggle('active-hit',j===activeHit));document.querySelectorAll('.search-result').forEach((b,j)=>b.classList.toggle('active',j===activeHit));hits[activeHit].scrollIntoView({behavior:'auto',block:'center'});$('searchCount').textContent=(activeHit+1)+' of '+hits.length}
function escapeHtml(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function snapshot(){return pagesHost.innerHTML}
function resetHistory(){history=[snapshot()];historyIndex=0;updateHistoryButtons()}
function queueHistory(){if(restoring)return;clearTimeout(historyTimer);historyTimer=setTimeout(()=>{const s=snapshot();if(s===history[historyIndex])return;history=history.slice(0,historyIndex+1);history.push(s);if(history.length>40)history.shift();else historyIndex++;updateHistoryButtons()},350)}
function restoreHistory(index){if(index<0||index>=history.length)return;restoring=true;historyIndex=index;pagesHost.innerHTML=history[index];bindPageObserver();buildPageList();setDirty(true);updateHistoryButtons();setTimeout(()=>restoring=false,0)}
function updateHistoryButtons(){$('undoBtn').disabled=historyIndex<=0;$('redoBtn').disabled=historyIndex>=history.length-1}
function closeSaveCopyPanel(){const panel=$('saveReadyPanel');if(saveReadyUrl){URL.revokeObjectURL(saveReadyUrl);saveReadyUrl=''}if(panel)panel.remove()}
function offerSaveCopy(result){
 closeSaveCopyPanel();
 const panel=document.createElement('div');panel.id='saveReadyPanel';panel.className='error-overlay';saveReadyUrl=URL.createObjectURL(result.blob);
 panel.innerHTML='<div class="error-card"><div class="word-badge" style="margin:0 auto 14px;width:38px;height:38px">W</div><h2>Save a copy</h2><p>The original file will not be changed.</p><p class="save-copy-note">The original OOXML package is preserved whenever possible. Use the button below and choose where the browser should store the new DOCX copy.</p><div class="error-actions"><button id="closeSaveReady">Cancel</button><a id="saveCopyDownload" class="save-copy-link">Save copy</a></div></div>';
 document.body.appendChild(panel);const a=panel.querySelector('#saveCopyDownload');a.href=saveReadyUrl;a.download=window.InkDeskRuntime?InkDeskRuntime.sanitizeFileName(result.fileName,'Document copy.docx'):result.fileName;
 panel.querySelector('#closeSaveReady').onclick=closeSaveCopyPanel;a.onclick=()=>{setDirty(false);if(recovery)recovery.markClean();status('Download requested; confirm the DOCX copy in your downloads');setTimeout(closeSaveCopyPanel,15000)}
}
async function save(){if(!pagesHost.querySelector('.page-content'))return;try{status('Preparing copy…');const result=await LocalDocxWriter.save(pagesHost,currentFileName,currentBuffer,sourceContext);offerSaveCopy(result);status('Copy ready')}catch(e){console.error(e);alert('Could not create a copy: '+e.message);status('Save copy failed')}}
function selectionBlock(){restoreSelection();const s=getSelection();if(!s.rangeCount)return null;let n=s.anchorNode;n=n&&n.nodeType===3?n.parentElement:n;return n&&n.closest('.page-content p,.page-content h1,.page-content h2,.page-content h3,.page-content li,.page-content td')}
function cmd(c,v){restoreSelection();document.execCommand(c,false,v);rememberSelection();setDirty(true);queueHistory();updateStats();status('Formatting applied')}
function makeAlphaList(){cmd('insertOrderedList');const b=selectionBlock(),ol=b&&b.closest('ol');if(ol)ol.style.listStyleType='upper-alpha'}
function insertTable(){const rows=Math.max(1,Math.min(12,parseInt(prompt('Rows','3'))||3)),cols=Math.max(1,Math.min(10,parseInt(prompt('Columns','3'))||3));let h='<table><tbody>';for(let r=0;r<rows;r++){h+='<tr>';for(let c=0;c<cols;c++)h+='<td><br></td>';h+='</tr>'}h+='</tbody></table><p><br></p>';cmd('insertHTML',h)}
function selectedCell(){const b=selectionBlock();return b&&b.closest('td,th')}
function addRow(){const cell=selectedCell();if(!cell){status('Place the cursor inside a table');return}const row=cell.parentElement,clone=row.cloneNode(true);clone.querySelectorAll('td,th').forEach(c=>c.innerHTML='<br>');row.after(clone);setDirty(true);queueHistory()}
function addColumn(){const cell=selectedCell();if(!cell){status('Place the cursor inside a table');return}const idx=cell.cellIndex,table=cell.closest('table');Array.from(table.rows).forEach(row=>{const c=row.insertCell(Math.min(idx+1,row.cells.length));c.innerHTML='<br>'});setDirty(true);queueHistory()}
function insertImage(file){
 if(!file)return;
 if(!/^image\//i.test(file.type||'')){status('Unsupported image');return}
 const reader=new FileReader();
 reader.onerror=()=>{status('Image could not be read');alert('The selected image could not be read.')};
 reader.onload=()=>{
  const src=String(reader.result||'');
  const img=document.createElement('img');img.src=src;img.alt=file.name||'Inserted image';img.dataset.docxData=src;img.style.width='50%';img.style.height='auto';
  const after=document.createElement('p');after.innerHTML='<br>';
  const sel=getSelection();let range=null;
  if(sel&&sel.rangeCount){const r=sel.getRangeAt(0);if(pagesHost.contains(r.commonAncestorContainer))range=r}
  if(range){range.deleteContents();range.insertNode(after);range.insertNode(img);range.setStartAfter(after);range.collapse(true);sel.removeAllRanges();sel.addRange(range)}
  else{const pc=pagesHost.querySelector('.page-content');if(!pc){status('Open a document first');return}pc.appendChild(img);pc.appendChild(after)}
  img.onload=()=>{setDirty(true);queueHistory();status('Image inserted')};
  setDirty(true);queueHistory();
 };
 reader.readAsDataURL(file)
}
const rulerState={left:0,first:0,right:0};
function rulerPixelsToDocument(x,rect){return Math.round(x*(644/Math.max(1,rect.width)))}
function updateRulerVisual(){
 $('leftIndent').style.left=rulerState.left+'px';$('hangingIndent').style.left=rulerState.left+'px';$('firstIndent').style.left=rulerState.first+'px';$('rightIndent').style.right=rulerState.right+'px';
}
function applyRulerToSelection(rect){const b=selectionBlock();if(!b)return;const left=rulerPixelsToDocument(rulerState.left,rect),first=rulerPixelsToDocument(rulerState.first,rect),right=rulerPixelsToDocument(rulerState.right,rect);b.style.marginLeft=left+'px';b.style.textIndent=(first-left)+'px';b.style.marginRight=right+'px';setDirty(true);queueHistory()}
function bindRuler(id,kind){const h=$(id),track=$('ruler').querySelector('.ruler-track');let down=false,startX=0,startLeft=0,startFirst=0;h.onpointerdown=e=>{down=true;startX=e.clientX;startLeft=rulerState.left;startFirst=rulerState.first;h.setPointerCapture(e.pointerId);e.preventDefault()};h.onpointermove=e=>{if(!down)return;const rect=track.getBoundingClientRect(),max=Math.max(0,rect.width),local=Math.max(0,Math.min(max,e.clientX-rect.left));if(kind==='first')rulerState.first=local;else if(kind==='hanging')rulerState.left=local;else if(kind==='left'){const delta=e.clientX-startX;rulerState.left=Math.max(0,Math.min(max,startLeft+delta));rulerState.first=Math.max(0,Math.min(max,startFirst+delta))}else if(kind==='right')rulerState.right=Math.max(0,Math.min(max,rect.right-e.clientX));updateRulerVisual();applyRulerToSelection(rect)};h.onpointerup=h.onpointercancel=()=>down=false}
recovery=window.InkDeskLocalRecovery?InkDeskLocalRecovery.create({module:'documents',appVersion:'0.20.2.16',defaultFileName:'Untitled.docx',serialize:captureDocumentRecovery,restore:restoreDocumentRecovery,status:message=>{if(message&&/restored|failed/i.test(message))status(message)}}):null;
if(recovery){window.__InkDeskDocumentsRecovery={manager:recovery,capture:captureDocumentRecovery,restore:restoreDocumentRecovery};recovery.promptLatest()}
updateRulerVisual()
fileInput.addEventListener('change',e=>openFile(e.target.files[0]));$('newBtn').addEventListener('click',newDocument);$('newWelcomeBtn').addEventListener('click',newDocument);$('sidebarBtn').onclick=()=>document.querySelector('.workspace').classList.toggle('sidebar-hidden');$('zoomIn').onclick=()=>{zoom=Math.min(1.8,zoom+.1);applyZoom()};$('zoomOut').onclick=()=>{zoom=Math.max(.45,zoom-.1);applyZoom()};$('zoomLabel').onclick=()=>{zoom=1;applyZoom()};$('fitWidth').onclick=fitWidth;$('saveBtn').onclick=save;
$('titleText').addEventListener('focus',e=>e.target.select());$('titleText').addEventListener('blur',commitTitleRename);$('titleText').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();e.target.blur()}if(e.key==='Escape'){e.preventDefault();e.target.value=displayedFileName();e.target.blur()}});
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===t));document.querySelectorAll('.side-panel').forEach(p=>p.classList.toggle('active',p.id===t.dataset.panel));if(t.dataset.panel==='searchPanel')setTimeout(()=>$('searchInput').focus(),50)});
let searchTimer;$('searchInput').oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>search($('searchInput').value),180)};$('nextHit').onclick=()=>focusHit(activeHit+1);$('prevHit').onclick=()=>focusHit(activeHit-1);
window.addEventListener('keydown',e=>{const mod=e.ctrlKey||e.metaKey;if(mod&&e.key.toLowerCase()==='f'){e.preventDefault();document.querySelector('[data-panel="searchPanel"]').click()}if(mod&&e.key.toLowerCase()==='s'){e.preventDefault();save()}if(mod&&e.key.toLowerCase()==='o'){e.preventDefault();fileInput.click()}if(mod&&e.key.toLowerCase()==='z'){e.preventDefault();e.shiftKey?restoreHistory(historyIndex+1):restoreHistory(historyIndex-1)}if(mod&&e.key.toLowerCase()==='y'){e.preventDefault();restoreHistory(historyIndex+1)}});
document.querySelectorAll('.fmt-btn[data-cmd]').forEach(b=>{b.addEventListener('pointerdown',e=>{rememberSelection();e.preventDefault()});b.onclick=()=>cmd(b.dataset.cmd)});$('undoBtn').onclick=()=>restoreHistory(historyIndex-1);$('redoBtn').onclick=()=>restoreHistory(historyIndex+1);['fontSelect','sizeSelect','styleSelect','lineSpacing'].forEach(id=>$(id).addEventListener('pointerdown',rememberSelection));$('fontSelect').onchange=e=>cmd('fontName',e.target.value);$('sizeSelect').onchange=e=>cmd('fontSize',e.target.value);$('styleSelect').onchange=e=>cmd('formatBlock',e.target.value);$('lineSpacing').onchange=e=>{restoreSelection();const sel=getSelection();const blocks=new Set();if(sel&&sel.rangeCount){const r=sel.getRangeAt(0);pagesHost.querySelectorAll('.page-content p,.page-content h1,.page-content h2,.page-content h3,.page-content li,.page-content td').forEach(b=>{try{if(r.intersectsNode(b))blocks.add(b)}catch(error){console.warn('Selection intersection could not be tested.',error)}})}if(!blocks.size){const b=selectionBlock();if(b)blocks.add(b)}blocks.forEach(b=>b.style.lineHeight=e.target.value);if(blocks.size){rememberSelection();setDirty(true);queueHistory();updateStats();status('Line spacing applied')}};$('alphaList').onclick=makeAlphaList;$('tableBtn').onclick=insertTable;$('rowBtn').onclick=addRow;$('colBtn').onclick=addColumn;$('imageInput').onchange=e=>{insertImage(e.target.files[0]);e.target.value=''};bindRuler('firstIndent','first');bindRuler('hangingIndent','hanging');bindRuler('leftIndent','left');bindRuler('rightIndent','right');
document.addEventListener('selectionchange',()=>{const sel=getSelection();if(sel&&sel.rangeCount&&rangeInsideEditor(sel.getRangeAt(0))){rememberSelection();updateStats()}});pagesHost.addEventListener('input',()=>{rememberSelection();status('Edited');setDirty(true);queueHistory();updateStats()});pagesHost.addEventListener('click',e=>{pagesHost.querySelectorAll('img.selected-image').forEach(i=>i.classList.remove('selected-image'));if(e.target.tagName==='IMG')e.target.classList.add('selected-image')});
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});window.addEventListener('resize',()=>{if(pages.length&&window.innerWidth<760)fitWidth()});
updateHistoryButtons();updateStats();
})();

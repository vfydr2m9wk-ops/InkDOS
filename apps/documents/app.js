(function(global){'use strict';
const NS=global.InkDOS2Documents;if(!NS)throw new Error('Documents runtime namespace missing.');
const $=id=>document.getElementById(id);
function loadScript(src,test){if(test?.())return Promise.resolve();return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(new Error('DOCUMENTS_LOCAL_ASSET_LOAD_FAILED: '+src));document.head.appendChild(s)})}
function loadCss(href,key){if(document.querySelector('link[data-doc-'+key+']'))return;const l=document.createElement('link');l.rel='stylesheet';l.href=href;l.dataset['doc'+key.toUpperCase()]='1';document.head.appendChild(l)}
async function loadD1(){loadCss('ui/d1-tools.css','d1');await loadScript('engine/d1-docx-extension.js',()=>!!NS.D1DocxExtension);await loadScript('ui/d1-tools.js',()=>!!NS.D1Tools)}
async function loadD2(){loadCss('ui/d2-tools.css','d2');await loadScript('engine/d2-docx-extension.js',()=>!!NS.D2DocxExtension);await loadScript('engine/d2-sections-extension.js',()=>!!NS.D2SectionsExtension);await loadScript('io/rtf-importer.js',()=>!!NS.RtfImporter);await loadScript('ui/d2-tools.js',()=>!!NS.D2Tools);await loadScript('ui/d2-sections.js',()=>!!NS.D2Sections)}
function installDocxOnOffFix(){
 if(NS.DocxOnOffFix||!NS.DocxParser||!global.JSZip)return;
 const originalParse=NS.DocxParser.parse.bind(NS.DocxParser),W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';
 const direct=(el,name)=>Array.from(el?.children||[]).find(x=>x.localName===name)||null;
 const val=el=>el?(el.getAttributeNS(W,'val')||el.getAttribute('w:val')||el.getAttribute('val')||''):'';
 const onOff=el=>{if(!el)return false;const raw=String(val(el)||'').trim().toLowerCase();return !['0','false','off','no'].includes(raw)};
 const sourceParagraph=(bodyChildren,block)=>{const source=bodyChildren[block.sourceIndex];if(!source)return null;if(source.localName==='p')return source;if(source.localName==='sdt'){const content=direct(source,'sdtContent')||source,items=Array.from(content.children||[]).filter(x=>x.localName==='p'||x.localName==='tbl'),candidate=items[block.sourceSubIndex||0];return candidate?.localName==='p'?candidate:null}return null};
 NS.DocxParser.parse=async function(buffer){const result=await originalParse(buffer);try{const zip=await global.JSZip.loadAsync(buffer),main=zip.file('word/document.xml')||zip.file('documents/document.xml');if(!main)return result;const text=await main.async('string');if(/<!DOCTYPE|<!ENTITY/i.test(text))return result;const doc=new DOMParser().parseFromString(text,'application/xml');if(doc.getElementsByTagName('parsererror').length)return result;const body=Array.from(doc.getElementsByTagNameNS('*','body'))[0],bodyChildren=Array.from(body?.children||[]);for(const block of result.blocks||[]){if(!Number.isFinite(block.sourceIndex))continue;const p=sourceParagraph(bodyChildren,block),pPr=direct(p,'pPr');if(!pPr)continue;const pageBreak=direct(pPr,'pageBreakBefore'),keepNext=direct(pPr,'keepNext');if(pageBreak)block.hardPageBreakBefore=onOff(pageBreak);if(keepNext)block.keepNext=onOff(keepNext)}}catch(error){console.warn('DOCX on/off repair skipped.',error)}return result};
 NS.DocxOnOffFix=Object.freeze({installed:true});
}
async function boot(){installDocxOnOffFix();await loadScript('runtime/commands/document-commands.js',()=>!!NS.DocumentCommands);await loadD1();await loadD2();
const session=new NS.DocumentSession();
const state=new NS.DocumentState(session);
const viewport=$('viewport'),pagesHost=$('pagesHost'),welcome=$('welcome'),fileInput=$('fileInput');
fileInput.accept='.docx,.rtf,.doc,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/rtf,application/msword';const startCopy=welcome?.querySelector('.start-card p');if(startCopy)startCopy.textContent='Create a document or open a DOCX, RTF or legacy DOC file locally.';
const adapter=new NS.ContentViewportAdapter(viewport,pagesHost);
let zoomControls=null;
const zoom=new NS.ZoomController(adapter,pagesHost,info=>zoomControls?.update(info));
const navigation=NS.NavigationPanel.create({pagesHost});
const chrome=NS.ChromeController.create({session});
const sessionDialog=NS.SessionDialog.create();
const surface=NS.PageSurface.create({state,session,viewport,pagesHost,welcome,zoom,navigation});
const editor=NS.EditorController.create({state,session,pagesHost,surface,chrome,zoom});
const ruler=NS.RulerController.create({state,editor});
const saveController=NS.SaveController.create({session,pagesHost,chrome});
const fileOpen=NS.FileOpenController.create({state,session,fileInput,pagesHost,chrome,surface,editor,sessionDialog,saveController});
saveController.setPromoter?.(fileOpen.openFile);
zoomControls=NS.ZoomControls.create({zoom});
const commandRegistry=NS.DocumentCommands.create({fileOpen,saveController,editor,navigation});
const commands=NS.CommandController.create({session,pagesHost,chrome,fileOpen,editor,ruler,navigation,zoom,zoomControls,commands:commandRegistry});
const d1=NS.D1Tools.create({state,session,pagesHost,surface,editor,navigation,chrome});
const d2=NS.D2Tools.create({state,session,pagesHost,surface,editor,navigation,chrome,d1});
const d2Sections=NS.D2Sections.create({state,session,pagesHost,surface,editor,d1,chrome});
chrome.setChooseFile(fileOpen.requestOpen);
NS.Appearance.install();
zoom.install();
fileOpen.install();
commandRegistry.install();
commands.install();
d1.install();
d2.install();
d2Sections.install();
let authorizedUnload=false;
const homeLink=document.querySelector('a[aria-label="Home"]');
homeLink?.addEventListener('click',async e=>{if(!session.dirty)return;e.preventDefault();const href=homeLink.href;if(!(await fileOpen.requestLeave()))return;authorizedUnload=true;global.location.assign(href)});
global.addEventListener('beforeunload',e=>{if(authorizedUnload){authorizedUnload=false;return}if(!session.dirty)return;e.preventDefault();e.returnValue=''});
chrome.syncDirty();
surface.updateStats();
NS.DocumentsApp=Object.freeze({session,state,zoom,d1,d2,d2Sections,open:fileOpen.openFile,requestOpen:fileOpen.requestOpen,newDocument:fileOpen.requestNew,save:saveController.save});
}
boot().catch(e=>{console.error(e);const status=$('statusText');if(status)status.textContent='Documents tools failed to load'});
})(globalThis);

(function(global){'use strict';
function installToolbarRail(){
 const target=document.getElementById('formatbar')||document.getElementById('editbar')||document.getElementById('toolbar');
 if(!target||target.closest('.inkdos-toolbar-rail'))return;
 const style=document.createElement('style');style.id='inkdosToolbarRailStyle';style.textContent=`.inkdos-toolbar-rail{width:100%;min-width:0;display:grid;grid-template-columns:34px 1px minmax(0,1fr) 1px 34px;align-items:stretch;background:var(--chrome,var(--frame-chrome,#fff));border-bottom:1px solid var(--line,var(--frame-line,#d7dce2));position:relative;z-index:30}.inkdos-toolbar-rail>.inkdos-toolbar-scroll{grid-column:3;min-width:0!important;width:100%!important;max-width:none!important;border-bottom:0!important}.inkdos-toolbar-arrow{width:34px;min-width:34px;min-height:44px;padding:0;border:0;border-radius:0;background:transparent;color:var(--muted,var(--frame-muted,#5f6368));font:600 18px/1 Arial,sans-serif;display:grid;place-items:center;cursor:pointer;user-select:none;-webkit-user-select:none}.inkdos-toolbar-arrow:hover:not(:disabled),.inkdos-toolbar-arrow:focus-visible:not(:disabled){background:var(--toolbar-hover,var(--frame-hover,rgba(60,64,67,.08)));color:var(--text,var(--frame-text,#202124));outline:none}.inkdos-toolbar-arrow:disabled{opacity:.28;cursor:default}.inkdos-toolbar-separator{width:1px;height:calc(100% - 16px);min-height:22px;align-self:center;background:var(--line,var(--frame-line,#d7dce2));pointer-events:none}.inkdos-toolbar-rail-host::after{display:none!important}@media(max-width:480px){.inkdos-toolbar-rail{grid-template-columns:30px 1px minmax(0,1fr) 1px 30px}.inkdos-toolbar-arrow{width:30px;min-width:30px;font-size:17px}}`;(document.head||document.documentElement).appendChild(style);
 const shell=document.createElement('div');shell.className='inkdos-toolbar-rail';
 const left=document.createElement('button'),right=document.createElement('button'),sepL=document.createElement('span'),sepR=document.createElement('span');
 left.type=right.type='button';left.className=right.className='inkdos-toolbar-arrow';sepL.className=sepR.className='inkdos-toolbar-separator';left.textContent='<';right.textContent='>';left.setAttribute('aria-label','Scroll toolbar left');right.setAttribute('aria-label','Scroll toolbar right');
 const parent=target.parentNode;parent.insertBefore(shell,target);shell.append(left,sepL,target,sepR,right);target.classList.add('inkdos-toolbar-scroll');if(parent.classList?.contains('toolstrip-shell'))parent.classList.add('inkdos-toolbar-rail-host');
 function sync(){const max=Math.max(0,target.scrollWidth-target.clientWidth);left.disabled=max<2||target.scrollLeft<=1;right.disabled=max<2||target.scrollLeft>=max-1}
 function move(dir){const amount=Math.max(150,Math.round(target.clientWidth*.62));try{target.scrollBy({left:dir*amount,behavior:'smooth'})}catch(_){target.scrollLeft+=dir*amount}setTimeout(sync,180)}
 left.addEventListener('click',()=>move(-1));right.addEventListener('click',()=>move(1));target.addEventListener('scroll',sync,{passive:true});global.addEventListener('resize',sync,{passive:true});
 if(global.ResizeObserver)new ResizeObserver(sync).observe(target);new MutationObserver(sync).observe(target,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class','style']});requestAnimationFrame(sync);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installToolbarRail,{once:true});else installToolbarRail();
})(globalThis);
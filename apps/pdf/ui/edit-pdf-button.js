(function(global){'use strict';
// PDF workspace: Edit PDF, a header button left of Settings (sun) like Edit with ONLYOFFICE in the office apps. The
// tool bar stays the single 2.8 bar. The button frames the BentoPDF toolkit of InkDOS-tools (its own origin, AGENTS.md
// origin isolation) over the workspace and hands it the open PDF through the viewer protocol (InkDOS-tools
// viewers/viewer-embed.js + bento-carry.js): every message checked against, and sent to, that origin.
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
const TOOLS_ORIGIN='https://inkdos-tools.github.io',TOOLKIT=TOOLS_ORIGIN+'/InkDOS-tools/bentopdf/';
// BentoPDF pages opened with the current PDF from the Security (lock) menu
const PAGES={protect:'encrypt-pdf.html',unprotect:'decrypt-pdf.html'};
const doc=document,root=doc.documentElement,$=id=>doc.getElementById(id);
const pt=()=>/^pt/i.test(String(global.InkDOSLocalization?.currentLanguage||root.lang||global.navigator.language||''));
const LABELS={edit:['Editar PDF','Edit PDF'],section:['Senha do PDF','PDF password'],protect:['Proteger com senha','Protect with password'],unprotect:['Remover senha','Remove password'],back:['Voltar ao PDF','Back to the PDF'],open:['Abra um PDF primeiro.','Open a PDF first.'],pick:['Ferramentas de PDF','PDF tools'],advanced:['Ferramentas avançadas','Advanced tools'],search:['Pesquisar ferramentas','Search tools'],none:['Nenhuma ferramenta encontrada.','No tools match your search.'],close:['Fechar','Close']};
const label=k=>LABELS[k][pt()?0:1];
const desktop=()=>!!global.InkDOSDesktop||root.dataset.inkdosHost==='tauri';
function debug(){return NS.PdfStabilityDebug||null}
function status(text){try{debug()?.commands?.chrome?.status?.(text)}catch(_){}const live=$('statusText')||$('pdfStatus');if(live)live.textContent=text}
function currentFile(){const s=debug()?.session;if(!s?.sourceBytes)return null;const name=String(s.fileName||'document.pdf');return new File([s.sourceBytes],/\.pdf$/i.test(name)?name:name+'.pdf',{type:'application/pdf'})}
function css(){if($('pdfEditBtnStyle'))return;const s=doc.createElement('style');s.id='pdfEditBtnStyle';s.textContent=
 '#pdfEditBtn{width:auto;min-width:0;padding:0 10px;display:inline-flex;align-items:center;white-space:nowrap;font:inherit;font-size:13px;font-weight:600}'+
 '@media (max-width:640px){#pdfEditBtn{padding:0 6px;font-size:12px}}'+
 '.pdf-toolkit-layer{position:fixed;inset:0;z-index:2147483646;display:flex;flex-direction:column;background:var(--bg,#f2f5f8);color:var(--text,#192235)}'+
 '.pdf-toolkit-head{display:flex;align-items:center;gap:10px;padding:6px 10px;background:var(--chrome,#fff);border-bottom:1px solid var(--line,#e3e8ef);font-weight:600;font-size:13px}'+
 '.pdf-toolkit-head span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'+
 '.pdf-toolkit-head button{height:32px;padding:0 12px;border:1px solid var(--line,#d5dce6);border-radius:9px;background:var(--control-bg,var(--panel,#f0f2f5));color:var(--control-fg,var(--text,#192235));font:inherit;cursor:pointer}'+
 '.pdf-toolkit-body{position:relative;flex:1 1 auto;min-height:0;overflow:auto;-webkit-overflow-scrolling:touch}'+
 '.pdf-toolkit-body iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#fff}';
 doc.head.appendChild(s)}
function openToolkit(page){
 const file=currentFile();if(!file){status(label('open'));return}
 // the toolkit opens as a page of its own, with no white frame over the workspace (owner, 2026-10-10); the PDF goes
 // through runtime/platform/file-launch.js and the browser's Back returns here
 const launch=global.InkDOSFileLaunch;
 if(launch?.handOff&&global.indexedDB){launch.handOff(file,new URL(typeof page==='string'?page:'',TOOLKIT)).catch(error=>{console.error('InkDOS: could not hand the PDF to BentoPDF',error);status(label('open'))});return}
 const layer=doc.createElement('div');layer.className='pdf-toolkit-layer';layer.setAttribute('role','dialog');layer.setAttribute('aria-label','BentoPDF');
 const head=doc.createElement('div'),body=doc.createElement('div'),title=doc.createElement('span'),back=doc.createElement('button');
 title.textContent='BentoPDF · '+file.name;back.type='button';back.textContent=label('back');head.append(title,back);
 const frame=doc.createElement('iframe');frame.title='BentoPDF';
 const url=new URL(typeof page==='string'?page:'',TOOLKIT);url.searchParams.set('embed','1');url.searchParams.set('inkdos-theme',root.dataset.theme==='dark'?'dark':'light');frame.src=url.href;
 head.className='pdf-toolkit-head';body.className='pdf-toolkit-body';body.appendChild(frame);layer.append(head,body);doc.body.appendChild(layer);
 let sent=false;
 const onMessage=event=>{if(event.origin!==TOOLS_ORIGIN||event.source!==frame.contentWindow)return;if(event.data?.type==='inkdos-viewer-ready'&&!sent){sent=true;frame.contentWindow.postMessage({type:'inkdos-viewer-open',file},TOOLS_ORIGIN)}};
 global.addEventListener('message',onMessage);
 back.addEventListener('click',()=>{global.removeEventListener('message',onMessage);layer.remove()});
}
// Edit PDF first shows one page of the most used tools, in the order of the usual online PDF sites (organize, convert,
// edit, protect); the last tag opens every BentoPDF tool, alphabetical and searchable (owner, 2026-10-11). The tool
// chosen then opens exactly as before, with the open PDF handed to it
const TAGS=[
 ['organize','merge-pdf','Juntar PDF','Merge PDF'],['organize','split-pdf','Dividir PDF','Split PDF'],['organize','compress-pdf','Comprimir PDF','Compress PDF'],
 ['from','pdf-to-docx','PDF para Word','PDF to Word'],['from','pdf-to-excel','PDF para Excel','PDF to Excel'],['from','pdf-to-jpg','PDF para JPG','PDF to JPG'],
 ['to','word-to-pdf','Word para PDF','Word to PDF'],['to','powerpoint-to-pdf','PowerPoint para PDF','PowerPoint to PDF'],['to','excel-to-pdf','Excel para PDF','Excel to PDF'],['to','image-to-pdf','Imagens para PDF','Images to PDF'],
 ['edit','edit-pdf','Editar PDF','Edit PDF'],['edit','sign-pdf','Assinar PDF','Sign PDF'],['edit','add-watermark','Marca d\'água','Watermark'],['edit','page-numbers','Números de página','Page numbers'],
 ['edit','rotate-pdf','Girar PDF','Rotate PDF'],['edit','organize-pdf','Organizar páginas','Organize pages'],['edit','ocr-pdf','OCR','OCR'],
 ['secure','encrypt-pdf','Proteger PDF','Protect PDF'],['secure','decrypt-pdf','Desbloquear PDF','Unlock PDF']];
// every page of the BentoPDF toolkit (InkDOS-tools bentopdf/), by its own English name
const ALL=[['add-attachments','Add Attachments'],['add-blank-page','Add Blank Page'],['add-page-labels','Add Page Labels'],['add-stamps','Add Stamps'],['add-watermark','Add Watermark'],['adjust-colors','Adjust Colors'],['alternate-merge','Alternate & Mix Pages'],['background-color','Background Color'],['bates-numbering','Bates Numbering'],['bmp-to-pdf','BMP to PDF'],['cbz-to-pdf','CBZ to PDF'],['change-permissions','Change Permissions'],['text-color','Change Text Color'],['combine-single-page','Combine to Single Page'],['compare-pdfs','Compare PDFs'],['compress-pdf','Compress PDF'],['form-creator','Create PDF Form'],['crop-pdf','Crop PDF'],['csv-to-pdf','CSV to PDF'],['decrypt-pdf','Decrypt PDF'],['delete-pages','Delete Pages'],['deskew-pdf','Deskew PDF'],['digital-sign-pdf','Digital Signature'],['divide-pages','Divide Pages'],['duplex-collate','Duplex Collate'],['organize-pdf','Duplicate & Organize'],['edit-attachments','Edit Attachments'],['bookmark','Edit Bookmarks'],['edit-metadata','Edit Metadata'],['edit-pdf-text','Edit PDF Text'],['email-to-pdf','Email to PDF'],['encrypt-pdf','Encrypt PDF'],['epub-to-pdf','EPUB to PDF'],['excel-to-pdf','Excel to PDF'],['extract-attachments','Extract Attachments'],['extract-images','Extract Images'],['extract-pages','Extract Pages'],['extract-tables','Extract Tables'],['fb2-to-pdf','FB2 to PDF'],['fix-page-size','Fix Page Size'],['flatten-pdf','Flatten PDF'],['font-to-outline','Font to Outline'],['header-footer','Header & Footer'],['heic-to-pdf','HEIC to PDF'],['image-to-pdf','Images to PDF'],['invert-colors','Invert Colors'],['jpg-to-pdf','JPG to PDF'],['json-to-pdf','JSON to PDF'],['linearize-pdf','Linearize PDF'],['markdown-to-pdf','Markdown to PDF'],['merge-pdf','Merge PDF'],['mobi-to-pdf','MOBI to PDF'],['n-up-pdf','N-Up PDF'],['ocr-pdf','OCR PDF'],['odg-to-pdf','ODG to PDF'],['odp-to-pdf','ODP to PDF'],['ods-to-pdf','ODS to PDF'],['odt-to-pdf','ODT to PDF'],['page-dimensions','Page Dimensions'],['page-numbers','Page Numbers'],['pages-to-pdf','Pages to PDF'],['pdf-booklet','PDF Booklet'],['edit-pdf','PDF Editor'],['form-filler','PDF Form Filler'],['pdf-multi-tool','PDF Multi Tool'],['pdf-layers','PDF OCG'],['overlay-pdf','PDF Overlay'],['pdf-to-bmp','PDF to BMP'],['pdf-to-cbz','PDF to CBZ'],['pdf-to-csv','PDF to CSV'],['pdf-to-excel','PDF to Excel'],['pdf-to-greyscale','PDF to Greyscale'],['pdf-to-jpg','PDF to JPG'],['pdf-to-json','PDF to JSON'],['pdf-to-markdown','PDF to Markdown'],['pdf-to-pdfa','PDF to PDF/A'],['pdf-to-png','PDF to PNG'],['pdf-to-svg','PDF to SVG'],['pdf-to-text','PDF to Text'],['pdf-to-tiff','PDF to TIFF'],['pdf-to-webp','PDF to WebP'],['pdf-to-docx','PDF to Word'],['pdf-workflow','PDF Workflow Builder'],['pdf-to-zip','PDFs to ZIP'],['png-to-pdf','PNG to PDF'],['posterize-pdf','Posterize PDF'],['powerpoint-to-pdf','PowerPoint to PDF'],['prepare-pdf-for-ai','Prepare PDF for AI'],['psd-to-pdf','PSD to PDF'],['pub-to-pdf','PUB to PDF'],['rasterize-pdf','Rasterize PDF'],['remove-annotations','Remove Annotations'],['remove-blank-pages','Remove Blank Pages'],['remove-metadata','Remove Metadata'],['remove-restrictions','Remove Restrictions'],['repair-pdf','Repair PDF'],['reverse-pages','Reverse Pages'],['rotate-custom','Rotate by Custom Degrees'],['rotate-pdf','Rotate PDF'],['rtf-to-pdf','RTF to PDF'],['sanitize-pdf','Sanitize PDF'],['scanner-effect','Scanner Effect'],['sign-pdf','Sign PDF'],['split-pdf','Split PDF'],['svg-to-pdf','SVG to PDF'],['table-of-contents','Table of Contents'],['txt-to-pdf','Text to PDF'],['tiff-to-pdf','TIFF to PDF'],['timestamp-pdf','Timestamp PDF'],['validate-signature-pdf','Validate Signature'],['view-metadata','View Metadata'],['vsd-to-pdf','VSD to PDF'],['webp-to-pdf','WebP to PDF'],['word-to-pdf','Word to PDF'],['wpd-to-pdf','WPD to PDF'],['wps-to-pdf','WPS to PDF'],['xml-to-pdf','XML to PDF'],['xps-to-pdf','XPS to PDF']];
function pickerCss(){if($('pdfToolPickerStyle'))return;const s=doc.createElement('style');s.id='pdfToolPickerStyle';s.textContent=
 '.pdf-picker{position:fixed;inset:0;z-index:2147483645;display:flex;flex-direction:column;background:var(--bg,#f2f5f8);color:var(--text,#192235)}'+
 '.pdf-picker-main{flex:1;min-height:0;overflow:auto;padding:18px 16px 24px}'+
 '.pdf-picker-grid{max-width:980px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:10px}'+
 '.pdf-tag{position:relative;min-height:48px;padding:0 14px 0 18px;border:1px solid var(--line,#e3e8ef);border-radius:12px;background:var(--chrome,#fff);color:inherit;font:inherit;font-size:14px;font-weight:600;text-align:left;cursor:pointer;overflow:hidden}'+
 '.pdf-tag:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--tag,#8a94a6)}'+
 '.pdf-tag:hover,.pdf-tag:focus-visible{background:var(--control-bg,var(--panel,#f0f2f5))}'+
 '.pdf-tag[data-kind=organize]{--tag:#d9534f}.pdf-tag[data-kind=from]{--tag:#2f6fed}.pdf-tag[data-kind=to]{--tag:#2e9e5b}.pdf-tag[data-kind=edit]{--tag:#7b5cd6}.pdf-tag[data-kind=secure]{--tag:#d39b1c}.pdf-tag[data-kind=advanced]{--tag:#4b5563}'+
 '.pdf-adv{position:fixed;inset:0;z-index:2147483646;display:grid;place-items:center;padding:16px;background:rgba(15,23,42,.28);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}'+
 '.pdf-adv-panel{width:min(520px,100%);max-height:min(640px,100%);display:flex;flex-direction:column;border:1px solid var(--line,#e3e8ef);border-radius:16px;background:var(--chrome,#fff);box-shadow:0 24px 60px rgba(15,23,42,.28);overflow:hidden}'+
 '.pdf-adv-panel input{-webkit-appearance:none;appearance:none;box-sizing:border-box;flex:0 0 auto;margin:12px;height:40px;min-height:40px;padding:0 12px;border:1px solid var(--line,#d5dce6);border-radius:10px;background:var(--bg,#f2f5f8);color:inherit;font:inherit;font-size:15px}'+
 '.pdf-adv-list{flex:1;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;padding:0 8px 8px}'+
 '.pdf-adv-list button{display:block;width:100%;padding:10px 12px;border:0;border-radius:9px;background:none;color:inherit;font:inherit;font-size:14px;text-align:left;cursor:pointer}'+
 '.pdf-adv-list button:hover,.pdf-adv-list button:focus-visible{background:var(--control-bg,var(--panel,#f0f2f5))}'+
 '.pdf-adv-list p{padding:12px;opacity:.7}';
 doc.head.appendChild(s)}
function openPicker(){
 const file=currentFile();if(!file){status(label('open'));return}
 css();pickerCss();
 const layer=doc.createElement('div');layer.className='pdf-picker';layer.setAttribute('role','dialog');layer.setAttribute('aria-label',label('pick'));
 const head=doc.createElement('div'),title=doc.createElement('span'),back=doc.createElement('button');
 head.className='pdf-toolkit-head';title.textContent=label('pick')+' · '+file.name;back.type='button';back.textContent=label('back');head.append(title,back);
 const main=doc.createElement('div'),grid=doc.createElement('div');main.className='pdf-picker-main';grid.className='pdf-picker-grid';
 const tag=(kind,text,run,id)=>{const b=doc.createElement('button');b.type='button';b.className='pdf-tag';b.dataset.kind=kind;if(id)b.dataset.pdfTool=id;b.textContent=text;b.addEventListener('click',run);grid.appendChild(b)};
 const done=()=>{doc.removeEventListener('keydown',onKey);layer.remove()};
 const choose=page=>{done();openToolkit(page)};
 for(const [kind,id,pt_,en] of TAGS)tag(kind,pt()?pt_:en,()=>choose(id+'.html'),id);
 tag('advanced',label('advanced'),()=>advanced(choose),'advanced');
 const onKey=event=>{if(event.key==='Escape'&&!doc.querySelector('.pdf-adv')){event.preventDefault();done()}};
 doc.addEventListener('keydown',onKey);back.addEventListener('click',done);
 main.appendChild(grid);layer.append(head,main);doc.body.appendChild(layer);grid.firstChild.focus({preventScroll:true});
}
function advanced(choose){
 const veil=doc.createElement('div'),panel=doc.createElement('div'),search=doc.createElement('input'),list=doc.createElement('div');
 veil.className='pdf-adv';panel.className='pdf-adv-panel';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label',label('advanced'));
 search.type='search';search.placeholder=label('search');search.setAttribute('aria-label',label('search'));search.autocomplete='off';search.spellcheck=false;list.className='pdf-adv-list';
 const shut=()=>{doc.removeEventListener('keydown',onKey,true);veil.remove()};
 const render=()=>{const q=search.value.trim().toLowerCase();list.replaceChildren();
  const rows=ALL.filter(([id,name])=>!q||(name+' '+id).toLowerCase().includes(q));
  for(const [id,name] of rows){const b=doc.createElement('button');b.type='button';b.textContent=name;b.dataset.pdfTool=id;b.addEventListener('click',()=>{shut();choose(id+'.html')});list.appendChild(b)}
  if(!rows.length){const p=doc.createElement('p');p.textContent=label('none');list.appendChild(p)}};
 const onKey=event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();shut()}};
 doc.addEventListener('keydown',onKey,true);search.addEventListener('input',render);veil.addEventListener('click',event=>{if(event.target===veil)shut()});
 panel.append(search,list);veil.appendChild(panel);doc.body.appendChild(veil);render();search.focus({preventScroll:true});
}
function installHeaderButton(){
 if(desktop()||$('pdfEditBtn'))return;
 const find=()=>doc.querySelector('[data-frame-action="sun"]'),sun=find();
 if(sun)return addHeaderButton(sun);
 // joins the header in the same moment as the sun, so the sun never moves under a finger
 const watch=new MutationObserver(()=>{const s=find();if(s){watch.disconnect();if(!$('pdfEditBtn'))addHeaderButton(s)}});
 watch.observe(doc.documentElement,{childList:true,subtree:true});setTimeout(()=>watch.disconnect(),15000);
}
function addHeaderButton(sun){
 css();const b=doc.createElement('button');b.type='button';b.id='pdfEditBtn';b.className='frame-btn inkdos-office-btn';
 b.textContent=label('edit');b.title=label('edit')+' (BentoPDF)';b.setAttribute('aria-label',label('edit'));b.addEventListener('click',openPicker);
 sun.parentNode.insertBefore(b,sun);
}
installHeaderButton();
// Security (lock): protect the open PDF with a password, or remove one the user knows (BentoPDF, encrypted there)
if(!desktop())global.InkDOSSecurityExtras=[...(global.InkDOSSecurityExtras||[]),...['protect','unprotect'].map(k=>({get section(){return label('section')},get label(){return label(k)},value:'pdf-'+k,run:()=>openToolkit(PAGES[k])}))];
NS.PdfEditButton=Object.freeze({open:openToolkit});
})(globalThis);

(function(){'use strict';
// Advanced tools (Home, web edition): a central, searchable list of extra tools. Every entry is an
// existing open-source tool that runs entirely in this browser; only tools that are actually
// available are listed, so the menu never leads to a missing page.
const TOOLS=Object.freeze([
  {id:'pdf-tools',group:'PDF',title:'PDF tools (beta)',description:'Visual signature, digital signature (A1) and signature check.',href:'./labs/pdf/index.html',icon:'pdf'},
  // from here on: open-source tools built and served by https://github.com/inkdos-tools/InkDOS-tools, a
  // separate origin on purpose (their third-party code cannot reach InkDOS storage); toolHref() passes
  // the InkDOS appearance along, since that site cannot read it
  // BentoPDF opens in its own tab (window:true): its Office-to-PDF conversion (LibreOffice WebAssembly) needs a
  // cross-origin isolated page, which a frame inside InkDOS cannot be
  {id:'bentopdf',group:'PDF',title:'PDF toolkit',description:'Merge, split, compress, convert, OCR, edit and protect PDFs (BentoPDF).',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/',icon:'pdf',window:true},
  // direct shortcuts to the most used PDF toolkit conversions
  {id:'word-to-pdf',group:'Convert',title:'Word to PDF',description:'Convert Word documents (DOCX, DOC, ODT, RTF) to PDF.',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/word-to-pdf.html',icon:'convert',window:true},
  {id:'excel-to-pdf',group:'Convert',title:'Excel to PDF',description:'Convert spreadsheets (XLSX, XLS, ODS) to PDF.',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/excel-to-pdf.html',icon:'convert',window:true},
  {id:'powerpoint-to-pdf',group:'Convert',title:'PowerPoint to PDF',description:'Convert presentations (PPTX, PPT, ODP) to PDF.',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/powerpoint-to-pdf.html',icon:'convert',window:true},
  {id:'pdf-to-docx',group:'Convert',title:'PDF to Word',description:'Turn a PDF into an editable Word document (DOCX).',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/pdf-to-docx.html',icon:'convert',window:true},
  {id:'pdf-to-excel',group:'Convert',title:'PDF to Excel',description:'Extract the tables of a PDF into a spreadsheet (XLSX).',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/pdf-to-excel.html',icon:'convert',window:true},
  {id:'image-to-pdf',group:'Convert',title:'Images to PDF',description:'Combine JPG, PNG, HEIC, WebP and other images into a PDF.',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/image-to-pdf.html',icon:'convert',window:true},
  {id:'pdf-to-jpg',group:'Convert',title:'PDF to images',description:'Save the pages of a PDF as JPG images.',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/pdf-to-jpg.html',icon:'convert',window:true},
  {id:'compress-pdf',group:'Convert',title:'Compress PDF',description:'Make a PDF file smaller.',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/compress-pdf.html',icon:'convert',window:true},
  {id:'squoosh',group:'Convert',title:'Convert and compress images',description:'Convert images between JPG, PNG, WebP and AVIF, resize them and make them smaller (Squoosh).',href:'https://inkdos-tools.github.io/InkDOS-tools/squoosh/',icon:'image'},
  {id:'merge-pdf',group:'Convert',title:'Merge PDFs',description:'Join several PDF files into one.',href:'https://inkdos-tools.github.io/InkDOS-tools/bentopdf/merge-pdf.html',icon:'convert',window:true},
  {id:'archivedrop',group:'Files',title:'Extract ZIP, RAR and 7z',description:'Open ZIP, RAR and 7z archives and save the files inside (ArchiveDrop).',href:'https://inkdos-tools.github.io/InkDOS-tools/archivedrop/',icon:'archive'},
  {id:'cyberchef',group:'Developer',title:'CyberChef (data toolbox)',description:'Encode, decode, hash, encrypt, compress and analyse data.',href:'https://inkdos-tools.github.io/InkDOS-tools/cyberchef/',icon:'code'},
  {id:'python',group:'Developer',title:'Python terminal',description:'A Python 3 console with the standard library (Pyodide).',href:'https://inkdos-tools.github.io/InkDOS-tools/python/',icon:'code'},
  {id:'it-tools',group:'Developer',title:'IT-Tools (developer utilities)',description:'JSON, YAML, UUID, JWT, regex, converters and generators.',href:'https://inkdos-tools.github.io/InkDOS-tools/it-tools/',icon:'code'}
]);
const ICONS={
  pdf:'<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/><path d="M9.5 13h5M9.5 16.5h5"/>',
  archive:'<path d="M4 4h16v4H4z"/><path d="M5 8v12h14V8"/><path d="M10 12h4"/>',
  convert:'<path d="M4 8h13l-3-3M20 16H7l3 3"/>',
  image:'<path d="M4 5h16v14H4z"/><path d="M4 16l5-5 4 4 2-2 5 5"/><circle cx="15.5" cy="9" r="1.5"/>',
  code:'<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
  tool:'<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2L4 16.8V20h3.2l5.3-5.3a4 4 0 0 0 5.2-5.4l-2.5 2.5-2.3-.6-.6-2.3z"/>'
};
const doc=document;
let overlay=null,list=null,search=null,trigger=null,lastFocus=null,shell=null;
// A chosen tool opens in an InkDOS panel (the same top bar and theme as the workspaces) with the
// tool framed below it; "Open full window" leaves for the tool itself. The frame is created on open
// and removed on close, so nothing a tool held outlives the panel.
function toolShell(){
  if(shell)return shell;
  shell=doc.createElement('div');shell.id='toolPanel';shell.className='tool-shell';shell.hidden=true;
  shell.setAttribute('role','dialog');shell.setAttribute('aria-modal','true');shell.setAttribute('aria-labelledby','toolPanelTitle');
  shell.innerHTML='<header class="tool-shell-bar">'
   +'<button type="button" class="tool-shell-back" data-tool-back>‹ <span>Advanced tools</span></button>'
   +'<strong id="toolPanelTitle" class="tool-shell-title"></strong><span class="tool-shell-badge">beta</span>'
   +'<a class="tool-shell-full" data-tool-full target="_top" title="Open full window" aria-label="Open full window"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-8 8M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg></a>'
   +'<button type="button" class="tools-close" data-tool-close aria-label="Close" title="Close">×</button>'
   +'</header><div class="tool-shell-body"></div>';
  shell.querySelector('[data-tool-back]').addEventListener('click',()=>{closeTool();open()});
  shell.querySelector('[data-tool-close]').addEventListener('click',closeTool);
  doc.body.appendChild(shell);
  return shell;
}
function toolHref(tool){
  if(!/^https:/.test(tool.href))return tool.href;
  const url=new URL(tool.href);url.searchParams.set('inkdos-theme',doc.documentElement.dataset.theme==='dark'?'dark':'light');return url.href;
}
function openTool(tool){
  const panel=toolShell();
  close();lastFocus=lastFocus||trigger;
  panel.querySelector('.tool-shell-title').textContent=tool.title;
  panel.querySelector('[data-tool-full]').href=toolHref(tool);
  const frame=doc.createElement('iframe');frame.className='tool-shell-frame';frame.title=tool.title;frame.src=toolHref(tool);
  frame.setAttribute('allow','clipboard-read; clipboard-write');
  panel.querySelector('.tool-shell-body').replaceChildren(frame);
  panel.dataset.toolId=tool.id;panel.hidden=false;doc.documentElement.classList.add('tools-open');
  requestAnimationFrame(()=>panel.querySelector('[data-tool-back]').focus({preventScroll:true}));
}
function closeTool(){
  if(!shell||shell.hidden)return;
  shell.hidden=true;shell.querySelector('.tool-shell-body').replaceChildren();delete shell.dataset.toolId;
  doc.documentElement.classList.remove('tools-open');
  try{(lastFocus||trigger)?.focus()}catch(_){}
}
function icon(name){return '<svg viewBox="0 0 24 24" aria-hidden="true">'+(ICONS[name]||ICONS.tool)+'</svg>'}
function render(query){
  const q=String(query||'').trim().toLowerCase();
  const shown=TOOLS.filter(t=>!q||(t.title+' '+t.description+' '+t.group).toLowerCase().includes(q));
  list.replaceChildren();
  let group='';
  for(const tool of shown){
    if(tool.group!==group){group=tool.group;const h=doc.createElement('h3');h.className='tools-group';h.textContent=group;list.appendChild(h)}
    const a=doc.createElement('a');a.className='tools-item';a.href=toolHref(tool);a.dataset.toolId=tool.id;
    if(tool.window){a.target='_blank';a.rel='noopener'}
    a.innerHTML='<span class="tools-item-icon">'+icon(tool.icon)+'</span><span class="tools-item-copy"><strong></strong><small></small></span><span class="tools-item-chevron" aria-hidden="true">›</span>';
    a.querySelector('strong').textContent=tool.title;a.querySelector('small').textContent=tool.description;
    list.appendChild(a);
  }
  if(!shown.length){const p=doc.createElement('p');p.className='tools-empty';p.textContent='No tools match your search.';list.appendChild(p)}
}
function open(){
  if(!overlay)return;
  lastFocus=doc.activeElement;overlay.hidden=false;doc.documentElement.classList.add('tools-open');
  trigger?.setAttribute('aria-expanded','true');search.value='';render('');
  requestAnimationFrame(()=>search.focus({preventScroll:true}));
}
function close(){
  if(!overlay||overlay.hidden)return;
  overlay.hidden=true;doc.documentElement.classList.remove('tools-open');trigger?.setAttribute('aria-expanded','false');
  try{(lastFocus||trigger)?.focus()}catch(_){}
}
function install(){
  trigger=doc.getElementById('advancedToolsButton');overlay=doc.getElementById('advancedTools');
  if(!trigger||!overlay)return;
  list=doc.getElementById('advancedToolsList');search=doc.getElementById('advancedToolsSearch');
  trigger.addEventListener('click',open);
  doc.getElementById('advancedToolsClose')?.addEventListener('click',close);
  overlay.addEventListener('click',event=>{if(event.target===overlay)close()});
  search.addEventListener('input',()=>render(search.value));
  list.addEventListener('click',event=>{
    const item=event.target.closest('.tools-item');
    if(!item||event.metaKey||event.ctrlKey||event.shiftKey||event.button!==0)return; // new tab/window: the browser handles it
    const tool=TOOLS.find(t=>t.id===item.dataset.toolId);if(!tool||tool.window)return; // window tools: the link opens a new tab
    event.preventDefault();openTool(tool);
  });
  doc.addEventListener('keydown',event=>{if(event.key==='Escape'&&shell&&!shell.hidden){event.preventDefault();closeTool()}});
  doc.addEventListener('keydown',event=>{
    if(overlay.hidden)return;
    if(event.key==='Escape'){event.preventDefault();close();return}
    if(event.key==='Tab'){ // keep focus inside the dialog
      const items=[...overlay.querySelectorAll('button,input,a[href]')].filter(el=>!el.hidden&&el.offsetParent!==null);
      if(!items.length)return;const first=items[0],last=items[items.length-1];
      if(event.shiftKey&&doc.activeElement===first){event.preventDefault();last.focus()}
      else if(!event.shiftKey&&doc.activeElement===last){event.preventDefault();first.focus()}
    }
  });
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',install,{once:true});else install();
window.InkDOSAdvancedTools=Object.freeze({open,close,openTool:id=>{const tool=TOOLS.find(t=>t.id===id);if(tool&&tool.window)window.open(toolHref(tool),'_blank','noopener');else if(tool)openTool(tool);return !!tool},closeTool,get tools(){return TOOLS.slice()}});
})();

(function(){'use strict';
// Advanced tools (Home, web edition): a central, searchable list of extra tools. Every entry is an
// existing open-source tool that runs entirely in this browser; only tools that are actually
// available are listed, so the menu never leads to a missing page.
const TOOLS=Object.freeze([
  {id:'pdf-tools',group:'PDF',title:'PDF tools (beta)',description:'Visual signature, digital signature (A1) and signature check.',href:'./labs/pdf/index.html',icon:'pdf'},
  // from here on: open-source tools built and served by https://github.com/vfydr2m9wk-ops/InkDOS-tools
  {id:'bentopdf',group:'PDF',title:'PDF toolkit (BentoPDF)',description:'Merge, split, compress, convert, OCR, edit and protect PDFs.',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/bentopdf/',icon:'pdf'},
  {id:'archivedrop',group:'Files',title:'Extract ZIP, RAR and 7z',description:'Open ZIP, RAR and 7z archives and save the files inside (ArchiveDrop).',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/archivedrop/',icon:'archive'},
  {id:'odt-view',group:'View',title:'LibreOffice Writer (.odt)',description:'Open an .odt document as a PDF to read, view only (BentoPDF).',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/bentopdf/odt-to-pdf.html',icon:'view'},
  {id:'ods-view',group:'View',title:'LibreOffice Calc (.ods)',description:'Open an .ods spreadsheet as a PDF to read, view only (BentoPDF).',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/bentopdf/ods-to-pdf.html',icon:'view'},
  {id:'odp-view',group:'View',title:'LibreOffice Impress (.odp)',description:'Open an .odp presentation as a PDF to read, view only (BentoPDF).',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/bentopdf/odp-to-pdf.html',icon:'view'},
  {id:'pnk',group:'View',title:'Apple Pages, Numbers and Keynote',description:'View .pages, .numbers and .key files, view only (pnk).',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/pnk/',icon:'view'},
  {id:'cyberchef',group:'Developer',title:'CyberChef (data toolbox)',description:'Encode, decode, hash, encrypt, compress and analyse data.',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/cyberchef/',icon:'code'},
  {id:'python',group:'Developer',title:'Python terminal',description:'A Python 3 console with the standard library (Pyodide).',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/python/',icon:'code'},
  {id:'it-tools',group:'Developer',title:'IT-Tools (developer utilities)',description:'JSON, YAML, UUID, JWT, regex, converters and generators.',href:'https://vfydr2m9wk-ops.github.io/InkDOS-tools/it-tools/',icon:'code'}
]);
const ICONS={
  pdf:'<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/><path d="M9.5 13h5M9.5 16.5h5"/>',
  archive:'<path d="M4 4h16v4H4z"/><path d="M5 8v12h14V8"/><path d="M10 12h4"/>',
  view:'<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
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
function openTool(tool){
  const panel=toolShell();
  close();lastFocus=lastFocus||trigger;
  panel.querySelector('.tool-shell-title').textContent=tool.title;
  panel.querySelector('[data-tool-full]').href=tool.href;
  const frame=doc.createElement('iframe');frame.className='tool-shell-frame';frame.title=tool.title;frame.src=tool.href;
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
    const a=doc.createElement('a');a.className='tools-item';a.href=tool.href;a.dataset.toolId=tool.id;
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
    const tool=TOOLS.find(t=>t.id===item.dataset.toolId);if(!tool)return;
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
window.InkDOSAdvancedTools=Object.freeze({open,close,openTool:id=>{const tool=TOOLS.find(t=>t.id===id);if(tool)openTool(tool);return !!tool},closeTool,get tools(){return TOOLS.slice()}});
})();

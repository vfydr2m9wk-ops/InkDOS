(function(){'use strict';
// Advanced tools (Home, web edition): a central, searchable list of extra tools. Every entry is an
// existing open-source tool that runs entirely in this browser; only tools that are actually
// available are listed, so the menu never leads to a missing page.
const TOOLS=Object.freeze([
  {id:'pdf-tools',group:'PDF',title:'PDF tools (beta)',description:'Visual signature, digital signature (A1) and signature check.',href:'./labs/pdf/index.html',icon:'pdf'}
]);
const ICONS={
  pdf:'<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/><path d="M9.5 13h5M9.5 16.5h5"/>',
  tool:'<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2L4 16.8V20h3.2l5.3-5.3a4 4 0 0 0 5.2-5.4l-2.5 2.5-2.3-.6-.6-2.3z"/>'
};
const doc=document;
let overlay=null,list=null,search=null,trigger=null,lastFocus=null;
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
window.InkDOSAdvancedTools=Object.freeze({open,close,get tools(){return TOOLS.slice()}});
})();

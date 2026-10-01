(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
function create({zoom}={}){const $=id=>document.getElementById(id),btn=$('zoomMenuBtn'),pop=$('zoomPopover'),items=()=>[...pop.querySelectorAll('[data-zoom]')];let effective=1;
 function open(){pop.hidden=false;const anchor=$('zoomInput')||btn,r=anchor.getBoundingClientRect(),w=pop.offsetWidth||200;pop.style.left=Math.max(12,Math.min(innerWidth-12-w,r.left))+'px';pop.style.top=Math.min(innerHeight-12-(pop.offsetHeight||300),r.bottom+6)+'px';btn.setAttribute('aria-expanded','true')}
 function close(){pop.hidden=true;btn.setAttribute('aria-expanded','false')}
 function current(){const z=zoom.inspect();return Math.round((z.mode==='manual'?z.manual:effective)*100)}
 function setManual(pct){zoom.setPercent(pct);sync()}
 const MIN=1,MAX=800,STEP=25,clampPct=n=>Math.max(MIN,Math.min(MAX,Math.round(n)));
 function stepped(pct,dir){return clampPct(dir>0?(Math.floor(pct/STEP)+1)*STEP:(Math.ceil(pct/STEP)-1)*STEP)}
 function parsePct(text){const m=String(text||'').replace(',','.').match(/\d+(?:\.\d+)?/);return m?clampPct(Number(m[0])):null}
 function paint(pct,state){const input=$('zoomInput');if(document.activeElement!==input)input.value=pct+'%';for(const b of items()){const on=state.manual&&Number(b.dataset.zoom)===pct;b.classList.toggle('active',on);b.setAttribute('aria-checked',String(on))}for(const [id,on] of [['fitWidth',!!state.fitWidth],['fitPage',!!state.fitPage]]){const el=$(id);if(!el)continue;el.classList.toggle('active',on);el.setAttribute('aria-checked',String(on))}$('zoomOut').disabled=pct<=MIN;$('zoomIn').disabled=pct>=MAX}
 function bindField(){const input=$('zoomInput');input.addEventListener('focus',()=>{input.value=String(current());input.select()});input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commitInput();input.blur()}else if(e.key==='Escape'){e.preventDefault();input.value=String(current());input.blur()}else if(e.key==='ArrowUp'||e.key==='ArrowDown'){e.preventDefault();setManual(stepped(parsePct(input.value)??current(),e.key==='ArrowUp'?1:-1));input.value=String(current());input.select()}});input.addEventListener('blur',()=>{commitInput();update()});function commitInput(){const pct=parsePct(input.value);if(pct!=null&&pct!==current())setManual(pct)}$('zoomOut').onclick=()=>setManual(stepped(current(),-1));$('zoomIn').onclick=()=>setManual(stepped(current(),1));for(const b of items())b.onclick=()=>{setManual(Number(b.dataset.zoom));close()}}
 function update(){const z=zoom.inspect();paint(current(),{manual:z.mode==='manual',fitWidth:z.mode==='fit-width',fitPage:z.mode==='fit-page'})}
 const sync=update;
 function setEffective(scale){if(Number.isFinite(scale)&&scale>0){effective=scale;sync()}}
 function install(){btn.addEventListener('click',()=>pop.hidden?open():close());document.addEventListener('pointerdown',e=>{if(!pop.hidden&&!pop.contains(e.target)&&!btn.contains(e.target))close()});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!pop.hidden){close();btn.focus()}});addEventListener('resize',()=>{if(!pop.hidden)close()},{passive:true});bindField();$('fitWidth').onclick=()=>{zoom.fitWidth();close();sync()};$('fitPage').onclick=()=>{zoom.fitPage();close();sync()};sync()}
 return Object.freeze({install,sync,setEffective})}
NS.ZoomControls=Object.freeze({create});
})(globalThis);

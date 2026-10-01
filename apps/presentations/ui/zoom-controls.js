(function(global){'use strict';
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
function create({zoom}={}){const $=id=>document.getElementById(id),items=()=>[...document.querySelectorAll('#zoomPopover [data-zoom]')];
 function close(){const pop=$('zoomPopover');if(pop&&!pop.hidden)$('zoomMenuBtn').click()}
 function current(){return Math.round(zoom.scale*100)}
 function setManual(pct){zoom.setMode('manual',pct/100)}
 const MIN=1,MAX=800,STEP=25,clampPct=n=>Math.max(MIN,Math.min(MAX,Math.round(n)));
 function stepped(pct,dir){return clampPct(dir>0?(Math.floor(pct/STEP)+1)*STEP:(Math.ceil(pct/STEP)-1)*STEP)}
 function parsePct(text){const m=String(text||'').replace(',','.').match(/\d+(?:\.\d+)?/);return m?clampPct(Number(m[0])):null}
 function paint(pct,state){const input=$('zoomInput');if(document.activeElement!==input)input.value=pct+'%';for(const b of items()){const on=state.manual&&Number(b.dataset.zoom)===pct;b.classList.toggle('active',on);b.setAttribute('aria-checked',String(on))}for(const [id,on] of [['fitWidth',!!state.fitWidth],['fitPage',!!state.fitPage]]){const el=$(id);if(!el)continue;el.classList.toggle('active',on);el.setAttribute('aria-checked',String(on))}$('zoomOut').disabled=pct<=MIN;$('zoomIn').disabled=pct>=MAX}
 function bindField(){const input=$('zoomInput');input.addEventListener('focus',()=>{input.value=String(current());input.select()});input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commitInput();input.blur()}else if(e.key==='Escape'){e.preventDefault();input.value=String(current());input.blur()}else if(e.key==='ArrowUp'||e.key==='ArrowDown'){e.preventDefault();setManual(stepped(parsePct(input.value)??current(),e.key==='ArrowUp'?1:-1));input.value=String(current());input.select()}});input.addEventListener('blur',()=>{commitInput();update()});function commitInput(){const pct=parsePct(input.value);if(pct!=null&&pct!==current())setManual(pct)}$('zoomOut').onclick=()=>setManual(stepped(current(),-1));$('zoomIn').onclick=()=>setManual(stepped(current(),1));for(const b of items())b.onclick=()=>{setManual(Number(b.dataset.zoom));close()}}
 function update(info){paint(info?.percent||current(),{manual:zoom.mode==='manual',fitWidth:zoom.mode==='fit-width',fitPage:zoom.mode==='fit-page'})}
 function install(){bindField();$('fitWidth').onclick=()=>{zoom.setMode('fit-width');close()};$('fitPage').onclick=()=>{zoom.setMode('fit-page');close()};update()}
 return Object.freeze({install,update});
}
NS.ZoomControls=Object.freeze({create});
})(globalThis);

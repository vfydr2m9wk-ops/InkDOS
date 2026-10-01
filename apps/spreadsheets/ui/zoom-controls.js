(function(global){'use strict';
const NS=global.InkDOS2Spreadsheets=global.InkDOS2Spreadsheets||{};
function create({zoom,viewport}={}){const $=id=>document.getElementById(id),popover=NS.FrameUI.bindPopover({trigger:$('zoomMenuBtn'),popover:$('zoomPopover')}),items=()=>[...document.querySelectorAll('#zoomPopover [data-zoom]')];let fitted=false;
 function close(){popover.close()}
 function current(){return Math.round((zoom?.scale||1)*100)}
 function setManual(pct){fitted=false;zoom.set(pct/100)}
 const MIN=1,MAX=800,STEP=25,clampPct=n=>Math.max(MIN,Math.min(MAX,Math.round(n)));
 function stepped(pct,dir){return clampPct(dir>0?(Math.floor(pct/STEP)+1)*STEP:(Math.ceil(pct/STEP)-1)*STEP)}
 function parsePct(text){const m=String(text||'').replace(',','.').match(/\d+(?:\.\d+)?/);return m?clampPct(Number(m[0])):null}
 function paint(pct,state){const input=$('zoomInput');if(document.activeElement!==input)input.value=pct+'%';for(const b of items()){const on=state.manual&&Number(b.dataset.zoom)===pct;b.classList.toggle('active',on);b.setAttribute('aria-checked',String(on))}for(const [id,on] of [['fitWidth',!!state.fitWidth],['fitPage',!!state.fitPage]]){const el=$(id);if(!el)continue;el.classList.toggle('active',on);el.setAttribute('aria-checked',String(on))}$('zoomOut').disabled=pct<=MIN;$('zoomIn').disabled=pct>=MAX}
 function bindField(){const input=$('zoomInput');input.addEventListener('focus',()=>{input.value=String(current());input.select()});input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commitInput();input.blur()}else if(e.key==='Escape'){e.preventDefault();input.value=String(current());input.blur()}else if(e.key==='ArrowUp'||e.key==='ArrowDown'){e.preventDefault();setManual(stepped(parsePct(input.value)??current(),e.key==='ArrowUp'?1:-1));input.value=String(current());input.select()}});input.addEventListener('blur',()=>{commitInput();update()});function commitInput(){const pct=parsePct(input.value);if(pct!=null&&pct!==current())setManual(pct)}$('zoomOut').onclick=()=>setManual(stepped(current(),-1));$('zoomIn').onclick=()=>setManual(stepped(current(),1));for(const b of items())b.onclick=()=>{setManual(Number(b.dataset.zoom));close()}}
 function update(){paint(current(),{manual:!fitted,fitWidth:fitted});fitted=false}
 function fitWidth(){const geometry=zoom.geometry;if(!geometry||!viewport)return;const available=Math.max(1,viewport.clientWidth-8),natural=Math.max(1,geometry.totalWidth/(zoom.scale||1));fitted=true;zoom.set(Math.min(4,Math.max(.25,available/natural)));close()}
 function install(){bindField();$('fitWidth').onclick=fitWidth;update();return popover}
 return Object.freeze({install,update,get popover(){return popover}})
}
NS.ZoomControls=Object.freeze({create});
})(globalThis);

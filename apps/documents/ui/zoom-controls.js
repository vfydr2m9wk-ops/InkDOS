(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
const PRESETS=[25,50,75,100,125,150,200,300,400];
function create({zoom}={}){const $=id=>document.getElementById(id),items=()=>[...document.querySelectorAll('#zoomPopover [data-zoom]')];
 function close(){const pop=$('zoomPopover');if(pop&&!pop.hidden)$('zoomMenuBtn').click()}
 function current(){return Math.round((zoom.mode==='manual'?zoom.manual:zoom.scale)*100)}
 function step(dir){const pct=current(),next=dir>0?PRESETS.find(p=>p>pct):[...PRESETS].reverse().find(p=>p<pct);if(next)zoom.setMode('manual',next/100)}
 function update(info){const percent=info?.percent||Math.round(zoom.scale*100),manual=zoom.mode==='manual';$('zoomToolbarLabel').textContent=percent+'%';for(const b of items()){const on=manual&&Math.abs(Number(b.dataset.zoom)-percent)<1;b.classList.toggle('active',on);b.setAttribute('aria-checked',String(on))}for(const [id,mode] of [['fitWidth','fit-width'],['fitPage','fit-page']]){const on=zoom.mode===mode;$(id).classList.toggle('active',on);$(id).setAttribute('aria-checked',String(on))}$('zoomOut').disabled=percent<=PRESETS[0];$('zoomIn').disabled=percent>=PRESETS[PRESETS.length-1]}
 function install(){update();$('zoomOut').onclick=()=>step(-1);$('zoomIn').onclick=()=>step(1);for(const b of items())b.onclick=()=>{zoom.setMode('manual',Number(b.dataset.zoom)/100);close()};$('fitWidth').onclick=()=>{zoom.setMode('fit-width');close()};$('fitPage').onclick=()=>{zoom.setMode('fit-page');close()}}
 return Object.freeze({install,update});
}
NS.ZoomControls=Object.freeze({create});
})(globalThis);

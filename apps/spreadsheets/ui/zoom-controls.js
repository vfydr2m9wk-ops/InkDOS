(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
const PRESETS=[25,50,75,100,125,150,200,300,400];
function create({zoom,viewport}={}){const $=id=>document.getElementById(id),popover=NS.FrameUI.bindPopover({trigger:$('zoomMenuBtn'),popover:$('zoomPopover')}),items=()=>[...document.querySelectorAll('#zoomPopover [data-zoom]')];let fitted=false;
 function percent(){return Math.round((zoom?.scale||1)*100)}
 function step(dir){const pct=percent(),next=dir>0?PRESETS.find(p=>p>pct):[...PRESETS].reverse().find(p=>p<pct);if(next){fitted=false;zoom.set(next/100)}}
 function update(){const pct=percent();$('zoomToolbarLabel').textContent=pct+'%';for(const b of items()){const on=!fitted&&Math.abs(Number(b.dataset.zoom)-pct)<1;b.classList.toggle('active',on);b.setAttribute('aria-checked',String(on))}$('fitWidth').classList.toggle('active',fitted);$('fitWidth').setAttribute('aria-checked',String(fitted));$('zoomOut').disabled=pct<=PRESETS[0];$('zoomIn').disabled=pct>=PRESETS[PRESETS.length-1];fitted=false}
 function fitWidth(){const geometry=zoom.geometry;if(!geometry||!viewport)return;const available=Math.max(1,viewport.clientWidth-8),natural=Math.max(1,geometry.totalWidth/(zoom.scale||1));fitted=true;zoom.set(Math.min(4,Math.max(.25,available/natural)));popover.close()}
 function install(){update();$('zoomOut').onclick=()=>step(-1);$('zoomIn').onclick=()=>step(1);for(const b of items())b.onclick=()=>{zoom.set(Number(b.dataset.zoom)/100);popover.close()};$('fitWidth').onclick=fitWidth;return popover}
 return Object.freeze({install,update,get popover(){return popover}})
}
NS.ZoomControls=Object.freeze({create});
})(globalThis);

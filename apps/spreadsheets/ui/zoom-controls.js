(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
function create({zoom,viewport}={}){const $=id=>document.getElementById(id),popover=NS.FrameUI.bindPopover({trigger:$('zoomMenuBtn'),popover:$('zoomPopover')});
 function percent(){return Math.round((zoom?.scale||1)*100)}
 function update(){const pct=percent();$('zoomToolbarLabel').textContent=pct+'%';$('zoomOutput').textContent=pct+'%';$('zoomSlider').value=String(Math.max(25,Math.min(400,pct)));$('zoom100').classList.toggle('active',Math.abs(pct-100)<1);$('fitWidth').classList.remove('active')}
 function fitWidth(){const geometry=zoom.geometry;if(!geometry||!viewport)return;const available=Math.max(1,viewport.clientWidth-8),natural=Math.max(1,geometry.totalWidth/(zoom.scale||1));zoom.set(Math.min(4,Math.max(.25,available/natural)));$('fitWidth').classList.add('active')}
 function install(){update();$('zoomOut').onclick=()=>zoom.step(-.05);$('zoomIn').onclick=()=>zoom.step(.05);$('zoomSlider').oninput=e=>zoom.set(Number(e.target.value)/100);$('zoom100').onclick=()=>zoom.reset();$('fitWidth').onclick=fitWidth;return popover}
 return Object.freeze({install,update,get popover(){return popover}})
}
NS.ZoomControls=Object.freeze({create});
})(globalThis);

(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function create({zoom}={}){const $=id=>document.getElementById(id);
 function update(info){const percent=info?.percent||Math.round(zoom.scale*100);$('zoomToolbarLabel').textContent=percent+'%';$('zoomOutput').textContent=percent+'%';$('zoomSlider').value=String(Math.max(25,Math.min(400,percent)));$('fitWidth').classList.toggle('active',zoom.mode==='fit-width');$('fitPage').classList.toggle('active',zoom.mode==='fit-page');$('zoom100').classList.toggle('active',zoom.mode==='manual'&&Math.abs(percent-100)<1)}
 function install(){update();$('zoomOut').onclick=()=>{const base=zoom.mode==='manual'?zoom.manual:zoom.scale;zoom.setMode('manual',base-.05)};$('zoomIn').onclick=()=>{const base=zoom.mode==='manual'?zoom.manual:zoom.scale;zoom.setMode('manual',base+.05)};$('zoomSlider').oninput=e=>zoom.setMode('manual',Number(e.target.value)/100);$('fitWidth').onclick=()=>zoom.setMode('fit-width');$('fitPage').onclick=()=>zoom.setMode('fit-page');$('zoom100').onclick=()=>zoom.setMode('manual',1)}
 return Object.freeze({install,update});
}
NS.ZoomControls=Object.freeze({create});
})(globalThis);

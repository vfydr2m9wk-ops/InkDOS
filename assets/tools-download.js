(function(){'use strict';
// Home download button: the offline tools panel of the suite (ONLYOFFICE, BentoPDF) opens over Home in a frame of
// the suite's own origin (AGENTS.md origin isolation: messages checked against, and only accepted from, that origin).
const ORIGIN='https://inkdos-tools.github.io',button=document.getElementById('toolsDownload');
if(!button)return;
let layer=null,frame=null;
function close(){if(!layer)return;layer.remove();layer=frame=null;button.focus()}
button.addEventListener('click',event=>{
 event.preventDefault();if(layer)return;
 const root=document.documentElement,theme=root.dataset.theme==='dark'?'dark':'light';
 layer=document.createElement('div');layer.className='tools-download-layer';
 frame=document.createElement('iframe');frame.title=button.title||'Offline tools';
 frame.src=ORIGIN+'/?offline=1&embed=1&inkdos-theme='+theme+'&lang='+encodeURIComponent(root.lang||'en');
 frame.style.colorScheme=theme;layer.appendChild(frame);document.body.appendChild(layer);
});
addEventListener('message',event=>{if(!frame||event.origin!==ORIGIN||event.source!==frame.contentWindow)return;if(event.data&&event.data.type==='inkdos-offline-close')close()});
addEventListener('keydown',event=>{if(event.key==='Escape')close()});
})();

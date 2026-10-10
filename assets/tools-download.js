(function(){'use strict';
// Home download button: the offline tools panel of the suite (ONLYOFFICE, BentoPDF) opens over Home in a frame of
// the suite's own origin (AGENTS.md origin isolation: messages checked against, and only accepted from, that origin).
const ORIGIN='https://inkdos-tools.github.io',button=document.getElementById('toolsDownload');
if(!button)return;
// Browsers that cannot keep pages for offline use (no service worker or Cache Storage, e.g. some in-app web views)
// get no download button at all.
if(!('serviceWorker' in navigator)||!('caches' in window)){button.hidden=true;button.style.display='none';return}
let layer=null,frame=null;
// Closing: the frame goes at once, but an empty shield stays half a second so the rest of the tap (iPad sends the
// click after the finger lifts) does not land on the workspace card behind it.
function close(){if(!layer)return;const shield=layer;layer=frame=null;shield.replaceChildren();shield.style.background='transparent';
 const eat=event=>{event.preventDefault();event.stopPropagation()};for(const type of ['click','pointerup','touchend','mouseup'])shield.addEventListener(type,eat,true);
 setTimeout(()=>shield.remove(),500);button.focus({preventScroll:true})}
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

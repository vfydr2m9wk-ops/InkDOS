/* Pickers keep their look when the host restyles native dropdowns (XeOS): each one is a fixed box that shows
   the icon (icon pickers) or the chosen value (value pickers), with the real dropdown, invisible, on top. */
(function(){const icons=["styleSelect", "fontSelect", "alignmentSelect", "lineSpacing"],values=["sizeSelect"];
function box(s,id,value){const w=document.createElement("span");w.className="inkdos-picker"+(value?" inkdos-value-picker":"");w.dataset.for=id;w.title=s.title||s.getAttribute("aria-label")||"";s.before(w);w.append(s);/* the dropdown list takes the width of the select: the invisible select keeps the width of its longest option (the box clips it) */for(const[k,v]of[["width","auto"],["max-width","none"],["min-width","100%"],["right","auto"]])s.style.setProperty(k,v,"important");if(value){const l=document.createElement("span");l.className="inkdos-picker-label";w.append(l)}}
function label(){for(const id of values){const s=document.getElementById(id),l=s?.parentElement?.querySelector(".inkdos-picker-label");if(!l)continue;const o=s.options[s.selectedIndex],t=o?o.textContent:s.value;if(l.textContent!==t)l.textContent=t}}
function wrap(){for(const w of document.querySelectorAll(".inkdos-picker"))if(!w.querySelector("select"))w.remove();
for(const id of icons){const s=document.getElementById(id);if(s&&s.closest("#formatbar")&&!s.parentElement.classList.contains("inkdos-picker"))box(s,id,false)}
for(const id of values){const s=document.getElementById(id);if(s&&!s.parentElement.classList.contains("inkdos-picker"))box(s,id,true)}label()}
wrap();new MutationObserver(wrap).observe(document.body,{childList:true,subtree:true});
document.addEventListener("change",label,true);document.addEventListener("input",label,true);setInterval(label,500)})();

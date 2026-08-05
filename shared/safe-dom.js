(function(global){
'use strict';
const ALLOWED_TAGS=new Set(['P','H1','H2','H3','H4','H5','H6','SPAN','BR','IMG','TABLE','THEAD','TBODY','TFOOT','TR','TD','TH','UL','OL','LI','DIV']);
const ALLOWED_CLASSES=new Set(['doc-list','list-label','hyperlink','tracked-insert','tracked-delete','content-control','content-control-block']);
const DATA_ATTRS=new Set(['data-docx-rel-id','data-docx-tracked','data-docx-content-control','data-list-num-id','data-list-level','data-list-format']);
const STYLE_PROPS=new Set(['font-family','font-size','font-weight','font-style','text-decoration','color','background-color','text-align','line-height','margin-left','margin-right','text-indent','width','min-width','max-width','height','min-height','vertical-align','white-space','table-layout','border-collapse','border-top','border-right','border-bottom','border-left','padding-top','padding-right','padding-bottom','padding-left','margin-top','margin-bottom']);
const SAFE_IMAGE_DATA=/^data:image\/(?:png|jpeg|gif|webp);base64,[a-z0-9+/=\s]+$/i;
function safeImageUrl(value){const url=String(value||'').trim();return url.startsWith('blob:')||SAFE_IMAGE_DATA.test(url)?url:''}
function safeStyle(value){const out=[];for(const declaration of String(value||'').split(';')){const pos=declaration.indexOf(':');if(pos<1)continue;const prop=declaration.slice(0,pos).trim().toLowerCase(),val=declaration.slice(pos+1).trim();if(!STYLE_PROPS.has(prop)||!val||/[<>{}]|url\s*\(|expression\s*\(|@import|javascript:/i.test(val))continue;if(prop==='font-family'&&!/^[\w\s,'".-]+$/.test(val))continue;if(['color','background-color'].includes(prop)&&!/^(?:#[0-9a-f]{3,8}|rgba?\([\d\s.,%]+\)|[a-z]{1,20})$/i.test(val))continue;if(/^border-(?:top|right|bottom|left)$/.test(prop)&&!/^(?:none|\d+(?:\.\d+)?px\s+(?:solid|dashed|dotted|double)\s+(?:#[0-9a-f]{3,8}|rgba?\([\d\s.,%]+\)|[a-z]{1,20}))$/i.test(val))continue;if(['width','min-width','max-width','height','min-height','font-size','margin-left','margin-right','margin-top','margin-bottom','text-indent','padding-top','padding-right','padding-bottom','padding-left'].includes(prop)&&!/^\d+(?:\.\d+)?(?:px|pt|em|rem|%)$/.test(val))continue;out.push(prop+':'+val)}return out.join(';')}
function copyNode(node,doc){if(node.nodeType===Node.TEXT_NODE)return doc.createTextNode(node.nodeValue||'');if(node.nodeType!==Node.ELEMENT_NODE)return doc.createDocumentFragment();const tag=node.tagName.toUpperCase();if(!ALLOWED_TAGS.has(tag)){const frag=doc.createDocumentFragment();for(const child of Array.from(node.childNodes))frag.appendChild(copyNode(child,doc));return frag}const el=doc.createElement(tag.toLowerCase());
  const classes=String(node.getAttribute('class')||'').split(/\s+/).filter(x=>ALLOWED_CLASSES.has(x));if(classes.length)el.className=classes.join(' ');
  for(const name of DATA_ATTRS)if(node.hasAttribute(name))el.setAttribute(name,String(node.getAttribute(name)).slice(0,256));
  if((tag==='TD'||tag==='TH')&&node.hasAttribute('colspan')){const n=Math.max(1,Math.min(100,Number(node.getAttribute('colspan'))||1));el.colSpan=n}
  if((tag==='TD'||tag==='TH')&&node.hasAttribute('rowspan')){const n=Math.max(1,Math.min(100,Number(node.getAttribute('rowspan'))||1));el.rowSpan=n}
  if(node.getAttribute('contenteditable')==='false')el.contentEditable='false';
  const style=safeStyle(node.getAttribute('style'));if(style)el.setAttribute('style',style);
  if(tag==='IMG'){const src=safeImageUrl(node.getAttribute('src'));if(!src)return doc.createTextNode('[Unsupported image removed]');el.src=src;el.alt=String(node.getAttribute('alt')||'Embedded image').slice(0,256);el.referrerPolicy='no-referrer';el.decoding='async'}
  for(const child of Array.from(node.childNodes))el.appendChild(copyNode(child,doc));return el
}
function fragmentFromHtml(html,doc=document){const template=doc.createElement('template');template.innerHTML=String(html||'');const fragment=doc.createDocumentFragment();for(const child of Array.from(template.content.childNodes))fragment.appendChild(copyNode(child,doc));return fragment}
function appendSanitizedHtml(target,html){target.appendChild(fragmentFromHtml(html,target.ownerDocument||document));return target}
global.InkDeskSafeDOM=Object.freeze({appendSanitizedHtml,fragmentFromHtml,safeImageUrl,safeStyle});
})(window);

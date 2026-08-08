(function(global){
'use strict';
const EMU_PER_CSS_PIXEL=9525;
const PT_TO_CSS_PIXEL=96/72;
const R_NS='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
function descendants(root,name){
  if(!root)return [];
  return Array.from(root.getElementsByTagName('*')).filter(node=>node.localName===name);
}
function first(root,name){return descendants(root,name)[0]||null}
function finite(value){const n=Number(value);return Number.isFinite(n)?n:0}
function positive(value){const n=finite(value);return n>0?n:0}
function round(value){return Math.round(value*1000)/1000}
function emuToPx(value){return round(finite(value)/EMU_PER_CSS_PIXEL)}
function pointToPx(value){return round(finite(value)*PT_TO_CSS_PIXEL)}
function attrR(node,name){
  if(!node)return'';
  return node.getAttributeNS(R_NS,name)||node.getAttribute('r:'+name)||node.getAttribute(name)||'';
}
function normalPath(base,target){
  if(String(target||'').startsWith('/'))return target.slice(1);
  const output=[];
  for(const bit of (base+'/'+target).split('/')){
    if(!bit||bit==='.')continue;
    if(bit==='..')output.pop();else output.push(bit);
  }
  return output.join('/');
}
function parseXml(bytes){
  const text=new TextDecoder('utf-8').decode(bytes);
  return new DOMParser().parseFromString(text,'application/xml');
}
function parseRels(doc){
  const output={};
  for(const rel of descendants(doc,'Relationship'))output[rel.getAttribute('Id')]=rel.getAttribute('Target');
  return output;
}
function relsPath(path){
  const bits=String(path||'').split('/');
  const name=bits.pop();
  return bits.concat(['_rels',name+'.rels']).join('/');
}
function mediaMime(path){
  const ext=String(path||'').split('.').pop().toLowerCase();
  if(ext==='png')return'image/png';
  if(ext==='gif')return'image/gif';
  if(ext==='svg')return'image/svg+xml';
  return'image/jpeg';
}
function mediaUrl(files,path,mediaUrls,key){
  if(!path||!files.has(path))return'';
  const cacheKey=key||path;
  if(mediaUrls[cacheKey])return mediaUrls[cacheKey];
  const blob=new Blob([files.get(path)],{type:mediaMime(path)});
  const url=URL.createObjectURL(blob);
  mediaUrls[cacheKey]=url;
  return url;
}
function positionDescriptor(anchor,axis){
  const name=axis==='x'?'positionH':'positionV';
  const node=first(anchor,name);
  const fallback=axis==='x'?'column':'paragraph';
  if(!node)return{relativeFrom:fallback,offsetPx:0,align:''};
  const offset=first(node,'posOffset');
  const align=first(node,'align');
  return{
    relativeFrom:node.getAttribute('relativeFrom')||fallback,
    offsetPx:emuToPx(offset&&offset.textContent),
    align:String(align&&align.textContent||'')
  };
}
function imageLayout(drawing,context){
  const extent=first(drawing,'extent')||first(drawing,'ext');
  const cx=positive(extent&&extent.getAttribute('cx'));
  const cy=positive(extent&&extent.getAttribute('cy'));
  if(!cx||!cy)return{style:'',anchored:false};
  const width=emuToPx(cx);
  const height=emuToPx(cy);
  const base=[
    'width:'+width+'px',
    'height:'+height+'px',
    'aspect-ratio:'+cx+' / '+cy,
    'object-fit:contain'
  ];
  const anchor=descendants(drawing,'anchor')[0]||null;
  if(!anchor){
    base.push('max-width:100%');
    return{style:base.join(';')+';',anchored:false,widthPx:width,heightPx:height};
  }
  const horizontal=positionDescriptor(anchor,'x');
  const vertical=positionDescriptor(anchor,'y');
  const paragraphLeftPx=finite(context&&context.paragraphLeftPx);
  const localLeft=horizontal.relativeFrom==='column'
    ? horizontal.offsetPx-paragraphLeftPx
    : horizontal.offsetPx;
  base.push('position:absolute','margin:0','max-width:none');
  base.push('left:'+round(localLeft)+'px','top:'+vertical.offsetPx+'px');
  return{
    style:base.join(';')+';',
    anchored:true,
    widthPx:width,
    heightPx:height,
    horizontal,
    vertical,
    behindDoc:anchor.getAttribute('behindDoc')==='1'
  };
}
function stylePointValue(style,name){
  const escaped=name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const pattern=new RegExp('(?:^|;)\\s*'+escaped+'\\s*:\\s*(-?[0-9.]+)pt','i');
  const match=String(style||'').match(pattern);
  return match?pointToPx(match[1]):0;
}
function vmlImageLayout(shape){
  if(!shape)return null;
  const style=shape.getAttribute('style')||'';
  const widthPx=stylePointValue(style,'width');
  const heightPx=stylePointValue(style,'height');
  if(!widthPx||!heightPx)return null;
  return{
    leftPx:stylePointValue(style,'margin-left'),
    topPx:stylePointValue(style,'margin-top'),
    widthPx,
    heightPx,
    horizontalRelative:/mso-position-horizontal-relative\s*:\s*page/i.test(style)?'page':'margin',
    verticalRelative:/mso-position-vertical-relative\s*:\s*page/i.test(style)?'page':'margin'
  };
}
function referenceNode(sect,kind){
  const nodes=descendants(sect,kind+'Reference');
  return nodes.find(node=>(node.getAttribute('w:type')||node.getAttribute('type')||'default')==='default')||nodes[0]||null;
}
function partSpec(sect,kind,rels,root,files,mediaUrls){
  const ref=referenceNode(sect,kind);
  const rid=attrR(ref,'id');
  const target=rid&&rels[rid];
  if(!target)return{text:'',artwork:[]};
  const path=normalPath(root,target);
  const bytes=files.get(path);
  if(!bytes)return{text:'',artwork:[]};
  const doc=parseXml(bytes);
  const relationshipBytes=files.get(relsPath(path));
  const partRels=relationshipBytes?parseRels(parseXml(relationshipBytes)):{};
  const artwork=[];
  for(const pict of descendants(doc,'pict')){
    const shape=first(pict,'shape');
    const image=first(pict,'imagedata');
    const mediaRid=attrR(image,'id');
    const mediaTarget=mediaRid&&partRels[mediaRid];
    const layout=vmlImageLayout(shape);
    if(!mediaTarget||!layout)continue;
    const base=path.split('/').slice(0,-1).join('/');
    const mediaPath=normalPath(base,mediaTarget);
    const src=mediaUrl(files,mediaPath,mediaUrls,'part:'+path+':'+mediaRid);
    if(!src)continue;
    const watermark=/watermark/i.test(String(shape&&shape.getAttribute('id')||''));
    artwork.push(Object.assign({src,opacity:watermark?.13:1},layout));
  }
  const text=descendants(doc,'t').map(node=>node.textContent||'').join('').trim();
  return{text,artwork};
}
function installStyles(){
  if(document.getElementById('inkdesk-docx-floating-layout'))return;
  const style=document.createElement('style');
  style.id='inkdesk-docx-floating-layout';
  style.textContent=[
    '.page{isolation:isolate}',
    '.page-content{position:relative;z-index:1}',
    '.page .has-docx-anchor{position:relative;min-height:0}',
    '.page img.docx-anchored-image{margin:0;max-width:none}',
    '.page-watermark{position:absolute;z-index:0;display:block;object-fit:contain;pointer-events:none;user-select:none;-webkit-user-select:none}'
  ].join('');
  document.head.appendChild(style);
}
function appendPageArtwork(page,spec){
  installStyles();
  const artwork=[];
  if(Array.isArray(spec&&spec.headerArtwork))artwork.push(...spec.headerArtwork);
  if(Array.isArray(spec&&spec.footerArtwork))artwork.push(...spec.footerArtwork);
  for(const item of artwork){
    if(!item||!item.src)continue;
    const img=document.createElement('img');
    img.className='page-watermark';
    img.contentEditable='false';
    img.alt='';
    img.src=item.src;
    const leftBase=item.horizontalRelative==='page'?0:finite(spec.marginLeftPx);
    const topBase=item.verticalRelative==='page'?0:finite(spec.marginTopPx);
    img.style.left=round(leftBase+finite(item.leftPx))+'px';
    img.style.top=round(topBase+finite(item.topPx))+'px';
    img.style.width=finite(item.widthPx)+'px';
    img.style.height=finite(item.heightPx)+'px';
    img.style.opacity=String(Number.isFinite(Number(item.opacity))?Number(item.opacity):1);
    page.appendChild(img);
  }
}
installStyles();
global.InkDeskDocumentDrawingLayout={
  appendPageArtwork,
  emuToPx,
  imageLayout,
  partSpec,
  pointToPx,
  vmlImageLayout
};
})(window);

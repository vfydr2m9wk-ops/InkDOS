(function(global){
'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
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
function parseXml(bytes){const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);if(/<!DOCTYPE|<!ENTITY/i.test(text))throw new Error('Unsafe XML declaration in DOCX part');const doc=new DOMParser().parseFromString(text,'application/xml');if(doc.getElementsByTagName('parsererror').length)throw new Error('Invalid DOCX XML part');return doc}

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
// A picture inside a VML group is placed in the group's coordinate space (coordsize/coordorigin), which
// the group's own style maps onto the page.
function vmlInFallback(node){for(let n=node&&node.parentNode;n;n=n.parentNode)if(n.localName==='Fallback')return true;return false}
function vmlGroupOf(shape){for(let n=shape&&shape.parentNode;n;n=n.parentNode){if(n.localName==='group')return n;if(n.localName==='pict')return null}return null}
function vmlNumber(style,name){const m=new RegExp('(?:^|;)\\s*'+name+'\\s*:\\s*(-?[\\d.]+)','i').exec(style||'');return m?Number(m[1]):0}
function vmlGroupChildLayout(group,shape){const outer=vmlImageLayout(group);if(!outer||!shape)return null;const pair=(v,d)=>{const p=String(v||'').split(',').map(Number);return[Number.isFinite(p[0])&&p[0]?p[0]:d[0],Number.isFinite(p[1])&&p[1]?p[1]:d[1]]},[cw,ch]=pair(group.getAttribute('coordsize'),[1000,1000]),origin=String(group.getAttribute('coordorigin')||'0,0').split(',').map(x=>Number(x)||0),style=shape.getAttribute('style')||'',sx=outer.widthPx/cw,sy=outer.heightPx/ch,w=vmlNumber(style,'width')*sx,h=vmlNumber(style,'height')*sy;if(!(w>0&&h>0))return null;return Object.assign({},outer,{leftPx:outer.leftPx+(vmlNumber(style,'left')-origin[0])*sx,topPx:outer.topPx+(vmlNumber(style,'top')-(origin[1]||0))*sy,widthPx:w,heightPx:h})}
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
function drawingImageLayout(drawing){
  if(!drawing)return null;
  const anchor=descendants(drawing,'anchor')[0]||null;
  const inline=descendants(drawing,'inline')[0]||null;
  const host=anchor||inline;
  if(!host)return null;
  const extent=first(host,'extent')||first(drawing,'ext');
  const cx=positive(extent&&extent.getAttribute('cx'));
  const cy=positive(extent&&extent.getAttribute('cy'));
  if(!cx||!cy)return null;
  const widthPx=emuToPx(cx),heightPx=emuToPx(cy);
  if(!anchor)return{
    leftPx:0,topPx:0,widthPx,heightPx,
    horizontalRelative:'margin',verticalRelative:'paragraph',
    horizontalAlign:'',verticalAlign:'',behindDoc:false
  };
  const horizontal=positionDescriptor(anchor,'x');
  const vertical=positionDescriptor(anchor,'y');
  return{
    leftPx:horizontal.offsetPx,
    topPx:vertical.offsetPx,
    widthPx,
    heightPx,
    horizontalRelative:horizontal.relativeFrom,
    verticalRelative:vertical.relativeFrom,
    horizontalAlign:horizontal.align,
    verticalAlign:vertical.align,
    behindDoc:anchor.getAttribute('behindDoc')==='1'
  };
}
function referenceNode(sect,kind,type){
  const nodes=descendants(sect,kind+'Reference');
  if(type)return nodes.find(node=>(node.getAttribute('w:type')||node.getAttribute('type')||'default')===type)||null;
  const kindOf=node=>node.getAttribute('w:type')||node.getAttribute('type')||'default';
  return nodes.find(node=>kindOf(node)==='default')||nodes.find(node=>kindOf(node)!=='first')||null;
}
function partSpec(sect,kind,rels,root,files,mediaUrls,type){
  const ref=referenceNode(sect,kind,type);
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
  // VML pictures; a compatibility fallback repeats a DrawingML picture already placed below, so it is skipped.
  for(const image of descendants(doc,'imagedata').filter(x=>descendants(doc,'pict').some(p=>p.contains(x))&&!vmlInFallback(x))){
    const shape=image.parentNode&&image.parentNode.localName==='shape'?image.parentNode:null;
    const mediaRid=attrR(image,'id');
    const mediaTarget=mediaRid&&partRels[mediaRid];
    const group=vmlGroupOf(shape);
    const layout=group?vmlGroupChildLayout(group,shape):vmlImageLayout(shape);
    if(!mediaTarget||!layout)continue;
    const base=path.split('/').slice(0,-1).join('/');
    const mediaPath=normalPath(base,mediaTarget);
    const src=mediaUrl(files,mediaPath,mediaUrls,'part:'+path+':'+mediaRid);
    if(!src)continue;
    const watermark=/watermark/i.test(String(shape&&shape.getAttribute('id')||''));
    artwork.push(Object.assign({src,opacity:watermark?.13:1,partKind:kind},layout));
  }
  for(const drawing of descendants(doc,'drawing')){
    const blip=first(drawing,'blip');
    const mediaRid=attrR(blip,'embed');
    const mediaTarget=mediaRid&&partRels[mediaRid];
    const layout=drawingImageLayout(drawing);
    if(!mediaTarget||!layout)continue;
    const base=path.split('/').slice(0,-1).join('/');
    const mediaPath=normalPath(base,mediaTarget);
    const src=mediaUrl(files,mediaPath,mediaUrls,'part:'+path+':'+mediaRid);
    if(!src)continue;
    artwork.push(Object.assign({src,opacity:1,partKind:kind},layout));
  }
  const text=descendants(doc,'t').filter(node=>!vmlInFallback(node)).map(node=>node.textContent||'').join('').trim();
  return{text,artwork};
}
function installStyles(){
  if(document.getElementById('inkdos2-documents-floating-layout'))return;
  const style=document.createElement('style');
  style.id='inkdos2-documents-floating-layout';
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
    const width=finite(item.widthPx),height=finite(item.heightPx);
    const pageWidth=finite(spec.widthPx),pageHeight=finite(spec.heightPx);
    const marginLeft=finite(spec.marginLeftPx),marginRight=finite(spec.marginRightPx);
    const marginTop=finite(spec.marginTopPx),marginBottom=finite(spec.marginBottomPx);
    const leftBase=item.horizontalRelative==='page'?0:marginLeft;
    const areaWidth=item.horizontalRelative==='page'?pageWidth:Math.max(0,pageWidth-marginLeft-marginRight);
    let left=leftBase+finite(item.leftPx);
    if(item.horizontalAlign==='center')left=leftBase+Math.max(0,(areaWidth-width)/2);
    else if(item.horizontalAlign==='right')left=leftBase+Math.max(0,areaWidth-width);
    const footerRelative=item.partKind==='footer'&&item.verticalRelative!=='page';
    const topBase=item.verticalRelative==='page'?0:(footerRelative?Math.max(0,pageHeight-marginBottom-height):marginTop);
    let top=topBase+finite(item.topPx);
    if(item.verticalAlign==='center'&&item.verticalRelative==='page')top=Math.max(0,(pageHeight-height)/2);
    else if(item.verticalAlign==='bottom'&&item.verticalRelative==='page')top=Math.max(0,pageHeight-height);
    img.style.left=round(left)+'px';
    img.style.top=round(top)+'px';
    img.style.width=width+'px';
    img.style.height=height+'px';
    img.style.opacity=String(Number.isFinite(Number(item.opacity))?Number(item.opacity):1);
    page.appendChild(img);
  }
}
installStyles();
NS.DrawingLayout={
  appendPageArtwork,
  emuToPx,
  imageLayout,
  drawingImageLayout,
  partSpec,
  pointToPx,
  vmlImageLayout
};
})(globalThis);

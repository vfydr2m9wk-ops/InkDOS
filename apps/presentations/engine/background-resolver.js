(function(global){
'use strict';
function all(root,name){
  if(!root)return [];
  return Array.from(root.getElementsByTagName('*')).filter(node=>node.localName===name);
}
function first(root,name){return all(root,name)[0]||null}
function attr(node,name,fallback=''){return node?node.getAttribute(name)||fallback:fallback}
function normalizePath(base,target){
  const out=[];
  for(const part of String(base+'/'+target).split('/')){
    if(!part||part==='.')continue;
    if(part==='..')out.pop();else out.push(part);
  }
  return out.join('/');
}
function mimeFor(path){
  const ext=String(path||'').split('.').pop().toLowerCase();
  if(ext==='png')return'image/png';
  if(ext==='jpg'||ext==='jpeg')return'image/jpeg';
  if(ext==='gif')return'image/gif';
  if(ext==='svg')return'image/svg+xml';
  return'image/'+ext;
}
function imageDimensions(data,ext){
  try{
    if(ext==='png'&&data.length>24){
      return{w:(data[16]<<24)|(data[17]<<16)|(data[18]<<8)|data[19],h:(data[20]<<24)|(data[21]<<16)|(data[22]<<8)|data[23]};
    }
    if(ext==='jpg'||ext==='jpeg'){
      let i=2;
      while(i+9<data.length){
        if(data[i]!==0xff){i++;continue}
        const marker=data[i+1],len=(data[i+2]<<8)+data[i+3];
        if([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker)){
          return{h:(data[i+5]<<8)+data[i+6],w:(data[i+7]<<8)+data[i+8]};
        }
        i+=Math.max(2,len+2);
      }
    }
  }catch(_){return{w:16,h:9}}
  return{w:16,h:9};
}
async function directImage(zip,source,bg){
  const fill=first(bg,'blipFill');
  if(!fill)return null;
  const blip=first(fill,'blip');
  const rid=blip&&(blip.getAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships','embed')||attr(blip,'r:embed'));
  const target=rid&&source.rmap&&source.rmap[rid];
  if(!target||!source.path)return null;
  const mediaPath=normalizePath(source.path.split('/').slice(0,-1).join('/'),target),file=zip.file(mediaPath);
  if(!file)return null;
  const ext=mediaPath.split('.').pop().toLowerCase();
  const data=await file.async('uint8array');
  const src='data:'+mimeFor(mediaPath)+';base64,'+await file.async('base64');
  const tile=first(fill,'tile');
  if(tile){
    const dim=imageDimensions(data,ext),sx=Math.max(.01,+attr(tile,'sx','100000')/100000),sy=Math.max(.01,+attr(tile,'sy','100000')/100000);
    return{color:'#ffffff',image:'url("'+src+'")',repeat:'repeat',size:Math.max(1,dim.w*sx)+'px '+Math.max(1,dim.h*sy)+'px'};
  }
  return{color:'#ffffff',image:'url("'+src+'")',repeat:'no-repeat',size:'100% 100%'};
}
async function resolve(options){
  const zip=options.zip,theme=options.theme||{},sources=options.sources||[];
  const colorFromNode=options.colorFromNode,rgbaColor=options.rgbaColor;
  for(const source of sources){
    const xml=source&&source.xml;
    if(!xml)continue;
    const bg=first(xml,'bg');
    if(!bg)continue;
    const direct=await directImage(zip,source,bg);
    if(direct)return direct;
    const ref=first(bg,'bgRef');
    if(ref){
      const idx=+attr(ref,'idx','0'),color=colorFromNode?colorFromNode(ref,'#ffffff'):'#ffffff';
      const fill=theme.backgroundFills&&theme.backgroundFills[idx>=1000?idx-1000:idx];
      if(fill&&fill.type==='image'&&fill.src){
        const veil=rgbaColor?rgbaColor(color,.94):color;
        return{color,image:'linear-gradient('+veil+','+veil+'),url("'+fill.src+'")',repeat:fill.tile?'repeat':'no-repeat',size:fill.tile?(fill.tileWidth+'px '+fill.tileHeight+'px'):'cover'};
      }
      return{color};
    }
    return{color:colorFromNode?colorFromNode(bg,'#ffffff'):'#ffffff'};
  }
  return{color:'#ffffff'};
}
global.InkDOSPresentationsBackground={resolve};
})(window);

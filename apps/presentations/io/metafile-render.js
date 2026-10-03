(function(global){
'use strict';
// EMF / WMF -> SVG for pictures embedded in legacy presentations (charts, equations and OLE previews are stored as
// metafiles). Covers the GDI drawing subset Office previews use: pens, brushes, fonts, world/window mapping, lines,
// polygons, Béziers, rectangles, ellipses, paths, text and DIB bitmaps. Unknown records are skipped; EMF+ comments are
// ignored because dual EMF files carry the GDI fallback. Returns an SVG string or null.
const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
const MAX_RECORDS=200000,MAX_ITEMS=60000;
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
const rgb=c=>'#'+[c&255,(c>>>8)&255,(c>>>16)&255].map(v=>v.toString(16).padStart(2,'0')).join('');
const n2=v=>Math.round(v*100)/100;
function b64(bytes){let s='';for(let i=0;i<bytes.length;i+=0x8000)s+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));return btoa(s)}
// DIB (BITMAPINFO + bits) -> BMP file bytes, which browsers display natively.
function dibToBmp(bmi,bits){const hdr=bmi.length>=4?new DataView(bmi.buffer,bmi.byteOffset,bmi.byteLength).getUint32(0,true):40;const total=14+bmi.length+bits.length,out=new Uint8Array(total),dv=new DataView(out.buffer);out[0]=0x42;out[1]=0x4d;dv.setUint32(2,total,true);dv.setUint32(10,14+bmi.length,true);out.set(bmi,14);out.set(bits,14+bmi.length);return hdr?out:null}
function dibFromPacked(bytes){if(bytes.length<40)return null;const dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),size=dv.getUint32(0,true);if(size<12||size>124)return null;const bpp=size===12?dv.getUint16(10,true):dv.getUint16(14,true),clr=size>=40?dv.getUint32(32,true):0,comp=size>=40?dv.getUint32(16,true):0,masks=comp===3&&size===40?12:0,pal=bpp<=8?(clr||1<<bpp)*(size===12?3:4):0,head=size+masks+pal;if(head>bytes.length)return null;return dibToBmp(bytes.subarray(0,head),bytes.subarray(head))}
function bmpDataUrl(bmp){return bmp?'data:image/bmp;base64,'+b64(bmp):null}

function Canvas(){
 const items=[];let st={pen:{color:'#000000',width:1,none:false},brush:{color:'#ffffff',none:false},font:{size:12,family:'Arial',weight:400,italic:false,underline:false,angle:0},textColor:'#000000',textAlign:0,fillRule:'evenodd',xf:[1,0,0,1,0,0],cur:[0,0],win:null,vp:null};
 const stack=[],P=(x,y)=>{const m=st.xf;return [m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]};
 const stroke=()=>st.pen.none?'stroke="none"':`stroke="${st.pen.color}" stroke-width="${n2(Math.max(st.pen.width,0.5))}" stroke-linejoin="round" vector-effect="non-scaling-stroke"`;
 const fill=()=>st.brush.none?'fill="none"':`fill="${st.brush.color}"`;
 const push=s=>{if(items.length<MAX_ITEMS)items.push(s)};
 let path=null;
 return {
  get st(){return st},set st(v){st=v},
  save(){stack.push(JSON.parse(JSON.stringify(st)))},restore(){if(stack.length)st=stack.pop()},
  P,
  poly(pts,closed,mode){if(pts.length<2)return;const d=pts.map(([x,y],i)=>{const [a,b]=P(x,y);return (i?'L':'M')+n2(a)+' '+n2(b)}).join('')+(closed?'Z':'');if(path!==null){path+=d;return}push(`<path d="${d}" ${mode==='stroke'?'fill="none"':fill()} ${stroke()} fill-rule="${st.fillRule}"/>`)},
  bezier(pts,start){if(pts.length<3)return;let d='';if(start){const [a,b]=P(...start);d='M'+n2(a)+' '+n2(b)}for(let i=0;i+2<pts.length;i+=3){const q=[pts[i],pts[i+1],pts[i+2]].map(p=>P(p[0],p[1]).map(n2).join(' '));d+='C'+q.join(' ')}if(path!==null){path+=d;return}push(`<path d="${d}" fill="none" ${stroke()}/>`)},
  rect(l,t,r,b,rx=0,ry=0){const [x1,y1]=P(l,t),[x2,y2]=P(r,b);if(path!==null){path+=`M${n2(x1)} ${n2(y1)}H${n2(x2)}V${n2(y2)}H${n2(x1)}Z`;return}push(`<rect x="${n2(Math.min(x1,x2))}" y="${n2(Math.min(y1,y2))}" width="${n2(Math.abs(x2-x1))}" height="${n2(Math.abs(y2-y1))}" rx="${n2(rx)}" ry="${n2(ry)}" ${fill()} ${stroke()}/>`)},
  ellipse(l,t,r,b){const [x1,y1]=P(l,t),[x2,y2]=P(r,b);push(`<ellipse cx="${n2((x1+x2)/2)}" cy="${n2((y1+y2)/2)}" rx="${n2(Math.abs(x2-x1)/2)}" ry="${n2(Math.abs(y2-y1)/2)}" ${fill()} ${stroke()}/>`)},
  moveTo(x,y){st.cur=[x,y];if(path!==null){const [a,b]=P(x,y);path+=`M${n2(a)} ${n2(b)}`}},
  lineTo(x,y){const [a,b]=P(x,y);if(path!==null)path+=`L${n2(a)} ${n2(b)}`;else{const [c,d]=P(...st.cur);push(`<path d="M${n2(c)} ${n2(d)}L${n2(a)} ${n2(b)}" fill="none" ${stroke()}/>`)}st.cur=[x,y]},
  beginPath(){path=''},closeFigure(){if(path!==null)path+='Z'},endPath(){},
  drawPath(mode){if(path){push(`<path d="${path}" ${mode==='stroke'?'fill="none"':fill()} ${mode==='fill'?'stroke="none"':stroke()} fill-rule="${st.fillRule}"/>`)}path=null},
  text(x,y,str){if(!str)return;const f=st.font,[a,b]=P(x,y),sy=Math.hypot(st.xf[2],st.xf[3])||1,size=Math.abs(f.size)*sy,al=st.textAlign,anchor=(al&6)===6?'middle':(al&2)?'end':'start',base=(al&24)===24?'':(al&8)?' dominant-baseline="text-after-edge"':' dominant-baseline="text-before-edge"';push(`<text x="${n2(a)}" y="${n2(b)}" font-family="${esc(f.family)}, Arial, sans-serif" font-size="${n2(size)}" font-weight="${f.weight}"${f.italic?' font-style="italic"':''}${f.underline?' text-decoration="underline"':''} fill="${st.textColor}" text-anchor="${anchor}"${base}${f.angle?` transform="rotate(${n2(-f.angle)} ${n2(a)} ${n2(b)})"`:''} xml:space="preserve">${esc(str)}</text>`)},
  image(x,y,w,h,url){if(!url)return;const [a,b]=P(x,y),[c,d]=P(x+w,y+h);push(`<image x="${n2(Math.min(a,c))}" y="${n2(Math.min(b,d))}" width="${n2(Math.abs(c-a))}" height="${n2(Math.abs(d-b))}" preserveAspectRatio="none" href="${url}"/>`)},
  items
 }}

function emf(bytes){const dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),len=bytes.length;if(len<88||dv.getUint32(0,true)!==1||dv.getUint32(40,true)!==0x464d4520)return null;
 const i32=o=>dv.getInt32(o,true),u32=o=>dv.getUint32(o,true),i16=o=>dv.getInt16(o,true),f32=o=>dv.getFloat32(o,true);
 const bounds=[i32(8),i32(12),i32(16),i32(20)],cv=Canvas(),objs=[];let p=0,n=0,viewBox=null;
 const stock=ih=>{const k=ih&0x7fffffff,s=cv.st;if(k===0)s.brush={color:'#ffffff',none:false};else if(k===1)s.brush={color:'#c0c0c0',none:false};else if(k===2)s.brush={color:'#808080',none:false};else if(k===3)s.brush={color:'#404040',none:false};else if(k===4)s.brush={color:'#000000',none:false};else if(k===5)s.brush={color:'#ffffff',none:true};else if(k===6)s.pen={color:'#ffffff',width:1,none:false};else if(k===7)s.pen={color:'#000000',width:1,none:false};else if(k===8)s.pen={color:'#000000',width:1,none:true}};
 const pts16=(o,c)=>{const a=[];for(let i=0;i<c&&o+i*4+4<=len;i++)a.push([i16(o+i*4),i16(o+i*4+2)]);return a},pts32=(o,c)=>{const a=[];for(let i=0;i<c&&o+i*8+8<=len;i++)a.push([i32(o+i*8),i32(o+i*8+4)]);return a};
 const dib=(rec,offBmi,cbBmi,offBits,cbBits)=>{if(!cbBmi||rec+offBmi+cbBmi>len||rec+offBits+cbBits>len)return null;return bmpDataUrl(dibToBmp(bytes.subarray(rec+offBmi,rec+offBmi+cbBmi),bytes.subarray(rec+offBits,rec+offBits+cbBits)))};
 while(p+8<=len&&n++<MAX_RECORDS){const type=u32(p),size=u32(p+4);if(size<8||p+size>len)break;const o=p+8,s=cv.st;
  switch(type){
   case 9:s.win=s.win||{};s.win.ex=[i32(o),i32(o+4)];break;case 10:s.win=s.win||{};s.win.org=[i32(o),i32(o+4)];break;
   case 11:s.vp=s.vp||{};s.vp.ex=[i32(o),i32(o+4)];break;case 12:s.vp=s.vp||{};s.vp.org=[i32(o),i32(o+4)];break;
   case 35:s.xf=[f32(o),f32(o+4),f32(o+8),f32(o+12),f32(o+16),f32(o+20)];break;
   case 36:{const m=[f32(o),f32(o+4),f32(o+8),f32(o+12),f32(o+16),f32(o+20)],mode=u32(o+24),a=s.xf;if(mode===1)s.xf=[1,0,0,1,0,0];else if(mode===2)s.xf=[m[0]*a[0]+m[1]*a[2],m[0]*a[1]+m[1]*a[3],m[2]*a[0]+m[3]*a[2],m[2]*a[1]+m[3]*a[3],m[4]*a[0]+m[5]*a[2]+a[4],m[4]*a[1]+m[5]*a[3]+a[5]];else if(mode===3)s.xf=[a[0]*m[0]+a[1]*m[2],a[0]*m[1]+a[1]*m[3],a[2]*m[0]+a[3]*m[2],a[2]*m[1]+a[3]*m[3],a[4]*m[0]+a[5]*m[2]+m[4],a[4]*m[1]+a[5]*m[3]+m[5]];else if(mode===4)s.xf=m;break}
   case 33:cv.save();break;case 34:cv.restore();break;
   case 19:s.fillRule=u32(o)===2?'nonzero':'evenodd';break;case 24:s.textColor=rgb(u32(o));break;case 22:s.textAlign=u32(o);break;
   case 38:objs[u32(o)]={k:'pen',v:{color:rgb(u32(o+16)),width:Math.max(1,i32(o+8)),none:(u32(o+4)&15)===5}};break;
   case 95:objs[u32(o)]={k:'pen',v:{color:rgb(u32(o+32)),width:Math.max(1,u32(o+24)),none:(u32(o+20)&15)===5}};break;
   case 39:objs[u32(o)]={k:'brush',v:{color:rgb(u32(o+8)),none:u32(o+4)===1}};break;
   case 82:{const face=[];for(let i=0;i<32;i++){const c=dv.getUint16(o+32+i*2,true);if(!c)break;face.push(c)}objs[u32(o)]={k:'font',v:{size:Math.abs(i32(o+4))||12,family:String.fromCharCode(...face)||'Arial',weight:i32(o+20)||400,italic:!!bytes[o+24],underline:!!bytes[o+25],angle:i32(o+12)/10}};break}
   case 37:{const ih=u32(o);if(ih&0x80000000)stock(ih);else{const ob=objs[ih];if(ob)s[ob.k]=JSON.parse(JSON.stringify(ob.v))}break}
   case 40:delete objs[u32(o)];break;
   case 27:cv.moveTo(i32(o),i32(o+4));break;case 54:cv.lineTo(i32(o),i32(o+4));break;
   case 43:cv.rect(i32(o),i32(o+4),i32(o+8),i32(o+12));break;case 44:cv.rect(i32(o),i32(o+4),i32(o+8),i32(o+12),i32(o+16)/2,i32(o+20)/2);break;
   case 42:cv.ellipse(i32(o),i32(o+4),i32(o+8),i32(o+12));break;
   case 3:cv.poly(pts32(o+20,u32(o+16)),true);break;case 4:cv.poly(pts32(o+20,u32(o+16)),false,'stroke');break;
   case 86:cv.poly(pts16(o+20,u32(o+16)),true);break;case 87:cv.poly(pts16(o+20,u32(o+16)),false,'stroke');break;
   case 89:{const a=pts16(o+20,u32(o+16));cv.poly([s.cur,...a],false,'stroke');if(a.length)s.cur=a[a.length-1];break}
   case 85:{const a=pts16(o+20,u32(o+16));cv.bezier(a.slice(1),a[0]);break}
   case 88:{const a=pts16(o+20,u32(o+16));cv.bezier(a,s.cur);if(a.length)s.cur=a[a.length-1];break}
   case 90:case 91:{const np=u32(o+16),counts=[];for(let i=0;i<np;i++)counts.push(u32(o+24+i*4));let q=o+24+np*4;const closed=type===91;if(closed&&np>1){cv.beginPath();for(const c of counts){const a=pts16(q,c);cv.poly(a,true);q+=c*4}cv.drawPath('both')}else for(const c of counts){cv.poly(pts16(q,c),closed,closed?null:'stroke');q+=c*4}break}
   case 59:cv.beginPath();break;case 60:cv.endPath();break;case 61:cv.closeFigure();break;
   case 62:cv.drawPath('fill');break;case 63:cv.drawPath('both');break;case 64:cv.drawPath('stroke');break;
   case 84:{const x=i32(o+28),y=i32(o+32),nc=u32(o+36),off=u32(o+40);let str='';for(let i=0;i<nc&&p+off+i*2+2<=len;i++)str+=String.fromCharCode(dv.getUint16(p+off+i*2,true));cv.text(x,y,str.replace(/\u0000/g,''));break}
   case 81:{const x=i32(o+16),y=i32(o+20),url=dib(p,u32(o+40),u32(o+44),u32(o+48),u32(o+52));cv.image(x,y,i32(o+64),i32(o+68),url);break}
   case 77:{const x=i32(o+16),y=i32(o+20),w=i32(o+24),h=i32(o+28),url=dib(p,u32(o+76),u32(o+80),u32(o+84),u32(o+88));cv.image(x,y,w,h,url);break}
   case 76:{const x=i32(o+16),y=i32(o+20),w=i32(o+24),h=i32(o+28),url=dib(p,u32(o+76),u32(o+80),u32(o+84),u32(o+88));if(url)cv.image(x,y,w,h,url);break}
   case 14:p=len;continue;
  }p+=size}
 // The picture shows the device bounds; with window and viewport mapping (anisotropic/isotropic modes) bring them back to
 // logical units, otherwise use the window, otherwise the bounds as they are.
 const s=cv.st,wo=(s.win&&s.win.org)||[0,0],vo=(s.vp&&s.vp.org)||[0,0],we=s.win&&s.win.ex,ve=s.vp&&s.vp.ex;
 if(we&&ve&&ve[0]&&ve[1]){const L=(d,i)=>(d-vo[i])*we[i]/ve[i]+wo[i],x0=L(bounds[0],0),y0=L(bounds[1],1),x1=L(bounds[2],0),y1=L(bounds[3],1);viewBox=[Math.min(x0,x1),Math.min(y0,y1),Math.max(1,Math.abs(x1-x0)),Math.max(1,Math.abs(y1-y0))]}
 else if(we&&we[0]&&we[1])viewBox=[wo[0],wo[1],we[0],we[1]];
 else viewBox=[bounds[0],bounds[1],Math.max(1,bounds[2]-bounds[0]),Math.max(1,bounds[3]-bounds[1])];
 return cv.items.length?svg(cv.items,viewBox):null}

function wmf(bytes){const dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),len=bytes.length;let p=0,bbox=null;
 const i16=o=>dv.getInt16(o,true),u16=o=>dv.getUint16(o,true),u32=o=>dv.getUint32(o,true);
 if(len>=22&&u32(0)===0x9ac6cdd7){bbox=[i16(6),i16(8),i16(10),i16(12)];p=22}
 if(p+18>len)return null;const hdrWords=u16(p+2);if(hdrWords!==9)return null;p+=18;
 const cv=Canvas(),objs=[];let n=0,win=null;
 const add=ob=>{let i=0;while(objs[i])i++;objs[i]=ob};
 const pts=(o,c)=>{const a=[];for(let i=0;i<c&&o+i*4+4<=len;i++)a.push([i16(o+i*4),i16(o+i*4+2)]);return a};
 while(p+6<=len&&n++<MAX_RECORDS){const words=u32(p),fn=u16(p+4),size=words*2;if(size<6||p+size>len)break;const o=p+6,s=cv.st;
  switch(fn){
   case 0x0000:p=len;continue;
   case 0x020B:win=win||{};win.org=[i16(o+2),i16(o)];break;case 0x020C:win=win||{};win.ex=[i16(o+2),i16(o)];break;
   case 0x001E:cv.save();break;case 0x0127:cv.restore();break;
   case 0x0106:s.fillRule=u16(o)===2?'nonzero':'evenodd';break;case 0x0209:s.textColor=rgb(u32(o));break;case 0x012E:s.textAlign=u16(o);break;
   case 0x02FA:add({k:'pen',v:{color:rgb(u32(o+6)),width:Math.max(1,i16(o+2)),none:(u16(o)&15)===5}});break;
   case 0x02FC:add({k:'brush',v:{color:rgb(u32(o+2)),none:u16(o)===1}});break;
   case 0x02FB:{let face='';for(let i=0;i<32&&o+18+i<p+size;i++){const c=bytes[o+18+i];if(!c)break;face+=String.fromCharCode(c)}add({k:'font',v:{size:Math.abs(i16(o))||12,family:face||'Arial',weight:i16(o+8)||400,italic:!!bytes[o+10],underline:!!bytes[o+11],angle:i16(o+4)/10}});break}
   case 0x00F7:case 0x0142:case 0x06FF:add({k:'other',v:null});break;
   case 0x012D:{const ob=objs[u16(o)];if(ob&&ob.k!=='other')s[ob.k]=JSON.parse(JSON.stringify(ob.v));break}
   case 0x01F0:objs[u16(o)]=undefined;break;
   case 0x0214:cv.moveTo(i16(o+2),i16(o));break;case 0x0213:cv.lineTo(i16(o+2),i16(o));break;
   case 0x041B:cv.rect(i16(o+6),i16(o+4),i16(o+2),i16(o));break;case 0x061C:cv.rect(i16(o+10),i16(o+8),i16(o+6),i16(o+4),i16(o+2)/2,i16(o)/2);break;
   case 0x0418:cv.ellipse(i16(o+6),i16(o+4),i16(o+2),i16(o));break;
   case 0x0324:cv.poly(pts(o+2,u16(o)),true);break;case 0x0325:cv.poly(pts(o+2,u16(o)),false,'stroke');break;
   case 0x0538:{const np=u16(o),counts=[];for(let i=0;i<np;i++)counts.push(u16(o+2+i*2));let q=o+2+np*2;cv.beginPath();for(const c of counts){cv.poly(pts(q,c),true);q+=c*4}cv.drawPath('both');break}
   case 0x0521:{const c=u16(o);let str='';for(let i=0;i<c;i++)str+=String.fromCharCode(bytes[o+2+i]);const q=o+2+c+(c&1);cv.text(i16(q+2),i16(q),str);break}
   case 0x0A32:{const y=i16(o),x=i16(o+2),c=u16(o+4),opt=u16(o+6);let q=o+8+((opt&6)?8:0),str='';for(let i=0;i<c&&q+i<p+size;i++)str+=String.fromCharCode(bytes[q+i]);cv.text(x,y,str);break}
   case 0x0F43:{const yd=i16(o+18),xd=i16(o+20),hd=i16(o+14),wd=i16(o+16);cv.image(xd,yd,wd,hd,bmpDataUrl(dibFromPacked(bytes.subarray(o+22,p+size))));break}
   case 0x0B41:{const yd=i16(o+16),xd=i16(o+18),hd=i16(o+12),wd=i16(o+14);if(size>26)cv.image(xd,yd,wd,hd,bmpDataUrl(dibFromPacked(bytes.subarray(o+20,p+size))));break}
   case 0x0940:{const yd=i16(o+12),xd=i16(o+14),hd=i16(o+8),wd=i16(o+10);if(size>22)cv.image(xd,yd,wd,hd,bmpDataUrl(dibFromPacked(bytes.subarray(o+16,p+size))));break}
  }p+=size}
 const vb=win&&win.ex&&win.ex[0]&&win.ex[1]?[(win.org||[0,0])[0],(win.org||[0,0])[1],win.ex[0],win.ex[1]]:bbox?[bbox[0],bbox[1],Math.max(1,bbox[2]-bbox[0]),Math.max(1,bbox[3]-bbox[1])]:null;
 return cv.items.length&&vb?svg(cv.items,vb):null}

function svg(items,[x,y,w,h]){const fx=w<0?-1:1,fy=h<0?-1:1,W=Math.abs(w),H=Math.abs(h),vx=fx<0?x-W:x,vy=fy<0?y-H:y;return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${n2(vx)} ${n2(vy)} ${n2(W)} ${n2(H)}" preserveAspectRatio="none">${items.join('')}</svg>`}
function toSvg(bytes,kind){try{return kind==='emf'?emf(bytes):kind==='wmf'?wmf(bytes):null}catch(_){return null}}
function svgDataUrl(svgText){return 'data:image/svg+xml;base64,'+b64(new TextEncoder().encode(svgText))}
NS.MetafileRender=Object.freeze({toSvg,svgDataUrl,dibFromPacked,bmpDataUrl});
})(globalThis);

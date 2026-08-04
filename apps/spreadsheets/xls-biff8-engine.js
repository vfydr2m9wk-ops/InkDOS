(function(global){
'use strict';

const FREE=0xFFFFFFFF,END=0xFFFFFFFE;
const DEFAULT_PALETTE=[
  '#000000','#FFFFFF','#FF0000','#00FF00','#0000FF','#FFFF00','#FF00FF','#00FFFF',
  '#800000','#008000','#000080','#808000','#800080','#008080','#C0C0C0','#808080',
  '#9999FF','#993366','#FFFFCC','#CCFFFF','#660066','#FF8080','#0066CC','#CCCCFF',
  '#000080','#FF00FF','#FFFF00','#00FFFF','#800080','#800000','#008080','#0000FF',
  '#00CCFF','#CCFFFF','#CCFFCC','#FFFF99','#99CCFF','#FF99CC','#CC99FF','#FFCC99',
  '#3366FF','#33CCCC','#99CC00','#FFCC00','#FF9900','#FF6600','#666699','#969696',
  '#003366','#339966','#003300','#333300','#993300','#993366','#333399','#333333'
];
const BUILTIN_FORMATS={
  0:'General',1:'0',2:'0.00',3:'#,##0',4:'#,##0.00',9:'0%',10:'0.00%',11:'0.00E+00',12:'# ?/?',13:'# ??/??',
  14:'m/d/yy',15:'d-mmm-yy',16:'d-mmm',17:'mmm-yy',18:'h:mm AM/PM',19:'h:mm:ss AM/PM',20:'h:mm',21:'h:mm:ss',22:'m/d/yy h:mm',
  37:'#,##0 ;(#,##0)',38:'#,##0 ;[Red](#,##0)',39:'#,##0.00;(#,##0.00)',40:'#,##0.00;[Red](#,##0.00)',
  45:'mm:ss',46:'[h]:mm:ss',47:'mmss.0',49:'@'
};
const H_ALIGN=['general','left','center','right','fill','justify','center','distributed'];
const V_ALIGN=['top','center','bottom','justify','distributed'];
const BORDER_STYLE=['','thin','medium','dashed','dotted','thick','double','hair','mediumDashed','thin','mediumDashDot','mediumDashDot','dashed','mediumDashed','mediumDashDot','mediumDashDot'];

function u16(v,o){return v.getUint16(o,true)}
function i16(v,o){return v.getInt16(o,true)}
function u32(v,o){return v.getUint32(o,true)}
function f64(v,o){return v.getFloat64(o,true)}
function bytesView(bytes){return new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength)}
function concat(parts){let n=0;for(const p of parts)n+=p.length;const out=new Uint8Array(n);let o=0;for(const p of parts){out.set(p,o);o+=p.length}return out}
function colName(n){let s='';while(n>=0){s=String.fromCharCode(n%26+65)+s;n=Math.floor(n/26)-1}return s}
function encodeRef(r,c){return colName(c)+(r+1)}
function cp1252(bytes){try{return new TextDecoder('windows-1252').decode(bytes)}catch(_){let s='';for(const b of bytes)s+=String.fromCharCode(b);return s}}
function utf16(bytes){let s='';const v=bytesView(bytes);for(let i=0;i+1<bytes.length;i+=2)s+=String.fromCharCode(u16(v,i));return s}
function cleanText(s){return String(s||'').replace(/\u0000/g,'').replace(/\r\n?/g,'\n')}
function colorAt(index,palette){if(index===0x7FFF||index===0x40||index===0x41)return'';if(index<8)return DEFAULT_PALETTE[index]||'';return palette[index-8]||DEFAULT_PALETTE[index-8]||''}
function pxWidth(raw){return Math.max(18,Math.min(720,Math.round((raw/256)*7+5)))}
function pxHeight(twips){return Math.max(12,Math.min(420,Math.round((twips/20)*1.333)))}
function trimPng(bytes){for(let i=8;i+12<=bytes.length;){const v=bytesView(bytes),len=u32be(v,i),type=String.fromCharCode(...bytes.subarray(i+4,i+8));const end=i+12+len;if(end>bytes.length)break;if(type==='IEND')return bytes.slice(0,end);i=end}return bytes}
function u32be(v,o){return v.getUint32(o,false)}
function trimJpeg(bytes){for(let i=2;i+1<bytes.length;i++)if(bytes[i]===0xFF&&bytes[i+1]===0xD9)return bytes.slice(0,i+2);return bytes}
function imagePayload(bytes){const signatures=[{sig:[0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A],mime:'image/png',ext:'png'},{sig:[0xFF,0xD8,0xFF],mime:'image/jpeg',ext:'jpg'},{sig:[0x42,0x4D],mime:'image/bmp',ext:'bmp'}];for(const x of signatures){outer:for(let i=0;i<=bytes.length-x.sig.length;i++){for(let j=0;j<x.sig.length;j++)if(bytes[i+j]!==x.sig[j])continue outer;let data=bytes.slice(i);if(x.ext==='png')data=trimPng(data);if(x.ext==='jpg')data=trimJpeg(data);return{bytes:data,mime:x.mime,extension:x.ext}}}return null}

class CFBReader{
  constructor(buffer){
    this.bytes=new Uint8Array(buffer);this.view=bytesView(this.bytes);
    if(this.bytes.length<512||Array.from(this.bytes.slice(0,8)).map(x=>x.toString(16).padStart(2,'0')).join('')!=='d0cf11e0a1b11ae1')throw new Error('This is not an Excel 97–2003 compound document');
    const sectorShift=u16(this.view,30),miniSectorShift=u16(this.view,32);if(![9,12].includes(sectorShift)||miniSectorShift!==6)throw new Error('Unsupported or malformed compound-document sector geometry');this.sectorSize=2**sectorShift;this.miniSectorSize=2**miniSectorShift;this.numFat=u32(this.view,44);this.firstDir=u32(this.view,48);this.miniCutoff=u32(this.view,56);this.firstMiniFat=u32(this.view,60);this.numMiniFat=u32(this.view,64);this.firstDifat=u32(this.view,68);this.numDifat=u32(this.view,72);this.maxSectors=Math.ceil(Math.max(0,this.bytes.length-512)/this.sectorSize);if(this.numDifat>this.maxSectors||this.numFat>this.maxSectors)throw new Error('Malformed compound-document allocation tables');
    const difat=[];for(let i=0;i<109;i++){const x=u32(this.view,76+i*4);if(x!==FREE&&x!==END)difat.push(x)}let sid=this.firstDifat;const seenDifat=new Set();
    for(let n=0;n<this.numDifat&&sid!==END&&sid!==FREE&&!seenDifat.has(sid);n++){if(sid>=this.maxSectors)throw new Error('Malformed compound-document DIFAT chain');seenDifat.add(sid);const sec=this.sector(sid),v=bytesView(sec),count=this.sectorSize/4;for(let i=0;i<count-1;i++){const x=u32(v,i*4);if(x!==FREE&&x!==END)difat.push(x)}sid=u32(v,(count-1)*4)}
    this.fat=[];for(const fsid of difat.slice(0,this.numFat)){const sec=this.sector(fsid),v=bytesView(sec);for(let i=0;i<sec.length;i+=4)this.fat.push(u32(v,i))}
    const dir=this.readChain(this.firstDir);this.entries=[];for(let o=0;o+128<=dir.length;o+=128){const e=dir.subarray(o,o+128),v=bytesView(e),nlen=u16(v,64);const name=nlen>=2?utf16(e.subarray(0,Math.min(64,nlen-2))):'';this.entries.push({name,type:e[66],start:u32(v,116),size:u32(v,120)})}
    this.miniFat=[];if(this.numMiniFat&&this.firstMiniFat!==END&&this.firstMiniFat!==FREE){const m=this.readChain(this.firstMiniFat),v=bytesView(m);for(let i=0;i+4<=m.length;i+=4)this.miniFat.push(u32(v,i))}
    const root=this.entries.find(e=>e.type===5);this.miniStream=root?this.readChain(root.start).slice(0,root.size):new Uint8Array();
  }
  sector(id){const o=(id+1)*this.sectorSize;if(o<0||o>=this.bytes.length)return new Uint8Array();return this.bytes.subarray(o,o+this.sectorSize)}
  readChain(start){const parts=[],seen=new Set();let sid=start;while(sid!==FREE&&sid!==END&&sid<this.fat.length&&!seen.has(sid)){seen.add(sid);parts.push(this.sector(sid));sid=this.fat[sid]}return concat(parts)}
  readMiniChain(start,size){const parts=[],seen=new Set();let sid=start,total=0;while(sid!==FREE&&sid!==END&&sid<this.miniFat.length&&!seen.has(sid)&&total<size){seen.add(sid);const p=this.miniStream.subarray(sid*this.miniSectorSize,(sid+1)*this.miniSectorSize);parts.push(p);total+=p.length;sid=this.miniFat[sid]}return concat(parts).slice(0,size)}
  stream(name){const e=this.entries.find(x=>x.type===2&&x.name.toLowerCase()===String(name).toLowerCase());if(!e)return null;return e.size<this.miniCutoff?this.readMiniChain(e.start,e.size):this.readChain(e.start).slice(0,e.size)}
}

function parseRecords(bytes){const out=[];let p=0;while(p+4<=bytes.length){const v=bytesView(bytes.subarray(p,p+4)),type=u16(v,0),len=u16(v,2);if(p+4+len>bytes.length)break;out.push({offset:p,type,data:bytes.subarray(p+4,p+4+len)});p+=4+len}return out}
function unicodeString(data,offset=0,cchBytes=2){const v=bytesView(data);let p=offset,cch=cchBytes===1?data[p++]:u16(v,p);if(cchBytes===2)p+=2;if(p>=data.length)return{text:'',next:p};const flags=data[p++],wide=!!(flags&1),rich=!!(flags&8),ext=!!(flags&4);let runs=0,extLen=0;if(rich&&p+2<=data.length){runs=u16(v,p);p+=2}if(ext&&p+4<=data.length){extLen=u32(v,p);p+=4}const count=cch*(wide?2:1),chars=data.subarray(p,Math.min(data.length,p+count)),text=wide?utf16(chars):cp1252(chars);p+=count+4*runs+extLen;return{text:cleanText(text),next:p}}
function parseSst(records,start){
  const chunks=[records[start].data];let i=start+1;while(i<records.length&&records[i].type===0x003C){chunks.push(records[i].data);i++}
  let chunk=0,pos=0;const out=[];
  const advance=()=>{while(chunk<chunks.length&&pos>=chunks[chunk].length){chunk++;pos=0}};
  const raw=n=>{const result=new Uint8Array(n);let wrote=0;while(wrote<n){advance();if(chunk>=chunks.length)break;const take=Math.min(n-wrote,chunks[chunk].length-pos);result.set(chunks[chunk].subarray(pos,pos+take),wrote);pos+=take;wrote+=take}return result.subarray(0,wrote)};
  const byte=()=>{const b=raw(1);return b.length?b[0]:null};
  const word=()=>{const b=raw(2);return b.length===2?u16(bytesView(b),0):null};
  const dword=()=>{const b=raw(4);return b.length===4?u32(bytesView(b),0):null};
  const total=dword(),unique=dword();if(total==null||unique==null)return out;
  for(let n=0;n<unique;n++){
    const cch=word(),flags=byte();if(cch==null||flags==null)break;let wide=!!(flags&1),runs=0,extLen=0;
    if(flags&8){const value=word();if(value==null)break;runs=value}
    if(flags&4){const value=dword();if(value==null)break;extLen=value}
    let remain=cch,text='';
    while(remain>0){
      advance();if(chunk>=chunks.length)break;const unit=wide?2:1,available=chunks[chunk].length-pos,count=Math.min(remain,Math.floor(available/unit));
      if(count>0){const chars=chunks[chunk].subarray(pos,pos+count*unit);text+=wide?utf16(chars):cp1252(chars);pos+=count*unit;remain-=count}
      if(remain>0){chunk++;pos=0;if(chunk>=chunks.length)break;const continuation=byte();if(continuation==null)break;wide=!!(continuation&1)}
    }
    if(remain>0)break;
    raw(4*runs);raw(extLen);out.push(cleanText(text));
  }
  return out;
}
function parseBoundsheet(data){if(data.length<8)return null;const v=bytesView(data),offset=u32(v,0),state=data[4],type=data[5],cch=data[6],flags=data[7],wide=!!(flags&1),raw=data.subarray(8,8+cch*(wide?2:1));return{offset,state:state===1?'hidden':state===2?'veryHidden':'visible',type,name:cleanText(wide?utf16(raw):cp1252(raw))||'Sheet'} }
function parseFont(data,palette){if(data.length<16)return{};const v=bytesView(data),height=u16(v,0)/20,opts=u16(v,2),color=colorAt(u16(v,4),palette),weight=u16(v,6),underline=data[10],cch=data[14],flags=data[15],wide=!!(flags&1),name=cleanText(wide?utf16(data.subarray(16,16+cch*2)):cp1252(data.subarray(16,16+cch)));return{name,size:height||10,bold:weight>=700,italic:!!(opts&2),strike:!!(opts&8),underline:underline!==0,color}}
function parseFormat(data){if(data.length<3)return null;const id=u16(bytesView(data),0),x=unicodeString(data,2,2);return{id,format:x.text}}
function parsePalette(data){if(data.length<2)return DEFAULT_PALETTE.slice();const v=bytesView(data),n=u16(v,0),out=[];for(let i=0;i<n&&2+i*4+3<data.length;i++){const o=2+i*4;out.push('#'+[data[o],data[o+1],data[o+2]].map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase())}return out.length?out:DEFAULT_PALETTE.slice()}
function parseXf(data,fonts,formats,palette){if(data.length<20)return{};const v=bytesView(data),fontId=u16(v,0),numFmtId=u16(v,2),a=data[6],rotation=data[7],b1=u32(v,10),b2=u32(v,14),fill=u16(v,18),fillPattern=(b2>>>26)&0x3F,fg=fill&0x7F;const resolvedFontId=fontId===4?0:fontId>4?fontId-1:fontId,side=(style,color)=>style?{style:BORDER_STYLE[style]||'thin',color:colorAt(color,palette)||'#70757d'}:null,border={};const values={left:side(b1&15,(b1>>>16)&0x7F),right:side((b1>>>4)&15,(b1>>>23)&0x7F),top:side((b1>>>8)&15,b2&0x7F),bottom:side((b1>>>12)&15,(b2>>>7)&0x7F)};for(const[k,val]of Object.entries(values))if(val)border[k]=val;const fmt=formats[numFmtId]??BUILTIN_FORMATS[numFmtId]??'';return{font:fonts[resolvedFontId]||{},fill:fillPattern?colorAt(fg,palette):'',border,align:H_ALIGN[a&7]||'general',vertical:V_ALIGN[(a>>>4)&7]||'',wrap:!!(a&8),rotation:rotation>90?rotation-180:rotation,numFmtId,numberFormat:fmt,hideZero:String(fmt).split(';').length>=3&&/^\s*(?:""|)\s*$/.test(String(fmt).split(';')[2]||'')}}
function decodeRk(raw){let n;if(raw&2)n=(raw>>2);else{const b=new ArrayBuffer(8),v=new DataView(b);v.setUint32(0,0,true);v.setUint32(4,raw&0xFFFFFFFC,true);n=v.getFloat64(0,true)}return raw&1?n/100:n}
function excelDate(serial,date1904){let days=Number(serial);if(!Number.isFinite(days))return null;const base=date1904?Date.UTC(1904,0,1):Date.UTC(1899,11,30);return new Date(base+days*86400000)}
function formatNumber(value,style,date1904){const fmt=String(style?.numberFormat||'');if(!Number.isFinite(Number(value)))return value;if(/(^|[^a-z])[dmyhs]+/i.test(fmt)&&!/[#0]\s*[Ee]/.test(fmt)){const d=excelDate(value,date1904);if(d&&!isNaN(d)){const dd=String(d.getUTCDate()).padStart(2,'0'),mm=String(d.getUTCMonth()+1).padStart(2,'0'),yyyy=d.getUTCFullYear(),hh=String(d.getUTCHours()).padStart(2,'0'),mi=String(d.getUTCMinutes()).padStart(2,'0');if(/[hHsS]/.test(fmt)&&/[dmy]/i.test(fmt))return`${dd}/${mm}/${yyyy} ${hh}:${mi}`;if(/[hHsS]/.test(fmt))return`${hh}:${mi}`;return`${dd}/${mm}/${yyyy}`}}if(fmt.includes('%')){const decimals=(fmt.match(/0\.(0+)/)||[])[1]?.length||0;return(Number(value)*100).toFixed(decimals)+'%'}if(/0\.00/.test(fmt))return Number(value).toFixed(2);if(/#,##0/.test(fmt))return Number(value).toLocaleString(undefined,{maximumFractionDigits:/\.00/.test(fmt)?2:0,minimumFractionDigits:/\.00/.test(fmt)?2:0});return String(value)}
function formulaCached(data){if(data.length<14)return{value:'',special:true};const r=data.subarray(6,14),v=bytesView(r);if(r[6]===0xFF&&r[7]===0xFF){const type=r[0];if(type===1)return{value:!!r[2],special:true};if(type===2)return{value:'#ERROR!',special:true};if(type===3)return{value:'',special:true};return{value:'',special:true,string:true}}return{value:f64(v,0),special:false}}
function parseStringRecord(data){return unicodeString(data,0,2).text}
function isEscher(data){if(data.length<8)return false;const v=bytesView(data),t=u16(v,2);return t>=0xF000&&t<=0xF1FF}
function artRecords(data,start=0,end=data.length){const out=[];let p=start;while(p+8<=end){const v=bytesView(data.subarray(p,p+8)),vi=u16(v,0),type=u16(v,2),len=u32(v,4),q=p+8+len;if(q>end)break;out.push({offset:p,vi,type,data:data.subarray(p+8,q)});p=q}return out}
function walkArt(data,out=[]){for(const r of artRecords(data)){out.push(r);if((r.vi&15)===15)walkArt(r.data,out)}return out}
function parseGlobalImages(globalRecords){const chunks=[];let started=false;for(const r of globalRecords){if(!started){if(r.type===0x00EB){started=true;chunks.push(r.data)}}else if(r.type===0x00EB||r.type===0x003C)chunks.push(r.data);else break}if(!chunks.length)return[];const all=walkArt(concat(chunks)),images=[];for(const r of all){if(r.type!==0xF007||r.data.length<44)continue;const nameLen=r.data[33]||0,childAt=36+nameLen;if(childAt+8>r.data.length)continue;const child=artRecords(r.data,childAt,r.data.length)[0],payload=child?imagePayload(child.data):imagePayload(r.data.subarray(childAt));if(!payload)continue;const blob=new Blob([payload.bytes],{type:payload.mime});images.push({...payload,url:URL.createObjectURL(blob),valid:true})}return images}
function parseTxoTexts(records){const texts=[];for(let i=0;i<records.length;i++){const r=records[i];if(r.type!==0x01B6||r.data.length<14)continue;const v=bytesView(r.data),cch=u16(v,10);let remain=cch,text='',j=i+1;while(remain>0&&j<records.length&&records[j].type===0x003C){const d=records[j].data;if(!d.length){j++;continue}const wide=!!(d[0]&1),count=Math.min(remain,Math.floor((d.length-1)/(wide?2:1)));text+=wide?utf16(d.subarray(1,1+count*2)):cp1252(d.subarray(1,1+count));remain-=count;j++}texts.push(cleanText(text))}return texts}
function parseOpt(r){const props={};if(!r)return props;const count=r.vi>>>4,v=bytesView(r.data);for(let i=0;i<count&&i*6+6<=r.data.length;i++){const op=u16(v,i*6),id=op&0x3FFF;props[id]=u32(v,i*6+2)}return props}
function shapeContainers(data,out=[]){for(const r of artRecords(data)){if(r.type===0xF004)out.push(r.data);if((r.vi&15)===15)shapeContainers(r.data,out)}return out}
function anchorMarker(anchor,widths,heights,defaultColWidth,defaultRowHeight){if(!anchor||anchor.length<18)return null;const v=bytesView(anchor),vals=[];for(let i=0;i<9;i++)vals.push(u16(v,i*2));const[,c1,dx1,r1,dy1,c2,dx2,r2,dy2]=vals,cw=c=>widths[c]||defaultColWidth,rh=r=>heights[r]||defaultRowHeight;return{from:{c:c1,r:r1,x:cw(c1)*dx1/1024,y:rh(r1)*dy1/256},to:{c:c2,r:r2,x:cw(c2)*dx2/1024,y:rh(r2)*dy2/256}}}
function parseSheetDrawings(records,images,widths,heights,defaultColWidth,defaultRowHeight){const chunks=[];for(const r of records)if(r.type===0x00EC||(r.type===0x003C&&isEscher(r.data)))chunks.push(r.data);if(!chunks.length)return[];const texts=parseTxoTexts(records),drawings=[];let textIndex=0;for(const container of shapeContainers(concat(chunks))){let sp=null,opt=null,anchor=null,hasTextbox=false;for(const r of artRecords(container)){if(r.type===0xF00A)sp=r;else if(r.type===0xF00B)opt=r;else if(r.type===0xF010)anchor=r.data;else if(r.type===0xF00D)hasTextbox=true}if(!sp||!anchor)continue;const shapeType=sp.vi>>>4,markers=anchorMarker(anchor,widths,heights,defaultColWidth,defaultRowHeight);if(!markers)continue;if(shapeType===75){const pib=parseOpt(opt)[0x0104]||0,img=images[pib-1];if(img)drawings.push({kind:'image',url:img.url,bytes:img.bytes,mime:img.mime,extension:img.extension,from:markers.from,to:markers.to,name:`Legacy image ${pib}`})}else if(hasTextbox){const text=texts[textIndex++]||'';if(text)drawings.push({kind:'shape',text,from:markers.from,to:markers.to,fill:'transparent',line:'#00000000',lineWidth:0,fontSize:10,bold:false,name:'Legacy text box'})}}
  return drawings;
}
function parseHeaderFooter(data){return data.length?unicodeString(data,0,2).text:''}
function parseSheet(records,meta,globalInfo){
  const cells=new Map(),originalCells=new Map(),merges=[],widths={},heights={},styles=globalInfo.styles;let maxR=39,maxC=15,defaultColWidth=68,defaultRowHeight=20,freezePane=null,pageSetup={},margins={},autoFilter='',pendingStringFormula=null,header='',footer='';
  for(let i=0;i<records.length;i++){
    const r=records[i],d=r.data,v=bytesView(d);let row,col,xf,value,cell;
    if(r.type===0x0200&&d.length>=12){maxR=Math.max(maxR,u32(v,4)-1);maxC=Math.max(maxC,u16(v,10)-1)}
    else if(r.type===0x0208&&d.length>=8){row=u16(v,0);const h=u16(v,6)&0x7FFF;if(h)heights[row]=pxHeight(h);maxR=Math.max(maxR,row)}
    else if(r.type===0x007D&&d.length>=10){const first=u16(v,0),last=u16(v,2),w=u16(v,4);for(let c=first;c<=last;c++)widths[c]=pxWidth(w)}
    else if(r.type===0x0055&&d.length>=2)defaultColWidth=pxWidth(u16(v,0)*256)
    else if(r.type===0x0225&&d.length>=4)defaultRowHeight=pxHeight(u16(v,2)&0x7FFF)
    else if(r.type===0x00E5&&d.length>=2){const n=u16(v,0);for(let j=0;j<n&&2+j*8+8<=d.length;j++){const o=2+j*8,r1=u16(v,o),r2=u16(v,o+2),c1=u16(v,o+4),c2=u16(v,o+6);merges.push(`${encodeRef(r1,c1)}:${encodeRef(r2,c2)}`);maxR=Math.max(maxR,r2);maxC=Math.max(maxC,c2)}}
    else if(r.type===0x0041&&d.length>=10){freezePane={xSplit:u16(v,0),ySplit:u16(v,2),topLeftCell:encodeRef(u16(v,4),u16(v,6)),state:'frozen'}}
    else if([0x0026,0x0027,0x0028,0x0029].includes(r.type)&&d.length>=8){const k={0x26:'left',0x27:'right',0x28:'top',0x29:'bottom'}[r.type];margins[k]=f64(v,0)}
    else if(r.type===0x00A1&&d.length>=12){const flags=u16(v,10);pageSetup={paperSize:u16(v,0),scale:u16(v,2),fitToWidth:u16(v,6),fitToHeight:u16(v,8),orientation:(flags&2)?'portrait':'landscape'}}
    else if(r.type===0x0014)header=parseHeaderFooter(d)
    else if(r.type===0x0015)footer=parseHeaderFooter(d)
    else if(r.type===0x00FD&&d.length>=10){row=u16(v,0);col=u16(v,2);xf=u16(v,4);value=globalInfo.sst[u32(v,6)]??'';cell={v:value,f:'',styleId:xf,style:styles[xf]||{},t:'s',display:value}}
    else if(r.type===0x0203&&d.length>=14){row=u16(v,0);col=u16(v,2);xf=u16(v,4);value=f64(v,6);cell={v:value,f:'',styleId:xf,style:styles[xf]||{},t:'n',display:formatNumber(value,styles[xf],globalInfo.date1904)}}
    else if(r.type===0x027E&&d.length>=10){row=u16(v,0);col=u16(v,2);xf=u16(v,4);value=decodeRk(u32(v,6));cell={v:value,f:'',styleId:xf,style:styles[xf]||{},t:'n',display:formatNumber(value,styles[xf],globalInfo.date1904)}}
    else if(r.type===0x00BD&&d.length>=12){row=u16(v,0);const first=u16(v,2),last=u16(v,d.length-2);for(let c=first,o=4;c<=last&&o+6<=d.length-2;c++,o+=6){xf=u16(v,o);value=decodeRk(u32(v,o+2));const k=encodeRef(row,c),cc={v:value,f:'',styleId:xf,style:styles[xf]||{},t:'n',display:formatNumber(value,styles[xf],globalInfo.date1904)};cells.set(k,cc);originalCells.set(k,{v:cc.v,f:'',styleId:xf,t:'n',display:cc.display});maxR=Math.max(maxR,row);maxC=Math.max(maxC,c)}}
    else if(r.type===0x0006&&d.length>=14){row=u16(v,0);col=u16(v,2);xf=u16(v,4);const cached=formulaCached(d),cellStyle=styles[xf]||{};cell={v:cached.value,f:'',styleId:xf,style:cellStyle,t:typeof cached.value==='string'?'s':'n',display:typeof cached.value==='string'?cached.value:formatNumber(cached.value,cellStyle,globalInfo.date1904),legacyFormula:true};if(cached.string)pendingStringFormula={row,col,xf,cell}}
    else if(r.type===0x0207&&pendingStringFormula){value=parseStringRecord(d);pendingStringFormula.cell.v=value;pendingStringFormula.cell.t='s';pendingStringFormula.cell.display=value;const k=encodeRef(pendingStringFormula.row,pendingStringFormula.col);cells.set(k,pendingStringFormula.cell);originalCells.set(k,{v:value,f:'',styleId:pendingStringFormula.xf,t:'s',display:value});pendingStringFormula=null;continue}
    else if(r.type===0x0205&&d.length>=8){row=u16(v,0);col=u16(v,2);xf=u16(v,4);value=d[6];cell={v:d[7]?`#ERROR ${value}`:!!value,f:'',styleId:xf,style:styles[xf]||{},t:d[7]?'e':'b',display:d[7]?`#ERROR ${value}`:(value?'TRUE':'FALSE')}}
    else if(r.type===0x0201&&d.length>=6){row=u16(v,0);col=u16(v,2);xf=u16(v,4);cell={v:'',f:'',styleId:xf,style:styles[xf]||{},t:'s',display:''}}
    else if(r.type===0x00BE&&d.length>=8){row=u16(v,0);const first=u16(v,2),last=u16(v,d.length-2);for(let c=first,o=4;c<=last&&o+2<=d.length-2;c++,o+=2){xf=u16(v,o);const k=encodeRef(row,c),cc={v:'',f:'',styleId:xf,style:styles[xf]||{},t:'s',display:''};cells.set(k,cc);originalCells.set(k,{v:'',f:'',styleId:xf,t:'s',display:''});maxR=Math.max(maxR,row);maxC=Math.max(maxC,c)}}
    if(cell&&row!=null&&col!=null){const k=encodeRef(row,col);cells.set(k,cell);originalCells.set(k,{v:cell.v,f:'',styleId:xf,t:cell.t,display:cell.display});maxR=Math.max(maxR,row);maxC=Math.max(maxC,col)}
  }
  const drawings=parseSheetDrawings(records,globalInfo.images,widths,heights,defaultColWidth,defaultRowHeight);for(const d of drawings){maxR=Math.max(maxR,Number(d.to?.r||0));maxC=Math.max(maxC,Number(d.to?.c||0))}const legacyFormulaCount=[...cells.values()].filter(c=>c.legacyFormula).length;
  return{name:meta.name,state:meta.state,path:'',xml:'',cells,originalCells,merges,originalMerges:[...merges],widths,originalWidths:{...widths},heights,originalHeights:{...heights},defaultColWidth,defaultRowHeight,drawings,tables:[],maxR:Math.min(maxR+8,600),maxC:Math.min(maxC+4,100),printArea:'',margins,pageSetup,freezePane,autoFilter,hasConditionalFormatting:false,hasDataValidation:false,header,footer,legacyFormulaCount};
}
async function parseWorkbook(buffer,fileName='Workbook.xls'){
  if(global.InkDeskRuntime)global.InkDeskRuntime.validateInputSize(buffer.byteLength,fileName);
  const cfb=new CFBReader(buffer),workbook=cfb.stream('Workbook')||cfb.stream('Book');if(!workbook)throw new Error('The Excel workbook stream is missing');const records=parseRecords(workbook),bounds=[],formats={...BUILTIN_FORMATS};let palette=DEFAULT_PALETTE.slice(),date1904=false,active=0,sst=[];
  for(let i=0;i<records.length;i++){const r=records[i],d=r.data,v=bytesView(d);if(r.type===0x0085){const b=parseBoundsheet(d);if(b&&b.type===0)bounds.push(b)}else if(r.type===0x0092)palette=parsePalette(d);else if(r.type===0x041E){const f=parseFormat(d);if(f)formats[f.id]=f.format}else if(r.type===0x0022&&d.length>=2)date1904=!!u16(v,0);else if(r.type===0x003D&&d.length>=12)active=u16(v,10);else if(r.type===0x00FC)sst=parseSst(records,i)}
  if(!bounds.length)throw new Error('No BIFF8 worksheets were found');const firstSheet=Math.min(...bounds.map(x=>x.offset));const globals=records.filter(r=>r.offset<firstSheet),fonts=[];for(const r of globals)if(r.type===0x0031)fonts.push(parseFont(r.data,palette));const styles=[];for(const r of globals)if(r.type===0x00E0)styles.push(parseXf(r.data,fonts,formats,palette));const images=parseGlobalImages(globals),offsetIndex=new Map(records.map((r,i)=>[r.offset,i])),globalInfo={sst,fonts,styles,formats,palette,date1904,images},sheets=[];
  for(const meta of bounds){const start=offsetIndex.get(meta.offset);if(start==null)continue;let end=start;while(end<records.length&&records[end].type!==0x000A)end++;sheets.push(parseSheet(records.slice(start,end+1),meta,globalInfo))}
  if(!sheets.length)throw new Error('The BIFF8 worksheets could not be decoded');active=Math.min(Math.max(0,active),sheets.length-1);if(sheets[active]?.state!=='visible'){const v=sheets.findIndex(s=>s.state==='visible');if(v>=0)active=v}const formulaCount=sheets.reduce((n,s)=>n+s.legacyFormulaCount,0),drawingCount=sheets.reduce((n,s)=>n+(s.drawings||[]).length,0);
  return{zip:null,sheets,active,fileName,loaded:true,legacy:true,legacyFormat:'BIFF8',legacyStyles:styles,images,workbookXml:'',legacyDiagnostics:{formulaCount,drawingCount,imageCount:images.length},saveWarning:'This Excel 97–2003 workbook is imported locally. Saving creates an XLSX copy; legacy formulas are converted from their cached results and macros or unsupported embedded objects are not carried over.'};
}

global.LocalXLS={parseWorkbook};
})(window);

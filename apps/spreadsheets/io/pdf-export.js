(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
// In-app PDF export: the sheet is drawn once as vector content, then tiled onto paper pages
// (orientation, margins, scale, pages per sheet, page range). No browser print dialog involved.
const PX=.75,PAD=4,PAPER={a4:[595.28,841.89],letter:[612,792]},MARGINS={narrow:18,normal:54,wide:72};
let libPromise=null;
function loadLib(){if(root.PDFLib)return Promise.resolve(root.PDFLib);if(!libPromise)libPromise=new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='vendor/pdf-lib/pdf-lib.min.js';s.onload=()=>root.PDFLib?resolve(root.PDFLib):reject(new Error('The PDF engine failed to load.'));s.onerror=()=>{libPromise=null;reject(new Error('The PDF engine is unavailable.'))};document.head.appendChild(s)});return libPromise}
function rgb(L,c,f){const m=/^#?([0-9a-f]{6})/i.exec(String(c||''));if(!m)return f;const n=parseInt(m[1],16);return L.rgb(((n>>16)&255)/255,((n>>8)&255)/255,(n&255)/255)}
function colIndex(letters){let n=0;for(const ch of letters)n=n*26+ch.charCodeAt(0)-64;return n-1}
function extent(sheet,U,mm){let maxR=-1,maxC=-1;for(const[ref,cell]of sheet.cells){const m=/^([A-Z]+)(\d+)$/.exec(ref);if(!m)continue;const st=cell?.style||{};if(U.display(cell)===''&&!st.fill&&!st.border)continue;maxR=Math.max(maxR,Number(m[2])-1);maxC=Math.max(maxC,colIndex(m[1]))}for(const d of sheet.drawings||[])for(const m of[d.from,d.to])if(m){maxR=Math.max(maxR,Number(m.r)||0);maxC=Math.max(maxC,Number(m.c)||0)}for(const[,q]of mm.top)if(q.r1<=maxR&&q.c1<=maxC){maxR=Math.max(maxR,q.r2);maxC=Math.max(maxC,q.c2)}return{maxR,maxC}}
function safeText(font,text){return String(text).split('\n').map(line=>{try{font.encodeText(line);return line}catch(_){return [...line].map(ch=>{try{font.encodeText(ch);return ch}catch(__){return '?'}}).join('')}}).join('\n')}
function fit(font,text,size,width){if(font.widthOfTextAtSize(text,size)<=width)return text;let lo=0,hi=text.length;while(lo<hi){const mid=(lo+hi+1)>>1;if(font.widthOfTextAtSize(text.slice(0,mid),size)<=width)lo=mid;else hi=mid-1}return text.slice(0,lo)}
function wrapLines(font,text,size,width){const out=[];for(const para of String(text).split('\n')){let line='';for(const word of para.split(/(\s+)/)){const next=line+word;if(line&&font.widthOfTextAtSize(next.trimEnd(),size)>width){out.push(line.trimEnd());line=word.trimStart()}else line=next}out.push(line.trimEnd())}return out}
const BORDER_W={hair:.5,thin:.75,medium:1.5,thick:2.25,double:2.25,dashed:.75,dotted:.75,mediumDashed:1.5,mediumDashDot:1.5};
async function renderSheet(L,sheet){
 const U=NS.GridPrintModel,G=NS.GridGeometry;if(!U||!G)throw new Error('Spreadsheet print model is unavailable.');
 const mm=U.mergeMaps(sheet),{maxR,maxC}=extent(sheet,U,mm);if(maxR<0)throw new Error('The active sheet is empty.');
 const colX=[0],rowY=[0];for(let c=0;c<=maxC;c++)colX.push(colX[c]+G.colWidth(sheet,c));for(let r=0;r<=maxR;r++)rowY.push(rowY[r]+G.rowHeight(sheet,r));
 const W=colX[maxC+1]*PX,H=rowY[maxR+1]*PX,doc=await L.PDFDocument.create(),page=doc.addPage([W,H]),S=L.StandardFonts;
 const fonts={r:await doc.embedFont(S.Helvetica),b:await doc.embedFont(S.HelveticaBold),i:await doc.embedFont(S.HelveticaOblique),bi:await doc.embedFont(S.HelveticaBoldOblique)};
 const X=px=>px*PX,Y=px=>H-px*PX,black=L.rgb(0,0,0),cells=[];
 for(let r=0;r<=maxR;r++)for(let c=0;c<=maxC;c++){const key=root.LocalXLSX.encodeRef(r,c);if(mm.covered.has(key))continue;const cell=sheet.cells.get(key),q=mm.top.get(key);cells.push({r,c,key,cell,x1:colX[c],x2:colX[(q?q.c2:c)+1],y1:rowY[r],y2:rowY[(q?q.r2:r)+1],merged:!!q})}
 for(const k of cells){const fill=k.cell?.style?.fill;if(fill)page.drawRectangle({x:X(k.x1),y:Y(k.y2),width:X(k.x2-k.x1),height:X(k.y2-k.y1),color:rgb(L,fill,L.rgb(1,1,1))})}
 for(const k of cells){const b=k.cell?.style?.border;if(!b)continue;const line=(side,x1,y1,x2,y2)=>{const s=b[side];if(!s)return;page.drawLine({start:{x:X(x1),y:Y(y1)},end:{x:X(x2),y:Y(y2)},thickness:BORDER_W[s.style]||.75,color:rgb(L,s.color,black),dashArray:s.style==='dashed'?[3,2]:s.style==='dotted'?[1,1.5]:undefined})};line('top',k.x1,k.y1,k.x2,k.y1);line('bottom',k.x1,k.y2,k.x2,k.y2);line('left',k.x1,k.y1,k.x1,k.y2);line('right',k.x2,k.y1,k.x2,k.y2)}
 for(const k of cells){const raw=U.display(k.cell);if(!raw)continue;const st=k.cell?.style||{},f=st.font||{},font=f.bold&&f.italic?fonts.bi:f.bold?fonts.b:f.italic?fonts.i:fonts.r,size=Number(f.size)||11,color=rgb(L,f.color,black),text=safeText(font,raw);const value=k.cell.calculated!==undefined&&k.cell.calculated!==null?k.cell.calculated:k.cell.v,align=st.align&&st.align!=='general'?st.align:(typeof value==='number'?'right':'left');
  const ext=k.merged?0:(U.overflowExtent(sheet,mm,k.r,k.c,k.cell,raw,1)||0),boxW=X(k.x2-k.x1+ext)-2*X(PAD),boxTop=k.y1*PX,boxH=X(k.y2-k.y1);
  const lines=st.wrap?wrapLines(font,text,size,boxW):text.split('\n').map(t=>fit(font,t,size,boxW)),lh=size*1.2,blockH=lines.length*lh;
  let top=st.vertical==='top'?boxTop+2:st.vertical==='center'?boxTop+(boxH-blockH)/2:boxTop+boxH-blockH-2;
  for(const ln of lines){const w=font.widthOfTextAtSize(ln,size),left=align==='center'?X(k.x1)+(X(k.x2-k.x1)-w)/2:align==='right'?X(k.x2)-X(PAD)-w:X(k.x1)+X(PAD);page.drawText(ln,{x:left,y:H-(top+size*.95),size,font,color});top+=lh}}
 const point=m=>({x:colX[Math.min(maxC+1,Math.max(0,Number(m.c)||0))]+(Number(m.x)||0),y:rowY[Math.min(maxR+1,Math.max(0,Number(m.r)||0))]+(Number(m.y)||0)});
 for(const d of sheet.drawings||[]){if(!d.from)continue;const a=point(d.from),b=d.to?point(d.to):{x:a.x+120,y:a.y+60},w=Math.max(1,b.x-a.x),h=Math.max(1,b.y-a.y);
  if(d.kind==='image'&&d.bytes){try{const bytes=d.bytes instanceof Uint8Array?d.bytes:new Uint8Array(d.bytes),png=bytes[0]===0x89,img=png?await doc.embedPng(bytes):await doc.embedJpg(bytes);page.drawImage(img,{x:X(a.x),y:Y(a.y+h),width:X(w),height:X(h)})}catch(_){}}
  else if(d.kind==='shape'){if(d.fill&&d.fill!=='transparent')page.drawRectangle({x:X(a.x),y:Y(a.y+h),width:X(w),height:X(h),color:rgb(L,d.fill,L.rgb(1,1,1))});if(d.line&&d.line!=='#00000000'&&d.lineWidth)page.drawRectangle({x:X(a.x),y:Y(a.y+h),width:X(w),height:X(h),borderColor:rgb(L,d.line,black),borderWidth:Number(d.lineWidth)||.75});if(d.text){const font=d.bold?fonts.b:fonts.r,size=Number(d.fontSize)||10;let top=a.y*PX+2;for(const ln of wrapLines(font,safeText(font,d.text),size,X(w)-4)){page.drawText(ln,{x:X(a.x)+2,y:H-(top+size*.95),size,font,color:black});top+=size*1.15}}}}
 const finished=await L.PDFDocument.load(await doc.save());
 return{doc:finished,page:finished.getPage(0),W,H,colX:colX.map(X),rowY:rowY.map(X)}}
function breaks(pos,total,size){const out=[0];let start=0;while(total-start>size+.5){let next=pos.filter(v=>v>start+1&&v<=start+size+.01).pop();if(!next||next<=start)next=start+size;out.push(next);start=next}out.push(total);return out}
function parseRange(text,count){const t=String(text||'').trim();if(!t)return null;const set=new Set();for(const part of t.split(/[,;]\s*/)){const m=/^(\d+)(?:\s*-\s*(\d+))?$/.exec(part.trim());if(!m)continue;const a=Number(m[1]),b=Number(m[2]||m[1]);for(let i=Math.min(a,b);i<=Math.max(a,b)&&i<=count;i++)if(i>=1)set.add(i)}return set.size?set:null}
async function exportPdf(sheet,options={}){
 const L=await loadLib(),src=await renderSheet(L,sheet),paper=PAPER[options.paper]||PAPER.a4,landscape=options.orientation==='landscape'||(options.orientation!=='portrait'&&src.W>src.H*1.05);
 const pageW=landscape?paper[1]:paper[0],pageH=landscape?paper[0]:paper[1],margin=MARGINS[options.margins]??MARGINS.normal,per=[1,2,4].includes(Number(options.perSheet))?Number(options.perSheet):1;
 const cols=per===4?2:per===2&&pageW>=pageH?2:1,rows=per===4?2:per===2&&pageW<pageH?2:1,gap=per>1?12:0,slotW=(pageW-2*margin-(cols-1)*gap)/cols,slotH=(pageH-2*margin-(rows-1)*gap)/rows;
 const scale=options.scale==='fit'||!options.scale?Math.min(1,slotW/src.W):Math.max(.1,Math.min(4,Number(options.scale)/100));
 const colBreaks=breaks(src.colX,src.W,slotW/scale),rowBreaks=breaks(src.rowY,src.H,slotH/scale),tiles=[];
 for(let ci=0;ci<colBreaks.length-1;ci++)for(let ri=0;ri<rowBreaks.length-1;ri++)tiles.push({x0:colBreaks[ci],x1:colBreaks[ci+1],y0:rowBreaks[ri],y1:rowBreaks[ri+1]});
 const wanted=parseRange(options.range,tiles.length),chosen=tiles.filter((_,i)=>!wanted||wanted.has(i+1));if(!chosen.length)throw new Error('The page range selects no pages.');
 const out=await L.PDFDocument.create();let page=null,slot=per;
 for(const t of chosen){if(slot>=per){page=out.addPage([pageW,pageH]);slot=0}const emb=await out.embedPage(src.page,{left:t.x0,right:t.x1,bottom:src.H-t.y1,top:src.H-t.y0}),col=slot%cols,row=Math.floor(slot/cols),w=(t.x1-t.x0)*scale,h=(t.y1-t.y0)*scale;page.drawPage(emb,{x:margin+col*(slotW+gap),y:pageH-margin-row*(slotH+gap)-h,width:w,height:h});slot++}
 out.setTitle(String(options.title||'Spreadsheet'));out.setProducer('InkDOS Spreadsheets');
 return{bytes:await out.save(),pages:out.getPageCount(),tiles:tiles.length}}
NS.SheetPdfExport=Object.freeze({exportPdf,loadLib,parseRange});
})(globalThis);

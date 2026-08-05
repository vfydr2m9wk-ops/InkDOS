(function(global){
'use strict';
const W_NS='http://schemas.openxmlformats.org/wordprocessingml/2006/main';
const R_NS='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
let currentXmlBudget=null;
function u16(a,o){return a[o]|(a[o+1]<<8)}
function u32(a,o){return (a[o]|(a[o+1]<<8)|(a[o+2]<<16)|(a[o+3]<<24))>>>0}
function decode(bytes){return new TextDecoder('utf-8').decode(bytes).replace(/^\uFEFF/,'')}
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function val(el,name='val'){if(!el)return'';return el.getAttributeNS(W_NS,name)||el.getAttribute('w:'+name)||el.getAttribute(name)||''}
async function inflateRaw(bytes){
  if(global.pako&&typeof global.pako.inflateRaw==='function'){
    try{return new Uint8Array(global.pako.inflateRaw(bytes));}
    catch(error){throw new Error('The bundled DOCX decompressor could not read this file: '+(error&&error.message?error.message:error));}
  }
  if(typeof DecompressionStream!=='undefined'){
    try{const ds=new DecompressionStream('deflate-raw');return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(ds)).arrayBuffer());}
    catch(error){throw new Error('WebKit could not decompress this DOCX: '+(error&&error.message?error.message:error));}
  }
  throw new Error('The local DOCX decompression engine did not load. Re-extract the complete application folder and reopen Documents.html.');
}
async function unzip(buffer){
  if(global.InkDeskRuntime)global.InkDeskRuntime.validateZipPackage(buffer,'DOCX file');
  const a=new Uint8Array(buffer);let eocd=-1;
  for(let i=a.length-22;i>=Math.max(0,a.length-65557);i--){if(u32(a,i)===0x06054b50){eocd=i;break}}
  if(eocd<0)throw new Error('Invalid DOCX package: central directory was not found.');
  const count=u16(a,eocd+10),cd=u32(a,eocd+16);let p=cd;const map=new Map();
  for(let i=0;i<count;i++){
    if(u32(a,p)!==0x02014b50)throw new Error('Invalid DOCX central directory.');
    const method=u16(a,p+10),cs=u32(a,p+20),us=u32(a,p+24),nl=u16(a,p+28),el=u16(a,p+30),cl=u16(a,p+32),lo=u32(a,p+42);
    const name=decode(a.slice(p+46,p+46+nl)).normalize('NFC');
    if(u32(a,lo)!==0x04034b50)throw new Error('Invalid DOCX local entry.');
    const lnl=u16(a,lo+26),lel=u16(a,lo+28),start=lo+30+lnl+lel,packed=a.slice(start,start+cs);
    let data;if(method===0)data=packed;else if(method===8)data=await inflateRaw(packed);else throw new Error('Unsupported compression method in DOCX: '+method);
    if(us&&data.length!==us)throw new Error('Invalid DOCX entry size for '+name+'.');
    map.set(name,data);p+=46+nl+el+cl;
  }
  return map;
}
function xml(bytes,context='DOCX package part'){const text=decode(bytes).replace(/^\uFEFF/,'');if(global.InkDeskRuntime)return global.InkDeskRuntime.parseXml(text,context,currentXmlBudget);const doc=new DOMParser().parseFromString(text,'application/xml');if(doc.querySelector('parsererror'))throw new Error('Invalid XML in '+context+'.');return doc}
function all(el,name){return Array.from(el.getElementsByTagNameNS('*',name))}
function first(el,name){return el?el.getElementsByTagNameNS('*',name)[0]||null:null}
function attr(el,name){if(!el)return'';return el.getAttributeNS(R_NS,name)||el.getAttribute('r:'+name)||el.getAttribute(name)||''}
function parseRels(doc){const out={};all(doc,'Relationship').forEach(r=>{out[r.getAttribute('Id')]=r.getAttribute('Target')});return out}
function normalPath(base,target){base=String(base||'').normalize('NFC');target=String(target||'').normalize('NFC');if(target.startsWith('/'))return target.slice(1);const bits=(base+'/'+target).split('/'),out=[];for(const b of bits){if(!b||b==='.')continue;if(b==='..')out.pop();else out.push(b)}return out.join('/')}
function num(v,fallback=0){const n=parseFloat(v);return Number.isFinite(n)?n:fallback}
function merge(){return Object.assign({},...Array.from(arguments).filter(Boolean))}
function parseRunProps(rPr){
  if(!rPr)return{};const out={};
  if(first(rPr,'b'))out.bold=val(first(rPr,'b'))!=='0'&&val(first(rPr,'b'))!=='false';
  if(first(rPr,'i'))out.italic=val(first(rPr,'i'))!=='0'&&val(first(rPr,'i'))!=='false';
  if(first(rPr,'u'))out.underline=val(first(rPr,'u'))!=='none';
  const color=first(rPr,'color');if(color&&val(color)&&val(color)!=='auto')out.color='#'+val(color);
  const sz=first(rPr,'sz');if(sz&&num(val(sz)))out.fontSizePt=num(val(sz))/2;
  const fonts=first(rPr,'rFonts');if(fonts){const f=val(fonts,'ascii')||val(fonts,'hAnsi');const theme=val(fonts,'asciiTheme')||val(fonts,'hAnsiTheme');if(f)out.fontFamily=f;else if(theme)out.fontFamily=/major/i.test(theme)?'Cambria':'Calibri';}
  return out;
}
function parseParagraphProps(pPr){
  if(!pPr)return{};const out={};
  const jc=first(pPr,'jc');if(jc)out.alignment=val(jc);
  const ind=first(pPr,'ind');if(ind){for(const key of ['left','right','firstLine','hanging']){const v=val(ind,key);if(v!=='')out[key]=num(v)}}
  const spacing=first(pPr,'spacing');if(spacing){for(const key of ['before','after','line']){const v=val(spacing,key);if(v!=='')out[key]=num(v)}const lr=val(spacing,'lineRule');if(lr)out.lineRule=lr;}
  if(first(pPr,'contextualSpacing'))out.contextualSpacing=true;
  if(first(pPr,'pageBreakBefore'))out.pageBreakBefore=true;
  if(first(pPr,'keepNext'))out.keepNext=true;
  return out;
}
function parseNumberingRef(pPr){const numPr=first(pPr,'numPr');if(!numPr)return null;return{numId:val(first(numPr,'numId'))||'0',ilvl:parseInt(val(first(numPr,'ilvl'))||'0',10)||0};}
function parseStyles(files,root){
  const bytes=files.get(root+'/styles.xml');
  const defaults={run:{fontFamily:'Calibri',fontSizePt:11},paragraph:{after:160,line:259,lineRule:'auto'}},styles={};
  if(!bytes)return{defaults,resolve:()=>({run:{},paragraph:{}})};
  const doc=xml(bytes),docDefaults=first(doc,'docDefaults');
  if(docDefaults){defaults.run=merge(defaults.run,parseRunProps(first(first(docDefaults,'rPrDefault'),'rPr')));defaults.paragraph=merge(defaults.paragraph,parseParagraphProps(first(first(docDefaults,'pPrDefault'),'pPr')));}
  all(doc,'style').forEach(s=>{if(val(s,'type')!=='paragraph')return;const id=val(s,'styleId');if(!id)return;styles[id]={id,name:val(first(s,'name')),basedOn:val(first(s,'basedOn')),run:parseRunProps(first(s,'rPr')),paragraph:parseParagraphProps(first(s,'pPr')),numbering:parseNumberingRef(first(s,'pPr'))};});
  const cache={};
  function resolve(id,seen){if(!id||!styles[id])return{run:{},paragraph:{},name:'',numbering:null};if(cache[id])return cache[id];seen=seen||new Set();if(seen.has(id))return{run:{},paragraph:{},name:styles[id].name||'',numbering:styles[id].numbering||null};seen.add(id);const own=styles[id],base=resolve(own.basedOn,seen);return cache[id]={run:merge(base.run,own.run),paragraph:merge(base.paragraph,own.paragraph),name:own.name||base.name||'',numbering:own.numbering||base.numbering||null};}
  return{defaults,resolve};
}
function cssRun(props){let css='';if(props.fontFamily){const family=String(props.fontFamily).split(';')[0].trim();css+='font-family:'+JSON.stringify(family)+',Arial,sans-serif;'};if(props.fontSizePt)css+='font-size:'+props.fontSizePt+'pt;';if(props.bold)css+='font-weight:700;';if(props.italic)css+='font-style:italic;';if(props.underline)css+='text-decoration:underline;';if(props.color)css+='color:'+props.color+';';return css}
function cssParagraph(props,baseRun){
  let css=cssRun(baseRun);
  if(props.alignment==='center')css+='text-align:center;';else if(props.alignment==='right')css+='text-align:right;';else if(props.alignment==='both'||props.alignment==='justify')css+='text-align:justify;';
  if(Number.isFinite(props.left)&&props.left)css+='margin-left:'+(props.left/20)+'pt;';
  if(Number.isFinite(props.right)&&props.right)css+='margin-right:'+(props.right/20)+'pt;';
  if(Number.isFinite(props.firstLine)&&props.firstLine)css+='text-indent:'+(props.firstLine/20)+'pt;';else if(Number.isFinite(props.hanging)&&props.hanging)css+='text-indent:-'+(props.hanging/20)+'pt;';
  const before=Number.isFinite(props.before)?props.before:0;const after=props.contextualSpacing?0:(Number.isFinite(props.after)?props.after:0);
  css+='margin-top:'+(before/20)+'pt;margin-bottom:'+(after/20)+'pt;';
  if(Number.isFinite(props.line)&&props.line>0){if(props.lineRule==='exact'||props.lineRule==='atLeast')css+='line-height:'+(props.line/20)+'pt;';else css+='line-height:'+(props.line/240)+';';}
  return css;
}
function packagePart(files,standardPath,legacyPath){return files.get(standardPath)||files.get(legacyPath)||null}
function normalizeBullet(text,font){const t=String(text||'');const cp=t.codePointAt(0)||0;if(cp===0xf0b7||t==='')return'•';if(cp===0xf0a7||t==='')return'▪';if(t==='o'&&/courier/i.test(font||''))return'○';return t||'•'}
function parseNumbering(files,root){
  const bytes=packagePart(files,root+'/numbering.xml',root==='word'?'documents/numbering.xml':'word/numbering.xml');if(!bytes)return{};const doc=xml(bytes),abstract={},out={};
  all(doc,'abstractNum').forEach(a=>{const id=val(a,'abstractNumId')||'0';abstract[id]={};all(a,'lvl').forEach(l=>{const ilvl=parseInt(val(l,'ilvl')||'0',10)||0,fmtEl=first(l,'numFmt'),txtEl=first(l,'lvlText'),pPr=first(l,'pPr'),ind=first(pPr,'ind'),rPr=first(l,'rPr'),fonts=first(rPr,'rFonts');const font=fonts?(val(fonts,'ascii')||val(fonts,'hAnsi')):'';const fmt=fmtEl?(val(fmtEl)||'decimal'):'decimal';let text=txtEl?(val(txtEl)||'%1.'):'%1.';if(fmt==='bullet')text=normalizeBullet(text,font);abstract[id][ilvl]={fmt,text,font,left:ind?num(val(ind,'left'),NaN):NaN,hanging:ind?num(val(ind,'hanging'),NaN):NaN,start:num(val(first(l,'start')),1)}})});
  all(doc,'num').forEach(n=>{const id=val(n,'numId')||'0',a=first(n,'abstractNumId'),aid=a?(val(a)||'0'):'0';out[id]=abstract[aid]||{}});return out;
}
function alpha(n,upper){let x=n,s='';while(x>0){x--;s=String.fromCharCode((upper?65:97)+(x%26))+s;x=Math.floor(x/26)}return s}
function roman(n){const pairs=[[1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],[50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];let out='';for(const [v,s] of pairs)while(n>=v){out+=s;n-=v}return out}
function listLabel(info,counters){const key=info.numId+':'+info.ilvl,c=(counters[key]||((info.start||1)-1))+1;counters[key]=c;Object.keys(counters).forEach(k=>{const parts=k.split(':');if(parts[0]===String(info.numId)&&Number(parts[1])>info.ilvl)delete counters[k]});if(info.fmt==='bullet')return info.text||'•';let value=String(c);if(info.fmt==='upperLetter')value=alpha(c,true);else if(info.fmt==='lowerLetter')value=alpha(c,false);else if(info.fmt==='upperRoman')value=roman(c);else if(info.fmt==='lowerRoman')value=roman(c).toLowerCase();return String(info.text||'%1.').replace(/%\d+/g,value)}
function mapSymbol(font,hex){const code=parseInt(String(hex||''),16);const f=String(font||'').toLowerCase();if(f.includes('wingdings')){if(code===0xf0e0)return'→';if(code===0xf0df)return'←';if(code===0xf0e1)return'←';if(code===0xf0e2)return'↔';if(code===0xf0a7)return'▪';if(code===0xf0fc)return'✓';}if(f.includes('symbol')&&code===0xf0b7)return'•';return code?String.fromCodePoint(code>=0xf000?0x25a1:code):''}
function textOf(node){return all(node,'t').map(t=>t.textContent||'').join('')}
function pageSpecFromSect(sect,styles,files,root,rels,partRenderer){
  const pgSz=first(sect,'pgSz'),pgMar=first(sect,'pgMar');
  const w=num(val(pgSz,'w'),12240),h=num(val(pgSz,'h'),15840),top=num(val(pgMar,'top'),1440),right=num(val(pgMar,'right'),1440),bottom=num(val(pgMar,'bottom'),1440),left=num(val(pgMar,'left'),1440),header=num(val(pgMar,'header'),720),footer=num(val(pgMar,'footer'),720);const px=t=>t/15;
  function related(kind){const ref=all(sect,kind+'Reference').find(x=>(val(x,'type')||'default')==='default')||first(sect,kind+'Reference');const rid=attr(ref,'id'),target=rid&&rels[rid];if(!target)return{html:'',text:''};const path=normalPath(root,target),bytes=files.get(path);return bytes&&partRenderer?partRenderer(path,bytes):{html:'',text:bytes?textOf(xml(bytes)).trim():''}}
  const hp=related('header'),fp=related('footer');
  return{widthPx:px(w),heightPx:px(h),marginTopPx:px(top),marginRightPx:px(right),marginBottomPx:px(bottom),marginLeftPx:px(left),headerDistancePx:px(header),footerDistancePx:px(footer),contentWidthPx:px(Math.max(1440,w-left-right)),contentHeightPx:px(Math.max(1440,h-top-bottom)),fontFamily:styles.defaults.run.fontFamily||'Calibri',fontSizePt:styles.defaults.run.fontSizePt||11,lineHeight:(styles.defaults.paragraph.line||259)/240,orientation:val(pgSz,'orient')||((w>h)?'landscape':'portrait'),headerHtml:hp.html,footerHtml:fp.html,headerText:hp.text,footerText:fp.text};
}
function paragraphInfo(p,numbering,styles){
  const pPr=first(p,'pPr'),styleId=val(first(pPr,'pStyle')),resolved=styles.resolve(styleId),directP=parseParagraphProps(pPr),directR=parseRunProps(first(pPr,'rPr'));let props=merge(styles.defaults.paragraph,resolved.paragraph,directP),baseRun=merge(styles.defaults.run,resolved.run,directR),tag='p',level=0;
  const styleName=(resolved.name||styleId||'');const hm=styleName.match(/Heading\s*([1-6])/i)||styleId.match(/Heading\s*([1-6])/i),title=/Title/i.test(styleName)||/Title/i.test(styleId);if(hm||title){level=hm?Math.min(6,Math.max(1,Number(hm[1])||1)):1;tag='h'+level}
  let listInfo=null;const numRef=parseNumberingRef(pPr)||resolved.numbering;if(numRef){const numId=numRef.numId||'0',ilvl=numRef.ilvl||0;listInfo=merge({numId,ilvl,fmt:'decimal',text:'%1.',start:1},numbering[numId]&&numbering[numId][ilvl]);if(Number.isFinite(listInfo.left))props.left=listInfo.left;if(Number.isFinite(listInfo.hanging))props.hanging=listInfo.hanging;}
  return{tag,level,styleId,props,baseRun,listInfo,style:cssParagraph(props,baseRun),pageBreakBefore:!!props.pageBreakBefore};
}
function renderRun(run,info,mediaUrls,state){
  const drawing=first(run,'drawing')||first(run,'pict');if(drawing){const blip=first(drawing,'blip'),rid=attr(blip,'embed');if(rid&&mediaUrls[rid]){const extent=first(drawing,'extent'),cx=num(extent&&extent.getAttribute('cx'),0),cy=num(extent&&extent.getAttribute('cy'),0),style=(cx&&cy)?' style="width:'+(cx/9525)+'px;height:'+(cy/9525)+'px"':'';state.visible=true;return'<img src="'+mediaUrls[rid]+'" data-docx-rel-id="'+esc(rid)+'" alt="Embedded image"'+style+'>'}return''}
  const parts=[];for(const rc of Array.from(run.children)){
    if(rc.localName==='lastRenderedPageBreak'&&!state.visible&&!parts.length)state.softPageBreakBefore=true;
    else if(rc.localName==='t'){parts.push(esc(rc.textContent));if(rc.textContent)state.visible=true;}
    else if(rc.localName==='sym'){const mapped=mapSymbol(val(rc,'font'),val(rc,'char'));parts.push(esc(mapped));if(mapped)state.visible=true;}
    else if(rc.localName==='tab'){parts.push('&emsp;');state.visible=true;}
    else if(rc.localName==='br'){if(val(rc,'type')==='page'&&!state.visible&&!parts.length)state.hardPageBreakBefore=true;else parts.push('<br>');}
  }
  if(!parts.length)return'';const runProps=merge(info.baseRun,parseRunProps(first(run,'rPr')));return'<span style="'+cssRun(runProps)+'">'+parts.join('')+'</span>';
}
function renderInline(node,info,mediaUrls,state){let out='';for(const child of Array.from(node.children||[])){
  const name=child.localName;
  if(name==='r')out+=renderRun(child,info,mediaUrls,state);
  else if(name==='hyperlink')out+='<span class="hyperlink">'+renderInline(child,info,mediaUrls,state)+'</span>';
  else if(name==='ins')out+='<span class="tracked-insert" data-docx-tracked="insert">'+renderInline(child,info,mediaUrls,state)+'</span>';
  else if(name==='del')out+='<span class="tracked-delete" data-docx-tracked="delete">'+renderInline(child,info,mediaUrls,state)+'</span>';
  else if(name==='sdt'||name==='sdtContent')out+='<span class="content-control">'+renderInline(child,info,mediaUrls,state)+'</span>';
  else if(name!=='pPr')out+=renderInline(child,info,mediaUrls,state);
 }return out}
function paragraphBlock(p,numbering,styles,mediaUrls,listCounters,sourceIndex,sourceSubIndex){
  const info=paragraphInfo(p,numbering,styles),state={visible:false,softPageBreakBefore:false,hardPageBreakBefore:info.pageBreakBefore},parts=renderInline(p,info,mediaUrls,state),html=parts||'&nbsp;';let final;
  if(info.listInfo){const label=listLabel(info.listInfo,listCounters),hanging=Number.isFinite(info.listInfo.hanging)?info.listInfo.hanging:360;final='<p class="doc-list" data-list-num-id="'+esc(info.listInfo.numId)+'" data-list-level="'+info.listInfo.ilvl+'" data-list-format="'+esc(info.listInfo.fmt)+'" style="'+info.style+'"><span class="list-label" contenteditable="false" style="width:'+(hanging/20)+'pt">'+esc(label)+'</span>'+html+'</p>';}
  else final='<'+info.tag+' style="'+info.style+'">'+html+'</'+info.tag+'>';
  return{type:info.tag,html:final,text:textOf(p),outlineLevel:info.level,softPageBreakBefore:state.softPageBreakBefore,hardPageBreakBefore:state.hardPageBreakBefore,keepNext:!!info.props.keepNext,styleId:info.styleId,sourceIndex,sourceSubIndex};
}
function docxColor(value,fallback='#000000'){const c=String(value||'').replace(/^#/,'');return /^[0-9a-f]{6}$/i.test(c)?'#'+c:fallback}
function docxBorderCss(border){if(!border)return'';const style=val(border,'val')||'single';if(['nil','none'].includes(style))return'none';const sz=Math.max(2,num(val(border,'sz'),8))/8;const cssStyle=style==='double'?'double':(/dash/i.test(style)?'dashed':(/dot/i.test(style)?'dotted':'solid'));return Math.max(1,sz*1.333).toFixed(2)+'px '+cssStyle+' '+docxColor(val(border,'color'),'#70757d')}
function cellCss(tcPr,tableBorders){const css=[];if(!tcPr)return'';const tcW=first(tcPr,'tcW'),w=num(val(tcW,'w'),0);if(w>0)css.push('width:'+(w/20).toFixed(2)+'pt');const shd=first(tcPr,'shd'),fill=val(shd,'fill');if(fill&&fill!=='auto')css.push('background-color:'+docxColor(fill,'transparent'));const v=val(first(tcPr,'vAlign'),'val');if(v)css.push('vertical-align:'+(v==='center'?'middle':v));const tcMar=first(tcPr,'tcMar');if(tcMar){for(const side of ['top','right','bottom','left']){const x=first(tcMar,side),n=num(val(x,'w'),NaN);if(Number.isFinite(n))css.push('padding-'+side+':'+(n/20).toFixed(2)+'pt')}}const borders=first(tcPr,'tcBorders')||tableBorders;for(const side of ['top','right','bottom','left']){const b=first(borders,side),v=docxBorderCss(b);if(v)css.push('border-'+side+':'+v)}return css.join(';')}
function tableBlock(tbl,numbering,styles,mediaUrls,listCounters,sourceIndex,sourceSubIndex){const tblPr=first(tbl,'tblPr'),tblGrid=first(tbl,'tblGrid'),grid=tblGrid?Array.from(tblGrid.children).filter(x=>x.localName==='gridCol').map(x=>num(val(x,'w'),0)):[],tblBorders=first(tblPr,'tblBorders');const tableCss=['border-collapse:collapse','table-layout:fixed','max-width:100%'];const tblW=first(tblPr,'tblW'),tw=num(val(tblW,'w'),0),twType=val(tblW,'type');if(tw>0)tableCss.push('width:'+(twType==='pct'?(tw/50)+'%':(tw/20).toFixed(2)+'pt'));else tableCss.push('width:100%');const jc=val(first(tblPr,'jc'),'val');if(jc==='center')tableCss.push('margin-left:auto','margin-right:auto');else if(jc==='right')tableCss.push('margin-left:auto');let h='<table class="docx-table" style="'+tableCss.join(';')+'">';if(grid.length){h+='<colgroup>';for(const w of grid)h+='<col style="width:'+(w/20).toFixed(2)+'pt">';h+='</colgroup>'}const rows=Array.from(tbl.children).filter(x=>x.localName==='tr'),built=[],active={};for(let ri=0;ri<rows.length;ri++){const tr=rows[ri],entries=[];let col=0;for(const tc of Array.from(tr.children).filter(x=>x.localName==='tc')){const tcPr=first(tc,'tcPr'),span=Math.max(1,num(val(first(tcPr,'gridSpan')),1)),vm=first(tcPr,'vMerge'),vmVal=vm?(val(vm,'val')||'continue'):'';if(vm&&vmVal!=='restart'){const anchor=active[col];if(anchor){anchor.rowspan++;for(let k=0;k<span;k++)active[col+k]=anchor;col+=span;continue}}const paras=Array.from(tc.children).filter(x=>x.localName==='p');const body=paras.length?paras.map((p,i)=>paragraphBlock(p,numbering,styles,mediaUrls,listCounters,sourceIndex,sourceSubIndex+i).html).join(''):'&nbsp;';const entry={col,span,rowspan:1,style:cellCss(tcPr,tblBorders),body};entries.push(entry);if(vm&&vmVal==='restart')for(let k=0;k<span;k++)active[col+k]=entry;else for(let k=0;k<span;k++)delete active[col+k];col+=span}built.push({tr,entries})}for(const row of built){const trPr=first(row.tr,'trPr'),trH=first(trPr,'trHeight'),height=num(val(trH,'val'),0);h+='<tr'+(height>0?' style="height:'+(height/20).toFixed(2)+'pt"':'')+'>';for(const e of row.entries){h+='<td'+(e.span>1?' colspan="'+e.span+'"':'')+(e.rowspan>1?' rowspan="'+e.rowspan+'"':'')+(e.style?' style="'+e.style+'"':'')+'>'+e.body+'</td>'}h+='</tr>'}h+='</table>';return{type:'table',html:h,text:textOf(tbl),outlineLevel:0,softPageBreakBefore:false,hardPageBreakBefore:false,sourceIndex,sourceSubIndex}}
async function parse(buffer){
  currentXmlBudget=global.InkDeskRuntime?global.InkDeskRuntime.createXmlBudget():null;let mediaUrls={};
  try{
    const files=await unzip(buffer);if(global.InkDeskRuntime&&global.JSZip){const validationZip=await JSZip.loadAsync(buffer);await global.InkDeskRuntime.validateOoxmlRelationships(validationZip,{xmlBudget:currentXmlBudget})}const mainPath=files.has('word/document.xml')?'word/document.xml':files.has('documents/document.xml')?'documents/document.xml':'';
    if(!mainPath)throw new Error('DOCX does not contain word/document.xml.');
    const root=mainPath.split('/')[0],relsPath=root+'/_rels/document.xml.rels',doc=xml(files.get(mainPath),mainPath),styles=parseStyles(files,root),relsDoc=files.get(relsPath),rels=relsDoc?parseRels(xml(relsDoc,relsPath)):{},numbering=parseNumbering(files,root),listCounters={};
    for(const [id,target] of Object.entries(rels)){if(/media\//i.test(target)){const path=normalPath(root,target),bytes=files.get(path);if(bytes){const ext=path.split('.').pop().toLowerCase();if(!['png','jpg','jpeg','gif','webp'].includes(ext))continue;const mime=ext==='png'?'image/png':ext==='gif'?'image/gif':ext==='webp'?'image/webp':'image/jpeg';mediaUrls[id]=URL.createObjectURL(new Blob([bytes],{type:mime}))}}}
    function renderRelatedPart(path,bytes){
      const partDoc=xml(bytes,path),partDir=path.split('/').slice(0,-1).join('/'),relsPath=partDir+'/_rels/'+path.split('/').pop()+'.rels',partRels=files.get(relsPath)?parseRels(xml(files.get(relsPath),relsPath)):{},partMedia={};
      for(const [id,target] of Object.entries(partRels)){if(!/media\//i.test(target))continue;const mediaPath=normalPath(partDir,target),data=files.get(mediaPath);if(!data)continue;const ext=mediaPath.split('.').pop().toLowerCase(),mime=ext==='png'?'image/png':ext==='gif'?'image/gif':ext==='webp'?'image/webp':'image/jpeg';const url=URL.createObjectURL(new Blob([data],{type:mime}));mediaUrls[path+':'+id]=url;partMedia[id]=url;}
      let html='',partCounters={};const partRoot=partDoc.documentElement;function renderPartNode(node,sub=0){if(node.localName==='p')return paragraphBlock(node,numbering,styles,partMedia,partCounters,-1,sub).html;if(node.localName==='tbl')return tableBlock(node,numbering,styles,partMedia,partCounters,-1,sub).html;if(node.localName==='sdt'||node.localName==='sdtContent'){const content=first(node,'sdtContent')||node;return Array.from(content.children||[]).map((n,i)=>renderPartNode(n,sub+i)).join('')}return''}for(const [i,node] of Array.from(partRoot.children||[]).entries())html+=renderPartNode(node,i);
      return{html,text:textOf(partDoc).trim()};
    }
    const blocks=[],outline=[],body=first(doc,'body'),renderedSourceIndexes=[];if(!body)throw new Error('DOCX body is missing.');let sectionStart=0;
    const bodyChildren=Array.from(body.children);
    function addBlock(block){blocks.push(block);if(block.outlineLevel&&block.text.trim())outline.push({level:block.outlineLevel,text:block.text.trim(),blockIndex:blocks.length-1});}
    for(let sourceIndex=0;sourceIndex<bodyChildren.length;sourceIndex++){
      const child=bodyChildren[sourceIndex];if(child.localName==='sectPr')continue;let made=0;
      if(child.localName==='p'){addBlock(paragraphBlock(child,numbering,styles,mediaUrls,listCounters,sourceIndex,0));made=1;}
      else if(child.localName==='tbl'){addBlock(tableBlock(child,numbering,styles,mediaUrls,listCounters,sourceIndex,0));made=1;}
      else if(child.localName==='sdt'){
        const content=first(child,'sdtContent')||child;for(const nested of Array.from(content.children)){let block=null;if(nested.localName==='p')block=paragraphBlock(nested,numbering,styles,mediaUrls,listCounters,sourceIndex,made);else if(nested.localName==='tbl')block=tableBlock(nested,numbering,styles,mediaUrls,listCounters,sourceIndex,made);if(block){block.html='<div class="content-control content-control-block" data-docx-content-control="true">'+block.html+'</div>';addBlock(block);made++;}}
      }
      if(made)renderedSourceIndexes.push(sourceIndex);
      const localSect=child.localName==='p'?first(first(child,'pPr'),'sectPr'):null;if(localSect){const spec=pageSpecFromSect(localSect,styles,files,root,rels,renderRelatedPart);for(let j=sectionStart;j<blocks.length;j++)blocks[j].pageSpec=spec;if(sectionStart<blocks.length)blocks[sectionStart].sectionStart=true;sectionStart=blocks.length;}
    }
    const finalSect=Array.from(body.children).reverse().find(x=>x.localName==='sectPr')||null,finalSpec=pageSpecFromSect(finalSect,styles,files,root,rels,renderRelatedPart);for(let j=sectionStart;j<blocks.length;j++)blocks[j].pageSpec=finalSpec;if(sectionStart<blocks.length)blocks[sectionStart].sectionStart=true;if(blocks.length)blocks[0].sectionStart=false;
    let inheritedHeader='',inheritedFooter='';for(const block of blocks){const spec=block.pageSpec||finalSpec;if(spec.headerText)inheritedHeader=spec.headerText;else spec.headerText=inheritedHeader;if(spec.footerText)inheritedFooter=spec.footerText;else spec.footerText=inheritedFooter;}
    return{blocks,outline,mediaUrls,pageSpec:blocks[0]&&blocks[0].pageSpec?blocks[0].pageSpec:finalSpec,sourceContext:{mainPath,root,renderedSourceIndexes:Array.from(new Set(renderedSourceIndexes)),originalBlockCount:bodyChildren.length}};
  }catch(error){
    if(global.InkDeskRuntime)global.InkDeskRuntime.revokeObjectUrls(Object.values(mediaUrls));else Object.values(mediaUrls).forEach(url=>URL.revokeObjectURL(url));
    throw error;
  }
}
global.LocalDocxParser={parse};
})(window);

(function(global){
'use strict';

const NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main';
const REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const PKG_REL='http://schemas.openxmlformats.org/package/2006/relationships';

function xml(text,context='XLSX package part'){
  if(global.InkDeskRuntime)return global.InkDeskRuntime.parseXml(text,context);
  const d=new DOMParser().parseFromString(text,'application/xml');
  if(d.querySelector('parsererror'))throw new Error('Invalid XML in '+context);
  return d;
}
function serializeXml(doc){return new XMLSerializer().serializeToString(doc)}
function childText(node,name){if(!node)return'';const n=[...node.children].find(x=>x.localName===name);return n?n.textContent:''}
function children(node,name){return node?[...node.children].filter(x=>x.localName===name):[]}
function localOne(node,name){return node?[...node.querySelectorAll('*')].find(n=>n.localName===name):null}
function localAll(node,name){return node?[...node.querySelectorAll('*')].filter(n=>n.localName===name):[]}
function create(doc,name,ns=NS){return doc.createElementNS(ns,name)}
function colName(n){let s='';while(n>=0){s=String.fromCharCode(n%26+65)+s;n=Math.floor(n/26)-1}return s}
function decodeRef(ref){const m=/^([A-Z]+)(\d+)$/i.exec(ref||'A1');if(!m)return{r:0,c:0};let c=0;for(const ch of m[1].toUpperCase())c=c*26+ch.charCodeAt(0)-64;return{r:+m[2]-1,c:c-1}}
function encodeRef(r,c){return colName(c)+(r+1)}
function decodeRange(s){const [a,b=a]=(s||'A1').split(':');const p1=decodeRef(a.replace(/\$/g,'')),p2=decodeRef(b.replace(/\$/g,''));return{r1:Math.min(p1.r,p2.r),c1:Math.min(p1.c,p2.c),r2:Math.max(p1.r,p2.r),c2:Math.max(p1.c,p2.c)}}
function escapeXml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function normalizePath(base,target){
  if(!target)return'';
  if(target.startsWith('/'))return target.slice(1);
  const parts=base.split('/').slice(0,-1).concat(target.split('/')),out=[];
  for(const part of parts){if(!part||part==='.')continue;if(part==='..')out.pop();else out.push(part)}
  return out.join('/');
}
function relsPathFor(path){const a=path.split('/'),name=a.pop();return a.concat(['_rels',name+'.rels']).join('/')}
function emuPx(v){return(+v||0)/9525}
function widthPx(w){const n=+w||8.43;return Math.max(18,Math.min(720,Math.floor(n*7+5)))}
function pxWidth(px){return Math.max(0.1,(Math.max(18,+px||68)-5)/7)}
function heightPx(h){return Math.max(12,Math.min(420,Math.round((+h||15)*1.333)))}
function pxHeight(px){return Math.max(1,(+px||20)/1.333)}
function sameObject(a,b){return JSON.stringify(a||{})===JSON.stringify(b||{})}
function cloneCell(cell){
  if(!cell)return null;
  return{v:cell.v,f:cell.f||'',styleId:+(cell.styleId||0),t:cell.t||'',display:cell.display??''};
}
function sameCell(a,b){
  if(!a&&!b)return true;if(!a||!b)return false;
  return String(a.f||'')===String(b.f||'')&&String(a.t||'')===String(b.t||'')&&Number(a.styleId||0)===Number(b.styleId||0)&&String(a.v??'')===String(b.v??'');
}
function rangeValuesFromFormula(formula,sheets,currentSheet){
  const m=/^(?:(?:'((?:[^']|'')+)'|([^'!]+))!)?\$?([A-Z]{1,3})\$?(\d+):\$?([A-Z]{1,3})\$?(\d+)$/i.exec(String(formula||'').trim());
  if(!m)return[];
  const sheetName=(m[1]?m[1].replace(/''/g,"'"):m[2])||currentSheet.name;
  const target=sheets.find(s=>s.name===sheetName)||currentSheet;
  const q=decodeRange(`${m[3]}${m[4]}:${m[5]}${m[6]}`),out=[];
  for(let r=q.r1;r<=q.r2;r++)for(let c=q.c1;c<=q.c2;c++){const cell=target.cells.get(encodeRef(r,c));out.push(cell?.calculated??cell?.v??'')}
  return out;
}
function resolveChartData(sheets){
  for(const sheet of sheets)for(const drawing of sheet.drawings||[]){
    if(drawing.kind!=='chart')continue;
    for(const series of drawing.series||[]){
      if(!series.categories?.length&&series.categoryFormula)series.categories=rangeValuesFromFormula(series.categoryFormula,sheets,sheet).map(String);
      if(!series.values?.length&&series.valueFormula)series.values=rangeValuesFromFormula(series.valueFormula,sheets,sheet).map(v=>Number(v)||0);
      if(!series.name&&series.nameFormula){const vals=rangeValuesFromFormula(series.nameFormula+':'+series.nameFormula,sheets,sheet);series.name=String(vals[0]??'Series')}
    }
  }
}
function chartCachedValues(node){
  const pts=localAll(node,'pt').map(pt=>({idx:+(pt.getAttribute('idx')||0),value:childText(pt,'v')})).sort((a,b)=>a.idx-b.idx);
  return pts.map(p=>p.value);
}
async function parseChart(read,chartPath){
  const raw=await read(chartPath);if(!raw)return null;
  const d=xml(raw),plot=localOne(d,'plotArea');if(!plot)return null;
  const chartNode=[...plot.children].find(n=>/Chart$/.test(n.localName));if(!chartNode)return null;
  const titleNode=localOne(d,'title');const title=titleNode?localAll(titleNode,'t').map(n=>n.textContent).join(''):'Chart';
  const series=[];
  for(const ser of [...chartNode.children].filter(n=>n.localName==='ser')){
    const tx=children(ser,'tx')[0],cat=children(ser,'cat')[0],val=children(ser,'val')[0]||children(ser,'yVal')[0];
    const name=tx?localAll(tx,'t').map(n=>n.textContent).join(''):'';
    const nameFormula=tx?childText(localOne(tx,'strRef')||localOne(tx,'numRef'),'f'):'';
    const categoryFormula=cat?childText(localOne(cat,'strRef')||localOne(cat,'numRef'),'f'):'';
    const valueFormula=val?childText(localOne(val,'numRef')||localOne(val,'strRef'),'f'):'';
    const categories=cat?chartCachedValues(localOne(cat,'strCache')||localOne(cat,'numCache')):[];
    const values=val?chartCachedValues(localOne(val,'numCache')||localOne(val,'strCache')).map(v=>Number(v)||0):[];
    series.push({name:name||'',nameFormula,categoryFormula,valueFormula,categories,values});
  }
  return{title,chartType:chartNode.localName,series};
}
async function parseDrawings(zip,read,sheetPath,sheetDoc){
  const result=[];const drawingNode=[...sheetDoc.querySelectorAll('*')].find(n=>n.localName==='drawing');
  if(!drawingNode)return result;
  const sheetRelsRaw=await read(relsPathFor(sheetPath));if(!sheetRelsRaw)return result;
  const sheetRels=xml(sheetRelsRaw),sheetRelMap={};
  sheetRels.querySelectorAll('Relationship').forEach(r=>sheetRelMap[r.getAttribute('Id')]={target:r.getAttribute('Target'),type:r.getAttribute('Type')||''});
  const rid=drawingNode.getAttributeNS(REL,'id')||drawingNode.getAttribute('r:id'),drawRel=sheetRelMap[rid];if(!drawRel)return result;
  const drawingPath=normalizePath(sheetPath,drawRel.target),drawingRaw=await read(drawingPath);if(!drawingRaw)return result;
  const drawingDoc=xml(drawingRaw),drawingRelsRaw=await read(relsPathFor(drawingPath)),drawingRelMap={};
  if(drawingRelsRaw){const rd=xml(drawingRelsRaw);rd.querySelectorAll('Relationship').forEach(r=>drawingRelMap[r.getAttribute('Id')]={target:r.getAttribute('Target'),type:r.getAttribute('Type')||''})}
  const marker=(anchor,name)=>{const n=[...anchor.children].find(x=>x.localName===name);return{c:+(localOne(n,'col')?.textContent||0),r:+(localOne(n,'row')?.textContent||0),x:emuPx(localOne(n,'colOff')?.textContent||0),y:emuPx(localOne(n,'rowOff')?.textContent||0)}};
  for(const anchor of [...drawingDoc.documentElement.children].filter(n=>/CellAnchor$/.test(n.localName))){
    const from=marker(anchor,'from'),toNode=[...anchor.children].find(x=>x.localName==='to'),to=toNode?marker(anchor,'to'):null;
    const ext=[...anchor.children].find(x=>x.localName==='ext'),size=ext?{w:emuPx(ext.getAttribute('cx')),h:emuPx(ext.getAttribute('cy'))}:null;
    const pic=[...anchor.children].find(x=>x.localName==='pic');
    if(pic){
      const blip=localOne(pic,'blip'),embed=blip?.getAttributeNS(REL,'embed')||blip?.getAttribute('r:embed'),rel=drawingRelMap[embed];if(!rel)continue;
      const mediaPath=normalizePath(drawingPath,rel.target),file=zip.file(mediaPath);if(!file)continue;
      const extName=(mediaPath.split('.').pop()||'png').toLowerCase(),mime=extName==='jpg'||extName==='jpeg'?'image/jpeg':extName==='gif'?'image/gif':extName==='svg'?'image/svg+xml':'image/png';
      const blob=await file.async('blob');result.push({kind:'image',url:URL.createObjectURL(new Blob([blob],{type:mime})),from,to,size,name:localOne(pic,'cNvPr')?.getAttribute('name')||'Embedded image'});continue;
    }
    const graphicFrame=[...anchor.children].find(x=>x.localName==='graphicFrame');
    if(graphicFrame){
      const chartNode=localOne(graphicFrame,'chart'),chartRid=chartNode?.getAttributeNS(REL,'id')||chartNode?.getAttribute('r:id'),rel=drawingRelMap[chartRid];
      if(rel){const chartPath=normalizePath(drawingPath,rel.target),chart=await parseChart(read,chartPath);if(chart)result.push({kind:'chart',from,to,size,name:localOne(graphicFrame,'cNvPr')?.getAttribute('name')||chart.title,...chart,sourcePath:chartPath})}
      continue;
    }
    const sp=[...anchor.children].find(x=>x.localName==='sp');
    if(sp){
      const texts=localAll(sp,'t').map(n=>n.textContent).join('\n'),spPr=[...sp.children].find(n=>n.localName==='spPr'),ln=spPr?[...spPr.children].find(n=>n.localName==='ln'):null,solid=spPr?[...spPr.children].find(n=>n.localName==='solidFill'):null;
      const lineColor=ln?([...[...ln.children].find(n=>n.localName==='solidFill')?.children||[]].find(n=>/Clr$/.test(n.localName))?.getAttribute('val')||'000000'):'000000';
      const fillColor=solid?([...solid.children].find(n=>/Clr$/.test(n.localName))?.getAttribute('val')||'FFFFFF'):'transparent',run=localOne(sp,'rPr');
      result.push({kind:'shape',from,to,size,text:texts,fill:fillColor==='transparent'?'transparent':'#'+fillColor,line:'#'+lineColor,lineWidth:Math.max(1,emuPx(ln?.getAttribute('w')||9525)),fontSize:Math.max(8,+(run?.getAttribute('sz')||1000)/100),bold:run?.getAttribute('b')==='1'});
    }
  }
  return result;
}
function argb(v){if(!v)return'';v=v.replace(/^#/,'');if(v.length===8)v=v.slice(2);return/^[0-9a-f]{6}$/i.test(v)?'#'+v:''}
function parseStyles(raw){
  const out=[];if(!raw)return out;const d=xml(raw),root=d.documentElement;
  const fonts=children(root,'fonts')[0],fills=children(root,'fills')[0],borders=children(root,'borders')[0];
  const fontList=fonts?children(fonts,'font').map(f=>({name:children(f,'name')[0]?.getAttribute('val')||'',size:+(children(f,'sz')[0]?.getAttribute('val')||0),bold:!!children(f,'b').length,italic:!!children(f,'i').length,underline:!!children(f,'u').length,strike:!!children(f,'strike').length,color:argb(children(f,'color')[0]?.getAttribute('rgb')||'')})):[];
  const fillList=fills?children(fills,'fill').map(f=>{const p=children(f,'patternFill')[0];return argb(children(p,'fgColor')[0]?.getAttribute('rgb')||'')}):[];
  const borderList=borders?children(borders,'border').map(b=>{const o={};for(const side of['left','right','top','bottom']){const n=children(b,side)[0];if(n&&n.getAttribute('style'))o[side]={style:n.getAttribute('style'),color:argb(children(n,'color')[0]?.getAttribute('rgb')||'')||'#b7bcc4'}}return o}):[];
  const cellXfs=children(root,'cellXfs')[0];
  if(cellXfs)children(cellXfs,'xf').forEach(x=>{const al=children(x,'alignment')[0];out.push({font:fontList[+(x.getAttribute('fontId')||0)]||{},fill:fillList[+(x.getAttribute('fillId')||0)]||'',border:borderList[+(x.getAttribute('borderId')||0)]||{},align:al?.getAttribute('horizontal')||'',vertical:al?.getAttribute('vertical')||'',wrap:al?.getAttribute('wrapText')==='1',rotation:+(al?.getAttribute('textRotation')||0),numFmtId:+(x.getAttribute('numFmtId')||0)})});
  return out;
}
function formatValue(v,cell){if(v==null)return'';if(cell?.t==='b')return v?'TRUE':'FALSE';return v}
async function parseTableParts(read,sheetPath,sheetDoc){
  const result=[],relsRaw=await read(relsPathFor(sheetPath));if(!relsRaw)return result;
  const rels=xml(relsRaw),map={};rels.querySelectorAll('Relationship').forEach(r=>map[r.getAttribute('Id')]=r.getAttribute('Target'));
  for(const tp of localAll(sheetDoc,'tablePart')){
    const rid=tp.getAttributeNS(REL,'id')||tp.getAttribute('r:id'),target=map[rid];if(!target)continue;
    const path=normalizePath(sheetPath,target),raw=await read(path);if(!raw)continue;const d=xml(raw),root=d.documentElement;
    result.push({path,ref:root.getAttribute('ref')||'',name:root.getAttribute('displayName')||root.getAttribute('name')||'Table',style:localOne(root,'tableStyleInfo')?.getAttribute('name')||''});
  }
  return result;
}
async function parseWorkbook(buffer,fileName='Workbook.xlsx'){
  if(!global.JSZip)throw new Error('JSZip did not load');
  if(global.InkDeskRuntime)global.InkDeskRuntime.validateZipPackage(buffer,fileName);
  const zip=await JSZip.loadAsync(buffer),read=async p=>zip.file(p)?zip.file(p).async('text'):'';
  const wbRaw=await read('xl/workbook.xml');if(!wbRaw)throw new Error('This is not a supported XLSX workbook');
  const workbookXml=xml(wbRaw),relsRaw=await read('xl/_rels/workbook.xml.rels');if(!relsRaw)throw new Error('Workbook relationships are missing');
  const relsXml=xml(relsRaw),relMap={};relsXml.querySelectorAll('Relationship').forEach(r=>relMap[r.getAttribute('Id')]=r.getAttribute('Target'));
  const shared=[],ss=await read('xl/sharedStrings.xml');if(ss){const d=xml(ss);localAll(d,'si').forEach(si=>{let v='';localAll(si,'t').forEach(t=>v+=t.textContent);shared.push(v)})}
  const styles=parseStyles(await read('xl/styles.xml')),definedPrintAreas={};
  localAll(workbookXml,'definedName').forEach(n=>{if(n.getAttribute('name')==='_xlnm.Print_Area'){const local=+(n.getAttribute('localSheetId')||-1);if(local>=0)definedPrintAreas[local]=(n.textContent||'').split('!').pop().replace(/\$/g,'')}});
  const sheets=[];
  for(const [sheetIndex,s] of localAll(workbookXml,'sheet').entries()){
    const name=s.getAttribute('name')||'Sheet',state=s.getAttribute('state')||'visible',rid=s.getAttributeNS(REL,'id')||s.getAttribute('r:id');let target=relMap[rid]||'';
    if(target.startsWith('/'))target=target.slice(1);else if(!target.startsWith('xl/'))target='xl/'+target.replace(/^\.\//,'');
    const raw=await read(target);if(!raw)continue;const doc=xml(raw),cells=new Map(),originalCells=new Map();let maxR=39,maxC=15;
    localAll(doc,'c').filter(c=>c.parentElement?.localName==='row').forEach(c=>{
      const cellRef=c.getAttribute('r');if(!cellRef)return;const pos=decodeRef(cellRef);maxR=Math.max(maxR,pos.r);maxC=Math.max(maxC,pos.c);
      const t=c.getAttribute('t')||'',f=childText(c,'f');let v=childText(c,'v');
      if(t==='s')v=shared[+v]??'';else if(t==='inlineStr'){v='';localAll(c,'t').forEach(n=>v+=n.textContent)}else if(t==='b')v=v==='1';else if(v!==''&&!isNaN(Number(v)))v=Number(v);
      const styleId=+(c.getAttribute('s')||0),cell={v,f,styleId,style:styles[styleId]||{},t:t||typeof v,display:formatValue(v,{t})};cells.set(cellRef,cell);originalCells.set(cellRef,cloneCell(cell));
    });
    const merges=[];localAll(doc,'mergeCell').forEach(m=>{const x=m.getAttribute('ref');if(x)merges.push(x)});
    const sfp=localOne(doc,'sheetFormatPr'),defaultColWidth=widthPx(sfp?.getAttribute('defaultColWidth')||8.43),defaultRowHeight=heightPx(sfp?.getAttribute('defaultRowHeight')||15),widths={};
    localAll(doc,'col').forEach(c=>{const min=+(c.getAttribute('min')||1),max=+(c.getAttribute('max')||min),w=+(c.getAttribute('width')||8.43);for(let i=min-1;i<max;i++)widths[i]=widthPx(w)});
    const heights={};localAll(doc,'row').forEach(r=>{if(r.hasAttribute('ht'))heights[+(r.getAttribute('r')||1)-1]=heightPx(r.getAttribute('ht'))});
    const dim=localOne(doc,'dimension')?.getAttribute('ref');if(dim){const dr=decodeRange(dim);maxR=Math.max(maxR,dr.r2);maxC=Math.max(maxC,dr.c2)}
    const pm=localOne(doc,'pageMargins'),ps=localOne(doc,'pageSetup'),pane=localOne(doc,'pane'),filter=localOne(doc,'autoFilter');
    const margins=pm?Object.fromEntries(['left','right','top','bottom','header','footer'].map(k=>[k,+(pm.getAttribute(k)||0)])):{};
    const pageSetup=ps?{orientation:ps.getAttribute('orientation')||'',paperSize:+(ps.getAttribute('paperSize')||0),scale:+(ps.getAttribute('scale')||0),fitToWidth:+(ps.getAttribute('fitToWidth')||0),fitToHeight:+(ps.getAttribute('fitToHeight')||0)}:{};
    const drawings=await parseDrawings(zip,read,target,doc),tables=await parseTableParts(read,target,doc);
    sheets.push({name,state,path:target,xml:raw,cells,originalCells,merges,originalMerges:[...merges],widths,originalWidths:{...widths},heights,originalHeights:{...heights},defaultColWidth,defaultRowHeight,drawings,tables,maxR:Math.min(maxR+12,600),maxC:Math.min(maxC+6,100),printArea:definedPrintAreas[sheetIndex]||'',margins,pageSetup,freezePane:pane?{xSplit:+(pane.getAttribute('xSplit')||0),ySplit:+(pane.getAttribute('ySplit')||0),topLeftCell:pane.getAttribute('topLeftCell')||'',state:pane.getAttribute('state')||''}:null,autoFilter:filter?.getAttribute('ref')||'',hasConditionalFormatting:!!localOne(doc,'conditionalFormatting'),hasDataValidation:!!localOne(doc,'dataValidation')});
  }
  if(!sheets.length)throw new Error('No worksheets were found');resolveChartData(sheets);
  let active=+(localOne(workbookXml,'workbookView')?.getAttribute('activeTab')||0);active=Math.min(Math.max(0,active),sheets.length-1);if(sheets[active]?.state!=='visible'){const visible=sheets.findIndex(s=>s.state==='visible');if(visible>=0)active=visible}
  return{zip,sheets,active,fileName,loaded:true,legacy:false,images:[],workbookXml:wbRaw};
}
function createBlank(){return{zip:null,sheets:[{name:'Sheet1',state:'visible',path:'xl/worksheets/sheet1.xml',xml:'',cells:new Map(),originalCells:new Map(),merges:[],originalMerges:[],widths:{},originalWidths:{},heights:{},originalHeights:{},defaultColWidth:68,defaultRowHeight:20,drawings:[],tables:[],maxR:99,maxC:25}],active:0,fileName:'Untitled.xlsx',loaded:false}}
function writeCell(doc,node,cell){
  const keep=[...node.children].filter(ch=>!['f','v','is'].includes(ch.localName));for(const ch of[...node.children])if(!keep.includes(ch))node.removeChild(ch);
  node.removeAttribute('t');if(cell.styleId)node.setAttribute('s',String(cell.styleId));else node.removeAttribute('s');
  if(cell.f){const f=create(doc,'f');f.textContent=String(cell.f).replace(/^=/,'');node.appendChild(f);const cached=cell.calculated??cell.v;if(cached!==''&&cached!=null&&Number.isFinite(Number(cached))){const v=create(doc,'v');v.textContent=String(cached);node.appendChild(v)}return}
  if(typeof cell.v==='string'){
    node.setAttribute('t','inlineStr');const is=create(doc,'is'),t=create(doc,'t');t.setAttributeNS('http://www.w3.org/XML/1998/namespace','xml:space','preserve');t.textContent=cell.v;is.appendChild(t);node.appendChild(is);
  }else if(typeof cell.v==='boolean'){
    node.setAttribute('t','b');const v=create(doc,'v');v.textContent=cell.v?'1':'0';node.appendChild(v);
  }else if(cell.v!==''&&cell.v!=null){const v=create(doc,'v');v.textContent=String(cell.v);node.appendChild(v)}
}
function findRow(sheetData,rowNumber){return[...sheetData.children].find(r=>r.localName==='row'&&+(r.getAttribute('r')||0)===rowNumber)}
function insertRowSorted(sheetData,row){const n=+(row.getAttribute('r')||0),before=[...sheetData.children].find(r=>+(r.getAttribute('r')||0)>n);sheetData.insertBefore(row,before||null)}
function findCell(row,cellRef){return[...row.children].find(c=>c.localName==='c'&&c.getAttribute('r')===cellRef)}
function insertCellSorted(row,cell){const p=decodeRef(cell.getAttribute('r')),before=[...row.children].find(c=>c.localName==='c'&&decodeRef(c.getAttribute('r')).c>p.c);row.insertBefore(cell,before||null)}
function usedRange(sheet){let r1=Infinity,c1=Infinity,r2=0,c2=0;for(const [ref,cell] of sheet.cells){if((cell.v===''||cell.v==null)&&!cell.f&&!cell.styleId)continue;const p=decodeRef(ref);r1=Math.min(r1,p.r);c1=Math.min(c1,p.c);r2=Math.max(r2,p.r);c2=Math.max(c2,p.c)}if(!Number.isFinite(r1))return'A1';return r1===r2&&c1===c2?encodeRef(r1,c1):`${encodeRef(r1,c1)}:${encodeRef(r2,c2)}`}
function patchRowsAndCells(doc,sheet){
  const root=doc.documentElement,sheetData=localOne(root,'sheetData');if(!sheetData)throw new Error('Worksheet sheetData is missing');
  const refs=new Set([...sheet.originalCells.keys(),...sheet.cells.keys()]);
  for(const cellRef of refs){
    const original=sheet.originalCells.get(cellRef)||null,current=sheet.cells.get(cellRef)||null;if(sameCell(original,current))continue;
    const p=decodeRef(cellRef),rowNumber=p.r+1;let row=findRow(sheetData,rowNumber),node=row?findCell(row,cellRef):null;
    const empty=!current||((current.v===''||current.v==null)&&!current.f&&!current.styleId);
    if(empty){if(node)row.removeChild(node);continue}
    if(!row){row=create(doc,'row');row.setAttribute('r',String(rowNumber));insertRowSorted(sheetData,row)}
    if(!node){node=create(doc,'c');node.setAttribute('r',cellRef);insertCellSorted(row,node)}
    writeCell(doc,node,current);
  }
  const allRows=[...sheetData.children].filter(n=>n.localName==='row');for(const row of allRows){if(![...row.children].some(n=>n.localName==='c')&&!row.hasAttribute('ht'))sheetData.removeChild(row)}
  for(const key of new Set([...Object.keys(sheet.originalHeights||{}),...Object.keys(sheet.heights||{})])){
    const r=+key,old=sheet.originalHeights?.[r],now=sheet.heights?.[r];if(Number(old||0)===Number(now||0))continue;
    let row=findRow(sheetData,r+1);if(!row&&now){row=create(doc,'row');row.setAttribute('r',String(r+1));insertRowSorted(sheetData,row)}
    if(!row)continue;if(now){row.setAttribute('ht',pxHeight(now).toFixed(2));row.setAttribute('customHeight','1')}else{row.removeAttribute('ht');row.removeAttribute('customHeight')}
  }
  const dimension=localOne(root,'dimension');if(dimension)dimension.setAttribute('ref',usedRange(sheet));
}
function expandOriginalColAttributes(doc){
  const map={};for(const col of localAll(doc,'col')){const min=+(col.getAttribute('min')||1),max=+(col.getAttribute('max')||min);for(let i=min;i<=max;i++){const attrs={};for(const a of[...col.attributes])if(!['min','max'].includes(a.name))attrs[a.name]=a.value;map[i]=attrs}}return map;
}
function patchColumns(doc,sheet){
  if(sameObject(sheet.originalWidths,sheet.widths))return;
  const root=doc.documentElement,attrs=expandOriginalColAttributes(doc);let cols=localOne(root,'cols');if(cols)root.removeChild(cols);cols=create(doc,'cols');
  const indices=new Set([...Object.keys(attrs).map(Number),...Object.keys(sheet.widths||{}).map(x=>+x+1)]);
  for(const i of[...indices].sort((a,b)=>a-b)){
    const col=create(doc,'col'),base=attrs[i]||{};for(const[k,v]of Object.entries(base))col.setAttribute(k,v);col.setAttribute('min',String(i));col.setAttribute('max',String(i));
    const px=sheet.widths?.[i-1];if(px){col.setAttribute('width',pxWidth(px).toFixed(3));col.setAttribute('customWidth','1')}
    cols.appendChild(col);
  }
  const sheetData=localOne(root,'sheetData');root.insertBefore(cols,sheetData||null);
}
function patchMerges(doc,sheet){
  if(sameObject(sheet.originalMerges,sheet.merges))return;
  const root=doc.documentElement;let old=localOne(root,'mergeCells');if(old)root.removeChild(old);if(!sheet.merges.length)return;
  const node=create(doc,'mergeCells');node.setAttribute('count',String(sheet.merges.length));for(const ref of sheet.merges){const m=create(doc,'mergeCell');m.setAttribute('ref',ref);node.appendChild(m)}
  const sheetData=localOne(root,'sheetData'),after=[...root.children].find(n=>n.localName!=='sheetData'&&sheetData&&[...root.children].indexOf(n)>[...root.children].indexOf(sheetData));root.insertBefore(node,after||null);
}
function patchSheetXml(raw,sheet){const doc=xml(raw);patchRowsAndCells(doc,sheet);patchColumns(doc,sheet);patchMerges(doc,sheet);return'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+serializeXml(doc).replace(/^<\?xml[^>]*>\s*/,'')}
function sheetHasChanges(sheet){const refs=new Set([...sheet.originalCells.keys(),...sheet.cells.keys()]);for(const ref of refs)if(!sameCell(sheet.originalCells.get(ref)||null,sheet.cells.get(ref)||null))return true;return !sameObject(sheet.originalWidths,sheet.widths)||!sameObject(sheet.originalHeights,sheet.heights)||!sameObject(sheet.originalMerges,sheet.merges)}
function serializeSheet(sheet,drawingRid=''){
  const rows=new Map();for(const [cellRef,cell] of sheet.cells){const p=decodeRef(cellRef);if(!rows.has(p.r))rows.set(p.r,[]);rows.get(p.r).push([p.c,cellRef,cell])}
  let rowXml='';for(const r of[...new Set([...rows.keys(),...Object.keys(sheet.heights||{}).map(Number)])].sort((a,b)=>a-b)){
    let cs='';for(const[,cellRef,c]of(rows.get(r)||[]).sort((a,b)=>a[0]-b[0])){let attrs=` r="${cellRef}"`;if(c.styleId)attrs+=` s="${c.styleId}"`;let body='';if(c.f)body+=`<f>${escapeXml(c.f.replace(/^=/,''))}</f>`;if(typeof c.v==='string'){attrs+=' t="inlineStr"';body+=`<is><t xml:space="preserve">${escapeXml(c.v)}</t></is>`}else if(typeof c.v==='boolean'){attrs+=' t="b"';body+=`<v>${c.v?1:0}</v>`}else if(c.v!==''&&c.v!=null)body+=`<v>${escapeXml(c.v)}</v>`;cs+=`<c${attrs}>${body}</c>`}
    const ht=sheet.heights[r]?` ht="${pxHeight(sheet.heights[r]).toFixed(2)}" customHeight="1"`:'';rowXml+=`<row r="${r+1}"${ht}>${cs}</row>`;
  }
  const cols=Object.keys(sheet.widths||{}).length?`<cols>${Object.entries(sheet.widths).sort((a,b)=>+a[0]-+b[0]).map(([i,w])=>`<col min="${+i+1}" max="${+i+1}" width="${pxWidth(w).toFixed(3)}" customWidth="1"/>`).join('')}</cols>`:'';
  const mergeXml=sheet.merges.length?`<mergeCells count="${sheet.merges.length}">${sheet.merges.map(x=>`<mergeCell ref="${x}"/>`).join('')}</mergeCells>`:'';
  const pane=sheet.freezePane?`<sheetViews><sheetView workbookViewId="0"><pane xSplit="${sheet.freezePane.xSplit||0}" ySplit="${sheet.freezePane.ySplit||0}" topLeftCell="${escapeXml(sheet.freezePane.topLeftCell||'A1')}" state="frozen"/></sheetView></sheetViews>`:`<sheetViews><sheetView workbookViewId="0"/></sheetViews>`;
  const m=sheet.margins||{},margins=Object.keys(m).length?`<pageMargins left="${Number(m.left||0.7)}" right="${Number(m.right||0.7)}" top="${Number(m.top||0.75)}" bottom="${Number(m.bottom||0.75)}" header="${Number(m.header||0.3)}" footer="${Number(m.footer||0.3)}"/>`:'';
  const ps=sheet.pageSetup||{},setup=Object.keys(ps).length?`<pageSetup${ps.paperSize?` paperSize="${ps.paperSize}"`:''}${ps.scale?` scale="${ps.scale}"`:''}${ps.fitToWidth?` fitToWidth="${ps.fitToWidth}"`:''}${ps.fitToHeight?` fitToHeight="${ps.fitToHeight}"`:''}${ps.orientation?` orientation="${escapeXml(ps.orientation)}"`:''}/>`:'';
  const hf=(sheet.header||sheet.footer)?`<headerFooter>${sheet.header?`<oddHeader>${escapeXml(sheet.header)}</oddHeader>`:''}${sheet.footer?`<oddFooter>${escapeXml(sheet.footer)}</oddFooter>`:''}</headerFooter>`:'';
  const drawing=drawingRid?`<drawing r:id="${drawingRid}"/>`:'';
  return`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="${NS}" xmlns:r="${REL}"><dimension ref="${usedRange(sheet)}"/>${pane}${cols}<sheetFormatPr defaultRowHeight="${pxHeight(sheet.defaultRowHeight||20).toFixed(2)}"/><sheetData>${rowXml}</sheetData>${mergeXml}${margins}${setup}${hf}${drawing}</worksheet>`;
}
function styleColor(value){const v=String(value||'').replace(/^#/,'').toUpperCase();return/^[0-9A-F]{6}$/.test(v)?'FF'+v:''}
function legacyStylesXml(book){
  const styles=(book.legacyStyles&&book.legacyStyles.length?book.legacyStyles:[{}]);
  const fonts=styles.map(st=>{const f=st.font||{},color=styleColor(f.color);return`<font><sz val="${Number(f.size||11)}"/><name val="${escapeXml(f.name||'Calibri')}"/>${f.bold?'<b/>':''}${f.italic?'<i/>':''}${f.underline?'<u/>':''}${f.strike?'<strike/>':''}${color?`<color rgb="${color}"/>`:''}<family val="2"/></font>`});
  const fills=['<fill><patternFill patternType="none"/></fill>','<fill><patternFill patternType="gray125"/></fill>',...styles.map(st=>{const c=styleColor(st.fill);return c?`<fill><patternFill patternType="solid"><fgColor rgb="${c}"/><bgColor indexed="64"/></patternFill></fill>`:'<fill><patternFill patternType="none"/></fill>'})];
  const borderXml=side=>{if(!side)return'<'+sideName+'/>';};
  const borders=styles.map(st=>{const b=st.border||{};const one=(name,x)=>x?`<${name} style="${escapeXml(x.style||'thin')}">${styleColor(x.color)?`<color rgb="${styleColor(x.color)}"/>`:''}</${name}>`:`<${name}/>`;return`<border>${one('left',b.left)}${one('right',b.right)}${one('top',b.top)}${one('bottom',b.bottom)}<diagonal/></border>`});
  const custom=new Map();for(const st of styles){const id=Number(st.numFmtId||0),fmt=String(st.numberFormat||'');if(id>=164&&fmt)custom.set(id,fmt)}const numFmts=custom.size?`<numFmts count="${custom.size}">${[...custom].map(([id,fmt])=>`<numFmt numFmtId="${id}" formatCode="${escapeXml(fmt)}"/>`).join('')}</numFmts>`:'';
  const xfs=styles.map((st,i)=>{const al=[];if(st.align&&st.align!=='general')al.push(`horizontal="${escapeXml(st.align)}"`);if(st.vertical)al.push(`vertical="${escapeXml(st.vertical)}"`);if(st.wrap)al.push('wrapText="1"');if(st.rotation)al.push(`textRotation="${Math.max(0,Math.min(180,st.rotation<0?180+st.rotation:st.rotation))}"`);return`<xf numFmtId="${Number(st.numFmtId||0)}" fontId="${i}" fillId="${i+2}" borderId="${i}" xfId="0" applyFont="1" applyFill="1" applyBorder="1"${st.numFmtId?' applyNumberFormat="1"':''}${al.length?' applyAlignment="1"':''}>${al.length?`<alignment ${al.join(' ')}/>`:''}</xf>`});
  return`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="${NS}">${numFmts}<fonts count="${fonts.length}">${fonts.join('')}</fonts><fills count="${fills.length}">${fills.join('')}</fills><borders count="${borders.length}">${borders.join('')}</borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="${xfs.length}">${xfs.join('')}</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>`;
}
function markerXml(tag,m){const x=Math.round(Number(m?.x||0)*9525),y=Math.round(Number(m?.y||0)*9525);return`<xdr:${tag}><xdr:col>${Math.max(0,Number(m?.c||0))}</xdr:col><xdr:colOff>${x}</xdr:colOff><xdr:row>${Math.max(0,Number(m?.r||0))}</xdr:row><xdr:rowOff>${y}</xdr:rowOff></xdr:${tag}>`}
function drawingXmlForSheet(sheet,index,mediaStart){
  const objects=[],rels=[],media=[];let id=1,mediaNo=mediaStart;
  for(const d of sheet.drawings||[]){const from=d.from||{c:0,r:0,x:0,y:0},to=d.to||{c:(from.c||0)+1,r:(from.r||0)+1,x:0,y:0};if(d.kind==='image'&&d.bytes){const ext=(d.extension||'png').replace(/^jpeg$/,'jpg'),rid=`rId${rels.length+1}`,name=`image${mediaNo}.${ext}`;media.push({path:`xl/media/${name}`,bytes:d.bytes,extension:ext,mime:d.mime||`image/${ext}`});rels.push({id:rid,target:`../media/${name}`});objects.push(`<xdr:twoCellAnchor editAs="oneCell">${markerXml('from',from)}${markerXml('to',to)}<xdr:pic><xdr:nvPicPr><xdr:cNvPr id="${id}" name="${escapeXml(d.name||`Picture ${id}`)}"/><xdr:cNvPicPr/></xdr:nvPicPr><xdr:blipFill><a:blip r:embed="${rid}"/><a:stretch><a:fillRect/></a:stretch></xdr:blipFill><xdr:spPr><a:xfrm/><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></xdr:spPr></xdr:pic><xdr:clientData/></xdr:twoCellAnchor>`);mediaNo++;id++;continue}if(d.kind==='shape'&&String(d.text||'').trim()){const paras=String(d.text).split(/\n/).map(line=>`<a:p><a:r><a:rPr lang="en-US" sz="${Math.round(Number(d.fontSize||10)*100)}"${d.bold?' b="1"':''}/><a:t>${escapeXml(line)}</a:t></a:r><a:endParaRPr lang="en-US"/></a:p>`).join('');objects.push(`<xdr:twoCellAnchor editAs="oneCell">${markerXml('from',from)}${markerXml('to',to)}<xdr:sp><xdr:nvSpPr><xdr:cNvPr id="${id}" name="${escapeXml(d.name||`Text Box ${id}`)}"/><xdr:cNvSpPr txBox="1"/><xdr:nvPr/></xdr:nvSpPr><xdr:spPr><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></xdr:spPr><xdr:txBody><a:bodyPr wrap="square"/><a:lstStyle/>${paras}</xdr:txBody></xdr:sp><xdr:clientData/></xdr:twoCellAnchor>`);id++}}
  if(!objects.length)return null;const xml=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="${REL}">${objects.join('')}</xdr:wsDr>`,relsXml=rels.length?`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="${PKG_REL}">${rels.map(x=>`<Relationship Id="${x.id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="${x.target}"/>`).join('')}</Relationships>`:'';return{xml,relsXml,media,nextMedia:mediaNo,path:`xl/drawings/drawing${index+1}.xml`,relsPath:`xl/drawings/_rels/drawing${index+1}.xml.rels`};
}
async function buildNewPackage(book){
  const zip=new JSZip(),esc=escapeXml,sheetEntries=book.sheets.map((s,i)=>({s,i,path:`xl/worksheets/sheet${i+1}.xml`,rid:`rId${i+1}`}));let mediaNo=1;const drawings=[];for(const x of sheetEntries){const d=drawingXmlForSheet(x.s,x.i,mediaNo);drawings.push(d);if(d)mediaNo=d.nextMedia}
  const imageExts=new Set(drawings.flatMap(d=>d?d.media.map(m=>m.extension):[]));const imageDefaults=[...imageExts].map(ext=>`<Default Extension="${ext}" ContentType="${ext==='jpg'||ext==='jpeg'?'image/jpeg':ext==='gif'?'image/gif':ext==='bmp'?'image/bmp':'image/png'}"/>`).join('');
  zip.file('[Content_Types].xml',`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>${imageDefaults}<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>${sheetEntries.map(x=>`<Override PartName="/${x.path}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join('')}${drawings.map(d=>d?`<Override PartName="/${d.path}" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>`:'').join('')}</Types>`);
  zip.folder('_rels').file('.rels',`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="${PKG_REL}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`);
  zip.folder('xl').file('workbook.xml',`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="${NS}" xmlns:r="${REL}"><bookViews><workbookView activeTab="${book.active||0}"/></bookViews><sheets>${sheetEntries.map(x=>`<sheet name="${esc(x.s.name||`Sheet${x.i+1}`)}" sheetId="${x.i+1}"${x.s.state&&x.s.state!=='visible'?` state="${esc(x.s.state)}"`:''} r:id="${x.rid}"/>`).join('')}</sheets><calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>`);
  zip.folder('xl').folder('_rels').file('workbook.xml.rels',`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="${PKG_REL}">${sheetEntries.map(x=>`<Relationship Id="${x.rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${x.i+1}.xml"/>`).join('')}<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`);
  zip.folder('xl').file('styles.xml',legacyStylesXml(book));
  for(const x of sheetEntries){const d=drawings[x.i],drawingRid=d?'rIdDrawing1':'';x.s.path=x.path;zip.file(x.path,serializeSheet(x.s,drawingRid));if(d){zip.file(d.path,d.xml);if(d.relsXml)zip.file(d.relsPath,d.relsXml);for(const m of d.media)zip.file(m.path,m.bytes);zip.file(`xl/worksheets/_rels/sheet${x.i+1}.xml.rels`,`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="${PKG_REL}"><Relationship Id="rIdDrawing1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing${x.i+1}.xml"/></Relationships>`)}}
  return zip.generateAsync({type:'blob',mimeType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',compression:'DEFLATE',compressionOptions:{level:6}});
}
async function saveCopy(book){
  if(!book.loaded)throw new Error('Create or open a workbook before saving a copy');if(!book.zip)return buildNewPackage(book);
  const source=await book.zip.generateAsync({type:'uint8array'}),zip=await JSZip.loadAsync(source);let changedAny=await global.InkDeskSpreadsheetWorksheetPackage.appendNewSheets(zip,book,{serializeSheet});
  for(const s of book.sheets){if(!sheetHasChanges(s))continue;const raw=await zip.file(s.path)?.async('text');if(!raw)continue;zip.file(s.path,patchSheetXml(raw,s),{createFolders:false});changedAny=true}
  const wbRaw=changedAny?await zip.file('xl/workbook.xml')?.async('text'):'';if(wbRaw){const d=xml(wbRaw),root=d.documentElement;let calc=localOne(root,'calcPr');if(!calc){calc=create(d,'calcPr');root.appendChild(calc)}calc.setAttribute('calcMode','auto');calc.setAttribute('fullCalcOnLoad','1');calc.setAttribute('forceFullCalc','1');zip.file('xl/workbook.xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+serializeXml(d).replace(/^<\?xml[^>]*>\s*/,''),{createFolders:false})}
  return zip.generateAsync({type:'blob',mimeType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',compression:'DEFLATE',compressionOptions:{level:6}});
}
global.LocalXLSX={parseWorkbook,createBlank,saveCopy,colName,decodeRef,encodeRef,decodeRange};
})(window);

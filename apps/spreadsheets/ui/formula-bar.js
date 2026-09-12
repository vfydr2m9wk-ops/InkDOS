(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
function normalizeFormulaInput(value){const raw=String(value??''),text=raw.trim(),supported='SUM|AVERAGE|MIN|MAX|COUNT';let m=new RegExp('^=\\s*('+supported+')\\s*:\\s*(.+)$','i').exec(text);if(m)return`=${m[1].toUpperCase()}(${m[2].replace(/;/g,',')})`;m=new RegExp('^=\\s*('+supported+')\\s*\\((.*)\\)$','i').exec(text);if(m)return`=${m[1].toUpperCase()}(${m[2].replace(/;/g,',')})`;return raw}
function create({nameBox,input,functions,session,selection,editor,onNavigate,onCommitted}={}){
 function currentRef(){return root.LocalXLSX.encodeRef(selection.active.r,selection.active.c)}
 function sync(){const sheet=session.activeSheet();if(!sheet)return;const ref=currentRef(),cell=sheet.cells.get(ref);nameBox.value=ref;input.value=cell?(cell.f?'='+cell.f:(cell.v??'')):''}
 input.addEventListener('focus',sync);input.addEventListener('keydown',e=>{if(e.key==='Enter'&&session.book?.loaded){e.preventDefault();editor.commitValue(normalizeFormulaInput(input.value));onCommitted?.();sync()}else if(e.key==='Escape'){e.preventDefault();sync()}});nameBox.addEventListener('keydown',e=>{if(e.key!=='Enter'||!session.book?.loaded)return;e.preventDefault();const p=root.LocalXLSX.decodeRef(nameBox.value.toUpperCase());selection.select(p.r,p.c,session.activeSheet(),false);onNavigate?.();sync()});functions?.addEventListener('change',()=>{const fn=functions.value;functions.value='';if(!fn)return;const q=selection.range,ref=(r,c)=>root.LocalXLSX.encodeRef(r,c);if(['SUM','AVERAGE','MIN','MAX','COUNT'].includes(fn)){input.value=`=${fn}(${ref(q.r1,q.c1)}:${ref(q.r2,q.c2)})`;input.focus();input.setSelectionRange(input.value.length,input.value.length)}});
 return Object.freeze({sync})
}
NS.FormulaBar=Object.freeze({create});
})(globalThis);

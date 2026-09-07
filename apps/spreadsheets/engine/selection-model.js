(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
function clamp(n,a,b){return Math.max(a,Math.min(b,n))}
class SelectionModel{
 constructor(){this.active={r:0,c:0};this.anchor={r:0,c:0};this.range={r1:0,c1:0,r2:0,c2:0}}
 normalize(){this.range={r1:Math.min(this.anchor.r,this.active.r),c1:Math.min(this.anchor.c,this.active.c),r2:Math.max(this.anchor.r,this.active.r),c2:Math.max(this.anchor.c,this.active.c)};return this.range}
 select(r,c,sheet,extend=false){const rr=clamp(Number(r)||0,0,sheet.maxR),cc=clamp(Number(c)||0,0,sheet.maxC);if(!extend)this.anchor={r:rr,c:cc};this.active={r:rr,c:cc};return this.normalize()}
 selectRow(r,sheet,extend=false){const rr=clamp(Number(r)||0,0,sheet.maxR);if(!extend)this.anchor={r:rr,c:0};this.active={r:rr,c:sheet.maxC};return this.normalize()}
 selectColumn(c,sheet,extend=false){const cc=clamp(Number(c)||0,0,sheet.maxC);if(!extend)this.anchor={r:0,c:cc};this.active={r:sheet.maxR,c:cc};return this.normalize()}
 snapshot(){return{active:{...this.active},anchor:{...this.anchor},range:{...this.range}}}
 restore(s){if(!s)return;this.active={...s.active};this.anchor={...s.anchor};this.range={...s.range}}
}
NS.SelectionModel=SelectionModel;
})(globalThis);

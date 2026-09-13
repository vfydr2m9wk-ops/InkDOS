(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
const MIN_SCALE=.25,MAX_SCALE=4,SLIDER_STEP=.05,BUTTON_STEP=.1;
function clamp(n,a,b){return Math.max(a,Math.min(b,n))}
function normalizeScale(value){const n=Number(value);if(!Number.isFinite(n))return 1;return Math.round(clamp(n,MIN_SCALE,MAX_SCALE)*100)/100}
function colWidth(sheet,c){return Math.max(28,Number(sheet?.widths?.[c])||Number(sheet?.defaultColWidth)||68)}
function rowHeight(sheet,r){return Math.max(14,Number(sheet?.heights?.[r])||Number(sheet?.defaultRowHeight)||20)}
function buildAxis(count,sizeAt,scale){const starts=new Float64Array(count+1);for(let i=0;i<count;i++)starts[i+1]=starts[i]+sizeAt(i)*scale;return starts}
function build(sheet,scale=1){const s=normalizeScale(scale),rows=Math.max(1,(sheet?.maxR??99)+1),columns=Math.max(1,(sheet?.maxC??25)+1),rowHeader=48*s,columnHeader=28*s;return Object.freeze({scale:s,rows,columns,rowHeader,columnHeader,x:buildAxis(columns,c=>colWidth(sheet,c),s),y:buildAxis(rows,r=>rowHeight(sheet,r),s)})}
function findIndex(axis,value){let lo=0,hi=Math.max(0,axis.length-2);while(lo<=hi){const mid=(lo+hi)>>1;if(value<axis[mid])hi=mid-1;else if(value>=axis[mid+1])lo=mid+1;else return mid}return clamp(lo,0,Math.max(0,axis.length-2))}
function capture(scrollLeft,scrollTop,geometry){const x=Math.max(0,Number(scrollLeft)||0),y=Math.max(0,Number(scrollTop)||0),c=findIndex(geometry.x,x),r=findIndex(geometry.y,y),cw=Math.max(1,geometry.x[c+1]-geometry.x[c]),rh=Math.max(1,geometry.y[r+1]-geometry.y[r]);return Object.freeze({columnIndex:c,rowIndex:r,fractionX:clamp((x-geometry.x[c])/cw,0,.999999),fractionY:clamp((y-geometry.y[r])/rh,0,.999999)})}
function scrollFor(anchor,geometry){const c=clamp(Number(anchor?.columnIndex)||0,0,geometry.columns-1),r=clamp(Number(anchor?.rowIndex)||0,0,geometry.rows-1),fx=clamp(Number(anchor?.fractionX)||0,0,.999999),fy=clamp(Number(anchor?.fractionY)||0,0,.999999);return Object.freeze({left:geometry.x[c]+fx*(geometry.x[c+1]-geometry.x[c]),top:geometry.y[r]+fy*(geometry.y[r+1]-geometry.y[r])})}
function contentSize(g){return Object.freeze({width:g.rowHeader+g.x[g.x.length-1],height:g.columnHeader+g.y[g.y.length-1]})}
NS.GridGeometry=Object.freeze({MIN_SCALE,MAX_SCALE,SLIDER_STEP,BUTTON_STEP,normalizeScale,colWidth,rowHeight,build,capture,scrollFor,contentSize});
})(globalThis);

(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function defaultSpec(){return{widthPx:816,heightPx:1056,marginTopPx:82,marginRightPx:86,marginBottomPx:88,marginLeftPx:86,contentWidthPx:644,contentHeightPx:886,fontFamily:'Calibri',fontSizePt:11,lineHeight:1.15,orientation:'portrait',headerText:'',footerText:'',pageNumber:false,columns:1,columnGapPx:36,headerArtwork:[],footerArtwork:[]}}
function normalize(spec){const d=defaultSpec(),x={...d,...(spec||{})};for(const k of ['widthPx','heightPx','marginTopPx','marginRightPx','marginBottomPx','marginLeftPx','contentWidthPx','contentHeightPx','fontSizePt','lineHeight'])if(!Number.isFinite(Number(x[k]))||Number(x[k])<=0)x[k]=d[k];x.orientation=x.orientation==='landscape'||x.widthPx>x.heightPx?'landscape':'portrait';x.pageNumber=!!x.pageNumber;x.headerText=String(x.headerText||'').slice(0,500);x.footerText=String(x.footerText||'').slice(0,500);x.columns=Math.max(1,Math.min(3,Math.round(Number(x.columns)||1)));x.columnGapPx=Math.max(8,Math.min(144,Number(x.columnGapPx)||d.columnGapPx));return x}
function same(a,b){a=normalize(a);b=normalize(b);return ['widthPx','heightPx','marginTopPx','marginRightPx','marginBottomPx','marginLeftPx','columnGapPx'].every(k=>Math.abs(Number(a[k])-Number(b[k]))<.1)&&a.columns===b.columns}
NS.PageSpec=Object.freeze({defaultSpec,normalize,same});
})(globalThis);

(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function defaultSpec(){return{widthPx:816,heightPx:1056,marginTopPx:82,marginRightPx:86,marginBottomPx:88,marginLeftPx:86,contentWidthPx:644,contentHeightPx:886,fontFamily:'Calibri',fontSizePt:11,lineHeight:1.15,headerText:'',footerText:'',headerArtwork:[],footerArtwork:[]}}
function normalize(spec){const d=defaultSpec(),x={...d,...(spec||{})};for(const k of ['widthPx','heightPx','marginTopPx','marginRightPx','marginBottomPx','marginLeftPx','contentWidthPx','contentHeightPx','fontSizePt','lineHeight'])if(!Number.isFinite(Number(x[k]))||Number(x[k])<=0)x[k]=d[k];return x}
function same(a,b){return ['widthPx','heightPx','marginTopPx','marginRightPx','marginBottomPx','marginLeftPx'].every(k=>Math.abs(Number(a[k])-Number(b[k]))<.1)}
NS.PageSpec=Object.freeze({defaultSpec,normalize,same});
})(globalThis);

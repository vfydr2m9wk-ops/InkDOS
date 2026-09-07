(function(g){'use strict';const NS=g.InkDOS2=g.InkDOS2||{};
class ViewportMetrics{constructor({availableWidth,availableHeight,dpr=1,epoch=0,visibility='visible'}){this.availableWidth=Math.max(0,Number(availableWidth)||0);this.availableHeight=Math.max(0,Number(availableHeight)||0);this.dpr=Math.max(0.1,Number(dpr)||1);this.epoch=Math.max(0,Number(epoch)||0);this.visibility=visibility;Object.freeze(this)}get valid(){return this.availableWidth>0&&this.availableHeight>0}}
NS.ViewportMetrics=ViewportMetrics;})(globalThis);

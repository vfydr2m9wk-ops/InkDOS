(function(g){'use strict';const NS=g.InkDOS2=g.InkDOS2||{};
class ContentViewportAdapter{constructor(el,onMetrics){this.el=el;this.onMetrics=onMetrics;this.epoch=0;this.ro=null;this.handle=this.measure.bind(this);if(g.ResizeObserver){this.ro=new ResizeObserver(this.handle);this.ro.observe(el)}g.addEventListener('resize',this.handle,{passive:true});this.measure()}
measure(){const r=this.el.getBoundingClientRect();this.epoch+=1;const m=new NS.ViewportMetrics({availableWidth:r.width,availableHeight:r.height,dpr:g.devicePixelRatio||1,epoch:this.epoch,visibility:document.visibilityState});this.onMetrics&&this.onMetrics(m)}dispose(){this.ro&&this.ro.disconnect();g.removeEventListener('resize',this.handle)}}
NS.ContentViewportAdapter=ContentViewportAdapter;})(globalThis);

(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{},G=NS.GridGeometry;
class ZoomController{
 constructor({viewport,getSheet,onGeometry,onChange}={}){this.viewport=viewport;this.getSheet=getSheet;this.onGeometry=onGeometry;this.onChange=onChange;this.scale=1;this.geometry=null;this.canonicalAnchor=null;this.timer=0;this.programmaticUntil=0;viewport.addEventListener('scroll',()=>{if(performance.now()>this.programmaticUntil)this.canonicalAnchor=null},{passive:true})}
 currentAnchor(){return this.geometry?G.capture(this.viewport.scrollLeft,this.viewport.scrollTop,this.geometry):null}
 rebuild(anchor){const sheet=this.getSheet?.();if(!sheet)return null;this.geometry=G.build(sheet,this.scale);this.onGeometry?.(this.geometry);if(anchor){const p=G.scrollFor(anchor,this.geometry);this.programmaticUntil=performance.now()+140;this.viewport.scrollTo({left:p.left,top:p.top});this.stableAnchor=anchor}else this.stableAnchor=this.currentAnchor();this.onChange?.(this.scale,this.geometry);return this.geometry}
 set(value){const next=G.normalizeScale(value);if(Math.abs(next-this.scale)<.0001){this.onChange?.(this.scale,this.geometry);return this.scale}const anchor=this.canonicalAnchor||this.currentAnchor();if(anchor)this.canonicalAnchor=anchor;clearTimeout(this.timer);this.timer=setTimeout(()=>{this.canonicalAnchor=null},450);this.scale=next;this.rebuild(anchor);return this.scale}
 step(delta){return this.set(this.scale+Number(delta||0))}
 restoreStable(){if(!this.geometry||!this.stableAnchor)return;const p=G.scrollFor(this.stableAnchor,this.geometry);this.programmaticUntil=performance.now()+140;this.viewport.scrollTo({left:p.left,top:p.top})}
 reset(){return this.set(1)}
}
NS.ZoomController=ZoomController;
})(globalThis);

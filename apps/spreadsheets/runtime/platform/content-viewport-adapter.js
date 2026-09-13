(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
class ContentViewportAdapter{
 constructor(viewport){this.viewport=viewport;this.observer=null;this.epoch=0;this.last=null;this.resizeHandler=null}
 measure(){const cs=getComputedStyle(this.viewport),w=Math.max(0,this.viewport.clientWidth-(parseFloat(cs.paddingLeft)||0)-(parseFloat(cs.paddingRight)||0)),h=Math.max(0,this.viewport.clientHeight-(parseFloat(cs.paddingTop)||0)-(parseFloat(cs.paddingBottom)||0));this.last=Object.freeze({availableWidth:w,availableHeight:h,dpr:devicePixelRatio||1,epoch:++this.epoch,visible:document.visibilityState!=='hidden'});return this.last}
 install(onResize){const cb=()=>requestAnimationFrame(()=>onResize?.(this.measure()));this.resizeHandler=cb;window.addEventListener('resize',cb,{passive:true});if(typeof ResizeObserver==='function'){this.observer=new ResizeObserver(cb);this.observer.observe(this.viewport)}document.addEventListener('visibilitychange',cb);cb()}
 destroy(){if(this.resizeHandler){window.removeEventListener('resize',this.resizeHandler);document.removeEventListener('visibilitychange',this.resizeHandler)}this.observer?.disconnect()}
}
NS.ContentViewportAdapter=ContentViewportAdapter;
})(globalThis);

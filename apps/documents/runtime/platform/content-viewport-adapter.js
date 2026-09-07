(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function clamp(n,a,b){return Math.max(a,Math.min(b,n))}
class ContentViewportAdapter{
 constructor(viewport,stack){this.viewport=viewport;this.stack=stack;this.resizeObserver=null;this.resizeHandler=null}
 install(onResize){const cb=()=>requestAnimationFrame(()=>onResize?.());this.resizeHandler=cb;window.addEventListener('resize',cb);if(typeof ResizeObserver==='function'){this.resizeObserver=new ResizeObserver(cb);this.resizeObserver.observe(this.viewport)}}
 destroy(){if(this.resizeHandler)window.removeEventListener('resize',this.resizeHandler);this.resizeObserver?.disconnect()}
 metrics(){const cs=getComputedStyle(this.stack),pl=parseFloat(cs.paddingLeft)||0,pr=parseFloat(cs.paddingRight)||0,pt=parseFloat(cs.paddingTop)||0,pb=parseFloat(cs.paddingBottom)||0;return Object.freeze({width:Math.max(1,this.viewport.clientWidth-pl-pr),height:Math.max(1,this.viewport.clientHeight-pt-pb)})}
 horizontalFocus(){const max=Math.max(0,this.viewport.scrollWidth-this.viewport.clientWidth);if(max<=1)return .5;return clamp((this.viewport.scrollLeft+this.viewport.clientWidth/2)/Math.max(this.viewport.scrollWidth,1),0,1)}
 restoreHorizontalFocus(focus){const max=Math.max(0,this.viewport.scrollWidth-this.viewport.clientWidth);if(max<=1){this.viewport.scrollLeft=0;return}this.viewport.scrollLeft=clamp(focus*this.viewport.scrollWidth-this.viewport.clientWidth/2,0,max)}
}
NS.ContentViewportAdapter=ContentViewportAdapter;
})(globalThis);

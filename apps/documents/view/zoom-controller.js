(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
const MIN=.25,MAX=4,FIT_MAX=1.25,FIT_PAGE_MAX=1.1;
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const number=(n,f)=>{n=Number(n);return Number.isFinite(n)&&n>0?n:f};
class ZoomController{
 constructor(adapter,stack,onChange){this.adapter=adapter;this.stack=stack;this.onChange=onChange||(()=>{});this.mode='fit-width';this.manual=1;this.scale=1;this.currentSpec=null;this.epoch=0}
 install(){this.adapter.install(()=>this.apply({preserveFocus:true}));this.apply()}
 destroy(){this.adapter.destroy()}
 setCurrentSpec(spec){this.currentSpec=spec||this.currentSpec}
 computeScale(){const spec=this.currentSpec||(this.stack.querySelector('.doc-page')?._pageSpec);if(!spec)return 1;const m=this.adapter.metrics(),w=number(spec.widthPx,816),h=number(spec.heightPx,1056);if(this.mode==='manual')return clamp(this.manual,MIN,MAX);if(this.mode==='fit-page')return clamp(Math.min(FIT_PAGE_MAX,m.width/w,m.height/h),.2,FIT_PAGE_MAX);return clamp(Math.min(FIT_MAX,m.width/w),.2,FIT_MAX)}
 apply(options={}){const focus=options.preserveFocus===false ? .5 : this.adapter.horizontalFocus(),scale=this.computeScale();this.scale=scale;for(const shell of this.stack.querySelectorAll('.page-shell')){const page=shell.querySelector('.doc-page'),spec=page?._pageSpec||this.currentSpec;if(!page||!spec)continue;const w=number(spec.widthPx,816),h=number(spec.heightPx,1056);shell.style.width=(w*scale)+'px';shell.style.height=(h*scale)+'px';page.style.width=w+'px';page.style.height=h+'px';page.style.transform='scale('+scale+')'}requestAnimationFrame(()=>this.adapter.restoreHorizontalFocus(focus));this.epoch++;this.onChange(Object.freeze({mode:this.mode,scale:this.scale,percent:Math.round(this.scale*100),epoch:this.epoch,metrics:this.adapter.metrics()}))}
 setMode(mode,value){if(mode==='manual'){this.mode='manual';if(value!=null)this.manual=clamp(Number(value)||1,MIN,MAX)}else if(mode==='fit-page')this.mode='fit-page';else this.mode='fit-width';this.apply({preserveFocus:true})}
 setPercent(percent){this.setMode('manual',clamp(Number(percent)/100,MIN,MAX))}
}
NS.ZoomController=ZoomController;NS.ZoomLimits=Object.freeze({MIN,MAX,FIT_MAX,FIT_PAGE_MAX});
})(globalThis);

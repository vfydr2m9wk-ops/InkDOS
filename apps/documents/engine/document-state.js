(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
class DocumentState{
 constructor(session){this.session=session;this.pageModels=[];this.currentPage=1;this.currentPageSpec=null;this.mediaUrls={};this.outline=[];this.pageObserver=null;this.lastSelectionToken='';this.lastSelectionAt=0}
 revoke(urls){for(const url of Object.values(urls||{}))try{URL.revokeObjectURL(url)}catch(_){}}
 replaceMedia(next){const old=this.mediaUrls;this.mediaUrls=next||{};this.revoke(old)}
 resetPageObserver(){this.pageObserver?.disconnect();this.pageObserver=null}
}
NS.DocumentState=DocumentState;
})(globalThis);

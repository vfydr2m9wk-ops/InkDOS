(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
const l10n=Object.freeze({
  async get(key,args=null,fallback=null){return fallback||String(key||'')},
  async translate(){},
  async getLanguage(){return 'en-US'},
  async getDirection(){return 'ltr'},
  pause(){},resume(){}
});
const linkService=Object.freeze({
  externalLinkEnabled:true,externalLinkRel:'noopener noreferrer nofollow',externalLinkTarget:0,
  getDestinationHash(){return '#'},getAnchorUrl(hash){return hash||'#'},
  addLinkAttributes(link,url){link.href=url||'#';link.rel='noopener noreferrer';link.target='_blank'},
  async navigateTo(){},goToDestination(){},goToPage(){},executeNamedAction(){},executeSetOCGState(){},
  get pagesCount(){return 0},get page(){return 1},set page(v){},get rotation(){return 0},set rotation(v){},
  isPageVisible(){return true},isPageCached(){return true}
});
const downloadManager=Object.freeze({download(){},openOrDownloadData(){},downloadData(){}});
function altTextManager(){return Object.freeze({destroy(){},editAltText(){}})}
NS.PdfjsEnvironment=Object.freeze({l10n,linkService,downloadManager,altTextManager});})(globalThis);
(function(){
'use strict';
const EMU=914400;
const NS={p:'http://schemas.openxmlformats.org/presentationml/2006/main',a:'http://schemas.openxmlformats.org/drawingml/2006/main',r:'http://schemas.openxmlformats.org/officeDocument/2006/relationships'};
const $=id=>document.getElementById(id);
const xmlParser=new DOMParser();
let pres=null,currentSlide=0,zoom=0.9,dirty=false,idSeq=1;
let editingId=null,textEditBefore=null,templateMode='presentation';
let activeTheme=null,presentationTextDefaults=null;
let renderZoomOverride=null;
let fileController=null,recoveryController=null,pptxWriteAdapter=null;
let thumbnailsController=null,presenterNotesController=null,inspectorController=null;
let selectionController=null,historyController=null,slideshowController=null;
const ui={start:$('startScreen'),app:$('app'),file:$('fileInput'),img:$('imageInput'),title:$('docTitle'),list:$('slideList'),canvas:$('slideCanvas'),stageWrap:$('stageWrap'),save:$('saveBtn'),state:$('stateBadge'),status:$('slideStatus'),zoomText:$('zoomText'),present:$('presentOverlay'),presentSlide:$('presentSlide'),exitPresent:$('exitPresentBtn'),fullscreenPresent:$('fullscreenPresentBtn'),fullscreenPresentLabel:$('fullscreenPresentLabel'),presentCounter:$('presentCounter'),presentHelp:$('presentHelp'),template:$('templateDialog'),templateGrid:$('templateGrid'),notes:$('presenterNotes'),notesPanel:$('notesPanel'),notesCount:$('notesCount')};
function uid(prefix='o'){return prefix+(idSeq++).toString(36)+Date.now().toString(36).slice(-4)}
function markDirty(){dirty=true;ui.state.textContent='Unsaved';if(recoveryController)recoveryController.markDirty();setPresentationTitleValue()}
function presentationDisplayName(){return ((pres&&pres.name)||'Untitled presentation')+'.pptx'}
function normalizePresentationName(name){name=String(name||'').trim()||'Untitled presentation.pptx';name=name.replace(/\.pptx$/i,'').trim();return name||'Untitled presentation'}
function setPresentationTitleValue(){if(ui.title&&document.activeElement!==ui.title)ui.title.value=presentationDisplayName();document.title=presentationDisplayName()+(dirty?' •':'')+' — Presentations'}
function commitPresentationRename(){if(!pres){ui.title.value='Untitled presentation.pptx';return}const raw=String(ui.title.value||'').trim();if(raw===presentationDisplayName()){setPresentationTitleValue();return}const name=normalizePresentationName(raw);if(name!==pres.name){pres.name=name;markDirty();setReady('Unsaved');}setPresentationTitleValue()}
function markSaved(){dirty=false;ui.state.textContent='Saved';setPresentationTitleValue()}
function setReady(t='Ready'){ui.state.textContent=t}
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
function confirmIfDirty(){return !dirty || confirm('This presentation has unsaved changes. Continue and discard changes?')}
function resetOptionalPanelsForOpen(){setInspectorOpen(false,{relayout:false});if(presenterNotesController)presenterNotesController.resetClosed({relayout:false});else{ui.app.classList.add('hide-notes');const notes=$('toggleNotesBtn');if(notes)notes.textContent='Show presenter notes'}}
function showApp(){ui.start.classList.add('hidden');ui.app.classList.remove('hidden');resetOptionalPanelsForOpen()}

if(!window.InkDeskPresentationsSelection)throw new Error('Presentations selection controller is unavailable.');
selectionController=InkDeskPresentationsSelection.create({canvas:ui.canvas,getPresentation:()=>pres,getCurrentSlideData:()=>pres&&pres.slides.length?pres.slides[currentSlide]:null,getEditingId:()=>editingId,getZoom:()=>zoom,scaleX:sx,scaleY:sy,toPixelX:pxX,toPixelY:pxY,markDirty,renderSlide});
if(!window.InkDeskPresentationsHistory)throw new Error('Presentations history controller is unavailable.');
historyController=InkDeskPresentationsHistory.create({
  getState:()=>pres?{pres,currentSlide,selectedId:selectionController.getId()}:null,
  applyState:state=>{pres=state.pres;activeTheme=pres.theme||null;currentSlide=Math.min(state.currentSlide,pres.slides.length-1);selectionController.reset(state.selectedId,{render:false});editingId=null;markDirty();renderAll();},
  undoButton:$('undoBtn'),redoButton:$('redoBtn'),limit:80,
});

const LAYOUTS=[
  {id:'title',name:'Title slide',desc:'Title and subtitle'},
  {id:'titleContent',name:'Title and content',desc:'Heading with content area'},
  {id:'twoColumn',name:'Two columns',desc:'Heading with two content areas'},
  {id:'section',name:'Section heading',desc:'Large section title'},
  {id:'blank',name:'Blank',desc:'Empty slide'}
];
function makeSlide(layout='title'){
  const common={id:uid('s'),background:'#ffffff',title:'New slide',layout,objects:[],notes:''};
  if(layout==='blank')return common;
  if(layout==='section'){common.objects=[{id:uid(),type:'text',x:1000000,y:2300000,w:10200000,h:1100000,text:'Section title',font:'Arial',size:40,color:'#20242a',bold:true,align:'center',z:1},{id:uid(),type:'text',x:1700000,y:3500000,w:8800000,h:500000,text:'Section description',font:'Arial',size:20,color:'#6b7280',align:'center',z:2}];return common;}
  common.objects=[{id:uid(),type:'text',x:900000,y:650000,w:10400000,h:850000,text:layout==='title'?'Title':'Slide title',font:'Arial',size:layout==='title'?44:32,color:'#20242a',bold:true,align:layout==='title'?'center':'left',z:1}];
  if(layout==='title')common.objects.push({id:uid(),type:'text',x:1500000,y:2600000,w:9200000,h:650000,text:'Click to add subtitle',font:'Arial',size:24,color:'#6b7280',align:'center',z:2});
  if(layout==='titleContent')common.objects.push({id:uid(),type:'text',x:1000000,y:1750000,w:10200000,h:3500000,text:'Click to add text',font:'Arial',size:24,color:'#4b5563',align:'left',z:2});
  if(layout==='twoColumn'){common.objects.push({id:uid(),type:'text',x:900000,y:1750000,w:5000000,h:3500000,text:'Left column',font:'Arial',size:22,color:'#4b5563',align:'left',z:2});common.objects.push({id:uid(),type:'text',x:6300000,y:1750000,w:5000000,h:3500000,text:'Right column',font:'Arial',size:22,color:'#4b5563',align:'left',z:3});}
  return common;
}
function basePresentation(name='Untitled presentation',layout='title'){activeTheme={fonts:{majorLatin:'Arial',minorLatin:'Arial'},colors:{accent1:'#d64a24',dk1:'#000000',lt1:'#ffffff'}};return {name,width:12192000,height:6858000,source:'new',theme:activeTheme,compatibility:{engine:'0.19.0-beta-generated',presenterNotesEditor:true,presenterNotesExport:false},slides:[makeSlide(layout)]};}
function showTemplateDialog(mode='presentation'){templateMode=mode;ui.templateGrid.innerHTML='';LAYOUTS.forEach(l=>{const b=document.createElement('button');b.className='template-option';b.innerHTML='<div class="template-preview '+(l.id==='twoColumn'?'two ':l.id==='blank'?'blank ':'')+'"><span class="pv-title"></span><span class="pv-sub"></span></div><div class="template-name"></div><div class="template-desc"></div>';b.querySelector('.template-name').textContent=l.name;b.querySelector('.template-desc').textContent=l.desc;b.onclick=()=>chooseTemplate(l.id);ui.templateGrid.appendChild(b)});ui.template.classList.remove('hidden');}
function chooseTemplate(layout){ui.template.classList.add('hidden');if(templateMode==='presentation'){if(fileController)fileController.clearSource();pres=basePresentation('Untitled presentation',layout);currentSlide=0;selectionController.clear({render:false});historyController.reset();if(recoveryController)recoveryController.startNewDocument();showApp();renderAll();markDirty();}else{historyController.action(()=>{const created=makeSlide(layout);created.sourcePath='';created.sourcePresentationRid='';created.sourceSlideId='';pres.slides.splice(currentSlide+1,0,created);currentSlide++;selectionController.clear({render:false});markDirty();renderAll();});}}
function newPresentation(){if(!confirmIfDirty())return;showTemplateDialog('presentation');}
$('closeTemplateBtn').onclick=()=>ui.template.classList.add('hidden');ui.template.onclick=e=>{if(e.target===ui.template)ui.template.classList.add('hidden')};
function openDialog(){if(!confirmIfDirty())return;ui.file.value='';ui.file.click()}
function leaveTextEdit(){if(editingId){const ed=ui.canvas.querySelector('[data-id="'+editingId+'"] .editable');if(ed)ed.blur();editingId=null}}
ui.title.addEventListener('focus',event=>event.target.select());ui.title.addEventListener('blur',commitPresentationRename);ui.title.addEventListener('keydown',event=>{event.stopPropagation();if(event.key==='Enter'){event.preventDefault();event.target.blur()}else if(event.key==='Escape'){event.preventDefault();event.target.value=presentationDisplayName();event.target.blur()}});$('newBtn').onclick=newPresentation;$('newSmall').onclick=()=>{leaveTextEdit();newPresentation()};$('openBtn').onclick=openDialog;$('openSmall').onclick=()=>{leaveTextEdit();openDialog()};$('undoBtn').onclick=()=>historyController.undo();$('redoBtn').onclick=()=>historyController.redo();
function parseXml(s,context='PPTX package part'){if(window.InkDeskRuntime)return InkDeskRuntime.parseXml(s,context);const doc=xmlParser.parseFromString(s,'application/xml');if(doc.querySelector('parsererror'))throw new Error('Invalid XML in '+context);return doc}
function all(el,name){if(!el)return [];return Array.from(el.getElementsByTagName('*')).filter(n=>n.localName===name)}
function first(el,name){return all(el,name)[0]||null}
function attr(el,n,d=''){return el?el.getAttribute(n)||d:d}
function child(el,name){if(!el)return null;return Array.from(el.children).find(n=>n.localName===name)||null}
function textContent(el){return el?el.textContent||'':''}
function hex(c,def='#222222'){if(!c)return def;let v=attr(c,'val','');if(v&&/^[0-9a-fA-F]{6}$/.test(v))return '#'+v;return def}
function rgbParts(value){const m=String(value||'').match(/^#([0-9a-f]{6})$/i);if(!m)return null;return [parseInt(m[1].slice(0,2),16),parseInt(m[1].slice(2,4),16),parseInt(m[1].slice(4,6),16)];}
function rgbHex(parts){return '#'+parts.map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('');}
function rgbaColor(value,alpha){const p=rgbParts(value);if(!p)return value;return 'rgba('+p[0]+','+p[1]+','+p[2]+','+Math.max(0,Math.min(1,alpha))+')';}
function transformedColor(base,node){const rgb=rgbParts(base);if(!rgb||!node)return base;let out=rgb.slice(),alpha=1;const val=name=>{const n=first(node,name);return n?Math.max(0,Math.min(1,+attr(n,'val','100000')/100000)):null};const shade=val('shade');if(shade!=null)out=out.map(v=>v*shade);const tint=val('tint');if(tint!=null)out=out.map(v=>v+(255-v)*tint);const lumMod=val('lumMod');if(lumMod!=null)out=out.map(v=>v*lumMod);const lumOff=val('lumOff');if(lumOff!=null)out=out.map(v=>v+255*lumOff);const a=val('alpha');if(a!=null)alpha=a;const color=rgbHex(out);return alpha<.999?rgbaColor(color,alpha):color;}
function normalizePath(base,target){let parts=(base+'/'+target).split('/'),out=[];for(const p of parts){if(!p||p==='.')continue;if(p==='..')out.pop();else out.push(p)}return out.join('/')}
function relationshipPartPath(partPath){const slash=String(partPath||'').lastIndexOf('/');if(slash<0)return '_rels/'+partPath+'.rels';return partPath.slice(0,slash)+'/_rels/'+partPath.slice(slash+1)+'.rels'}
function serializeXml(doc){return new XMLSerializer().serializeToString(doc)}
function relMap(xml){const map={};all(xml,'Relationship').forEach(r=>{map[attr(r,'Id')]=attr(r,'Target')});return map}
async function loadPptx(file){return fileController.load(file)}
function parseSlideTransition(xml){
  const transition=first(xml,'transition');if(!transition)return {type:'none',rawType:'none',duration:0,advanceAfter:null};
  const effect=Array.from(transition.children||[]).find(n=>!['sndAc','extLst'].includes(n.localName));
  const rawType=effect?effect.localName:'fade';
  const type=rawType==='fade'?'fade':(['push','wipe','cover','uncover','split','cut','strips'].includes(rawType)?'slide':(['zoom','newsflash'].includes(rawType)?'zoom':'fade'));
  const speed=attr(transition,'spd','');const duration=speed==='slow'?2000:speed==='med'?1000:speed==='fast'?500:(+attr(transition,'dur','0')||0);
  return {type,rawType,duration,advanceAfter:attr(transition,'advTm','')||null};
}
async function parseSlide(zip,path,index){
  const xml=parseXml(await zip.file(path).async('text'));
  const relPath=relationshipPartPath(path);
  let rmap={};if(zip.file(relPath))rmap=relMap(parseXml(await zip.file(relPath).async('text')));
  const inheritance=await loadSlideInheritance(zip,path,rmap);
  const bgStyle=resolveSlideBackground(xml,inheritance.layoutXml,inheritance.masterXml);
  const slide={id:uid('s'),sourcePath:path,background:bgStyle.color||'#ffffff',backgroundImage:bgStyle.image||'',backgroundRepeat:bgStyle.repeat||'no-repeat',backgroundSize:bgStyle.size||'auto',objects:[],notes:'',originalNotes:'',notesPath:'',transition:parseSlideTransition(xml),originalTransition:null,title:'',compatibilityWarnings:[]};
  slide.originalTransition=slide.transition?JSON.parse(JSON.stringify(slide.transition)):null;
  const phMap=mergePlaceholderMaps(
    placeholderMap(inheritance.masterXml,inheritance.masterXml),
    placeholderMap(inheritance.layoutXml,inheritance.masterXml)
  );
  const slideRoot=xml.documentElement,layoutRoot=inheritance.layoutXml&&inheritance.layoutXml.documentElement;
  const showMaster=attr(slideRoot,'showMasterSp','1')!=='0'&&(!layoutRoot||attr(layoutRoot,'showMasterSp','1')!=='0');
  if(showMaster&&inheritance.masterXml&&inheritance.masterPath){
    await parseTreeObjects(zip,inheritance.masterPath,first(inheritance.masterXml,'spTree')||inheritance.masterXml,inheritance.masterRmap||{},slide.objects,{},null,slide.compatibilityWarnings,{skipPlaceholders:true,layer:'master'});
  }
  if(inheritance.layoutXml&&inheritance.layoutPath){
    await parseTreeObjects(zip,inheritance.layoutPath,first(inheritance.layoutXml,'spTree')||inheritance.layoutXml,inheritance.layoutRmap||{},slide.objects,{},null,slide.compatibilityWarnings,{skipPlaceholders:true,layer:'layout'});
  }
  await parseTreeObjects(zip,path,first(xml,'spTree')||xml,rmap,slide.objects,phMap,null,slide.compatibilityWarnings,{layer:'slide'});
  addMissingPlaceholders(slide,xml,phMap,inheritance.layoutXml);
  const notesInfo=await parsePresenterNotes(zip,path,rmap);slide.notes=notesInfo.text;slide.originalNotes=notesInfo.text;slide.notesPath=notesInfo.path;
  const titleObj=slide.objects.find(o=>(o.placeholderType==='title'||o.placeholderType==='ctrTitle')&&String(o.text||'').trim())||slide.objects.find(o=>o.type==='text'&&String(o.text||'').trim());
  slide.title=titleObj&&titleObj.text?titleObj.text.split(/\n/)[0].slice(0,40):'Slide '+(index+1);
  slide.objects.sort((a,b)=>(a.z||0)-(b.z||0));
  return slide;
}
function placeholderPrompt(type){return ({subTitle:'Double-click to add subtitle',title:'Double-click to add title',ctrTitle:'Double-click to add title',body:'Double-click to add text',obj:'Double-click to add text'}[type]||'');}
function placeholderObject(key,fallback){
  if(!fallback||fallback.x==null||fallback.y==null||fallback.w==null||fallback.h==null)return null;
  const type=String(key||'body|0').split('|')[0],st=fallback.textStyle||{},level=(st.levels&&st.levels[0])||st;
  return {id:uid(),type:'text',x:fallback.x,y:fallback.y,w:fallback.w,h:fallback.h,rot:fallback.rot||0,text:'',font:level.font||'+mn-lt',size:level.size||18,color:level.color||'#222',bold:Boolean(level.bold),italic:Boolean(level.italic),align:level.align||'left',paragraphs:[],margins:st.margins||{l:91440,t:45720,r:91440,b:45720},anchor:st.anchor||'top',fontScale:1,lineSpaceReduction:0,fill:'transparent',lineWidth:0,shape:'rect',placeholderType:type,placeholderIndex:String(key).split('|')[1]||'0',placeholderPrompt:placeholderPrompt(type),placeholderPromptStyle:st,syntheticPlaceholder:true,sourceLayer:'layout',fitText:false,z:10000+idSeq};
}
function addMissingPlaceholders(slide,slideXml,phMap,layoutXml){
  if(!layoutXml)return;
  const seen=new Set(),layoutKeys=new Set();
  all(first(slideXml,'spTree')||slideXml,'sp').forEach(n=>{const k=placeholderKey(n);if(k)seen.add(k)});
  all(first(layoutXml,'spTree')||layoutXml,'sp').forEach(n=>{const k=placeholderKey(n);if(k)layoutKeys.add(k)});
  for(const key of layoutKeys){
    const type=key.split('|')[0],fallback=phMap&&phMap[key];
    if(seen.has(key)||['dt','ftr','sldNum','hdr'].includes(type))continue;
    const o=placeholderObject(key,fallback);if(o)slide.objects.push(o);
  }
}
async function loadSlideInheritance(zip,slidePath,rmap){let layoutXml=null,masterXml=null,layoutPath=null,masterPath=null,layoutRmap={},masterRmap={};const layoutRid=Object.keys(rmap).find(k=>/(^|\/)slideLayouts?\/slideLayout\d*\.xml(?:$|[?#])/i.test(String(rmap[k]))||/slideLayout/i.test(String(rmap[k])));if(layoutRid){layoutPath=normalizePath(slidePath.split('/').slice(0,-1).join('/'),rmap[layoutRid]);if(zip.file(layoutPath)){layoutXml=parseXml(await zip.file(layoutPath).async('text'));const lr=relationshipPartPath(layoutPath);if(zip.file(lr)){layoutRmap=relMap(parseXml(await zip.file(lr).async('text')));const masterRid=Object.keys(layoutRmap).find(k=>/(^|\/)slideMasters?\/slideMaster\d*\.xml(?:$|[?#])/i.test(String(layoutRmap[k]))||/slideMaster/i.test(String(layoutRmap[k])));if(masterRid){masterPath=normalizePath(layoutPath.split('/').slice(0,-1).join('/'),layoutRmap[masterRid]);if(zip.file(masterPath)){masterXml=parseXml(await zip.file(masterPath).async('text'));const mr=relationshipPartPath(masterPath);if(zip.file(mr))masterRmap=relMap(parseXml(await zip.file(mr).async('text')));}}}}}return {layoutXml,masterXml,layoutPath,masterPath,layoutRmap,masterRmap};}
function resolveSlideBackground(slideXml,layoutXml,masterXml){for(const xml of [slideXml,layoutXml,masterXml]){if(!xml)continue;const bg=first(xml,'bg');if(!bg)continue;const ref=first(bg,'bgRef');if(ref){const idx=+attr(ref,'idx','0'),color=colorFromNode(ref,'#ffffff'),fill=activeTheme&&activeTheme.backgroundFills?activeTheme.backgroundFills[idx>=1000?idx-1000:idx]:null;if(fill&&fill.type==='image'&&fill.src){const veil=rgbaColor(color,.94);return {color,image:'linear-gradient('+veil+','+veil+'),url("'+fill.src+'")',repeat:fill.tile?'repeat':'no-repeat',size:fill.tile?(fill.tileWidth+'px '+fill.tileHeight+'px'):'cover'};}return {color};}return {color:colorFromNode(bg,'#ffffff')};}return {color:'#ffffff'};}
async function parseTreeObjects(zip,path,tree,rmap,out,phMap,parentGroup,warnings,options={}){
  const children=Array.from(tree.children||[]).filter(n=>['sp','pic','graphicFrame','grpSp','cxnSp'].includes(n.localName));
  for(const n of children){
    try{
      if(n.localName==='grpSp'){
        const g=groupTransform(n,parentGroup);
        await parseTreeObjects(zip,path,n,rmap,out,phMap,g,warnings,options);
        continue;
      }
      const key=placeholderKey(n);
      if(options.skipPlaceholders&&key)continue;
      const fallback=key&&phMap[key]?phMap[key]:null;
      let o=null;
      if(n.localName==='sp'){
        o=await parseImageFillShape(zip,path,n,rmap,fallback);
        if(!o)o=parseShape(n,fallback,Boolean(key));
      }else if(n.localName==='cxnSp')o=parseShape(n,fallback,false);
      else if(n.localName==='pic')o=await parsePic(zip,path,n,rmap,fallback);
      else if(n.localName==='graphicFrame')o=await parseGraphicFrame(zip,path,n,rmap,fallback);
      if(!o)continue;
      if(parentGroup)Object.assign(o,applyGroupRect(o,parentGroup));
      if(key){
        const ph=first(first(n,'nvPr')||n,'ph');
        o.placeholderType=attr(ph,'type','body');o.placeholderIndex=attr(ph,'idx','0');
        if(!cleanPptText(o.text||textContent(first(n,'txBody'))).trim()){
          o.placeholderPrompt=placeholderPrompt(o.placeholderType);
          o.placeholderPromptStyle=fallback&&fallback.textStyle?fallback.textStyle:{};
        }
      }
      const baseZ=options.layer==='master'?10:options.layer==='layout'?100:10000;
      o.z=baseZ+(o.z||0);
      o.sourceLayer=options.layer||'slide';o.sourceGrouped=Boolean(parentGroup);
      const cNvPr=first(n,'cNvPr');o.sourceNvId=attr(cNvPr,'id','');o.sourceElement=n.localName;o.sourcePartPath=path;
      o.originalText=typeof o.text==='string'?o.text:null;o.originalRect={x:o.x,y:o.y,w:o.w,h:o.h,rot:o.rot||0};
      if(options.layer==='master'||options.layer==='layout')o.templateObject=true;
      out.push(o);
    }catch(e){warnings.push((n.localName||'object')+': '+e.message);console.warn('object skipped',e)}
  }
}
async function parsePresenterNotes(zip,slidePath,rmap){
  const relPath=relationshipPartPath(slidePath);
  if(!zip.file(relPath))return {text:'',path:''};
  const relXml=parseXml(await zip.file(relPath).async('text'));
  const noteRel=all(relXml,'Relationship').find(r=>/\/notesSlide$/.test(attr(r,'Type')));
  if(!noteRel)return {text:'',path:''};
  const notePath=normalizePath(slidePath.split('/').slice(0,-1).join('/'),attr(noteRel,'Target'));
  const noteFile=zip.file(notePath);if(!noteFile)return {text:'',path:''};
  const noteXml=parseXml(await noteFile.async('text'));
  const bodies=all(noteXml,'sp').filter(sp=>{const ph=first(sp,'ph');return !ph||attr(ph,'type')==='body';});
  const lines=[];bodies.forEach(sp=>all(sp,'p').forEach(p=>{const t=all(p,'t').map(n=>textContent(n)).join('');if(t)lines.push(t)}));
  return {text:lines.join('\n'),path:notePath};
}

function xfrmObj(node,fallback=null){const x=first(node,'xfrm');if(!x&&fallback)return {...fallback};const off=first(x,'off'),ext=first(x,'ext');return {x:+attr(off,'x',fallback?String(fallback.x):'0'),y:+attr(off,'y',fallback?String(fallback.y):'0'),w:+attr(ext,'cx',fallback?String(fallback.w):'1500000'),h:+attr(ext,'cy',fallback?String(fallback.h):'800000'),rot:+attr(x,'rot',fallback?String((fallback.rot||0)*60000):'0')/60000};}
function placeholderKey(n){const ph=first(first(n,'nvPr')||n,'ph');if(!ph)return '';return (attr(ph,'type','body')||'body')+'|'+(attr(ph,'idx','0')||'0');}
function mapAlign(v,def='left'){return ({ctr:'center',r:'right',just:'justify',dist:'justify',l:'left'}[v]||def)}
function cloneBullet(v){return v?{...v}:null}
function normalizeBulletChar(v){const c=String(v||'•'),code=c.codePointAt(0)||0;return code>=0xe000&&code<=0xf8ff?'•':({'':'•','':'•','':'➤','':'◆'}[c]||c)}
function textStyleFromRPr(rp,base={}){
  const st={...base,bullet:cloneBullet(base.bullet)};if(!rp)return st;
  if(attr(rp,'sz'))st.size=Math.max(1,+attr(rp,'sz')/100);
  if(rp.hasAttribute('b'))st.bold=attr(rp,'b')==='1';
  if(rp.hasAttribute('i'))st.italic=attr(rp,'i')==='1';
  if(rp.hasAttribute('u'))st.underline=!['none','0'].includes(attr(rp,'u'));
  const fillNode=child(rp,'solidFill')||first(rp,'solidFill');if(fillNode)st.color=colorFromNode(fillNode,st.color||'#222');
  const latin=child(rp,'latin')||first(rp,'latin');if(latin&&attr(latin,'typeface'))st.font=normalizeFontName(attr(latin,'typeface'));
  if(attr(rp,'spc'))st.charSpacing=+attr(rp,'spc')/100;
  const hlink=child(rp,'hlinkClick')||first(rp,'hlinkClick');
  if(hlink){st.hyperlink=true;st.underline=true;if(!fillNode)st.color=(activeTheme&&activeTheme.colors&&activeTheme.colors.hlink)||'#cc9900';}
  return st;
}
function spacingPoints(container,name){
  const n=container&&(child(container,name)||first(container,name));if(!n)return null;
  const pts=child(n,'spcPts')||first(n,'spcPts');if(pts)return +attr(pts,'val','0')/100;
  return null;
}
function lineSpacingValue(container,base=1){
  const n=container&&(child(container,'lnSpc')||first(container,'lnSpc'));if(!n)return base;
  const pct=child(n,'spcPct')||first(n,'spcPct');if(pct)return Math.max(.45,+attr(pct,'val','100000')/100000);
  const pts=child(n,'spcPts')||first(n,'spcPts');if(pts)return {points:+attr(pts,'val','0')/100};
  return base;
}
function paragraphStyleFromLevel(level,base={}){
  let st={...base,bullet:cloneBullet(base.bullet)};if(!level)return st;
  if(attr(level,'algn'))st.align=mapAlign(attr(level,'algn'),st.align||'left');
  if(level.hasAttribute('marL'))st.marL=+attr(level,'marL','0');
  if(level.hasAttribute('indent'))st.indent=+attr(level,'indent','0');
  const before=spacingPoints(level,'spcBef'),after=spacingPoints(level,'spcAft');if(before!=null)st.spaceBefore=before;if(after!=null)st.spaceAfter=after;
  st.lineSpacing=lineSpacingValue(level,st.lineSpacing||1);
  const buNone=child(level,'buNone');
  if(buNone)st.bullet=null;
  else{
    const buChar=child(level,'buChar'),buAuto=child(level,'buAutoNum'),buFont=child(level,'buFont'),buClr=child(level,'buClr'),buSz=child(level,'buSzPct');
    if(buChar||buAuto||buFont||buClr||buSz){
      const bullet=cloneBullet(st.bullet)||{type:'char',char:'•'};
      if(buChar){bullet.type='char';bullet.char=normalizeBulletChar(attr(buChar,'char','•'));if(bullet.char==='•')bullet.font='';}
      if(buAuto){bullet.type='auto';bullet.char='•';bullet.startAt=+attr(buAuto,'startAt','1');bullet.autoType=attr(buAuto,'type','arabicPeriod');}
      if(buFont&&attr(buFont,'typeface'))bullet.font=normalizeFontName(attr(buFont,'typeface'));
      if(buClr)bullet.color=colorFromNode(buClr,bullet.color||st.color||'#222');
      if(buSz)bullet.scale=Math.max(.2,+attr(buSz,'val','100000')/100000);
      st.bullet=bullet;
    }
  }
  const def=child(level,'defRPr')||first(level,'defRPr');
  st=textStyleFromRPr(def,st);
  return st;
}
function defaultLevelStyles(){
  const color=(activeTheme&&activeTheme.colors&&(activeTheme.colors.tx1||activeTheme.colors.dk1))||'#222';
  return Array.from({length:9},(_,i)=>({size:18,color,bold:false,italic:false,underline:false,align:'left',font:'+mn-lt',charSpacing:0,lineSpacing:1,spaceBefore:0,spaceAfter:0,marL:i*457200,indent:0,bullet:null}));
}
function readLevelStyles(container,baseLevels){
  const bases=(baseLevels&&baseLevels.length?baseLevels:defaultLevelStyles()).map(v=>({...v,bullet:cloneBullet(v.bullet)}));
  return Array.from({length:9},(_,i)=>{
    const level=container&&(child(container,'lvl'+(i+1)+'pPr')||first(container,'lvl'+(i+1)+'pPr'));
    return paragraphStyleFromLevel(level,bases[i]||bases[0]);
  });
}
function parseDefaultTextStyle(presentationXml){
  const root=first(presentationXml,'defaultTextStyle');
  const levels=readLevelStyles(root,defaultLevelStyles());
  return {levels,...levels[0],anchor:'top',margins:{l:91440,t:45720,r:91440,b:45720}};
}
function masterTextStyle(masterXml,type){
  let base=(presentationTextDefaults&&presentationTextDefaults.levels)||defaultLevelStyles();
  const isTitle=type==='title'||type==='ctrTitle';
  base=base.map(v=>({...v,font:isTitle?'+mj-lt':(v.font||'+mn-lt'),bullet:cloneBullet(v.bullet)}));
  if(!masterXml){const levels=base;return {levels,...levels[0]};}
  const styleName=isTitle?'titleStyle':(['body','subTitle','obj'].includes(type)?'bodyStyle':'otherStyle');
  const style=first(masterXml,styleName),levels=readLevelStyles(style,base);
  return {levels,...levels[0]};
}
function placeholderTextStyle(n,masterXml,type){
  let st=masterTextStyle(masterXml,type),levels=st.levels;
  const tx=first(n,'txBody');
  const defaultMargins={l:91440,t:45720,r:91440,b:45720};
  let margins={...(st.margins||defaultMargins)},anchor=st.anchor||'top';
  if(tx){
    const body=child(tx,'bodyPr');
    if(body){
      const am={ctr:'middle',b:'bottom',t:'top'};if(attr(body,'anchor'))anchor=am[attr(body,'anchor')]||'top';
      margins={l:body.hasAttribute('lIns')?+attr(body,'lIns'):margins.l,t:body.hasAttribute('tIns')?+attr(body,'tIns'):margins.t,r:body.hasAttribute('rIns')?+attr(body,'rIns'):margins.r,b:body.hasAttribute('bIns')?+attr(body,'bIns'):margins.b};
    }
    const lst=child(tx,'lstStyle');if(lst)levels=readLevelStyles(lst,levels);
    const para=child(tx,'p'),pPr=para&&child(para,'pPr');if(pPr)levels[0]=paragraphStyleFromLevel(pPr,levels[0]);
  }
  return {levels,...levels[0],anchor,margins};
}
function placeholderMap(xml,masterXml=null){
  const map={};if(!xml)return map;
  all(xml,'sp').forEach(n=>{
    const k=placeholderKey(n);if(!k)return;
    const ph=first(first(n,'nvPr')||n,'ph'),type=attr(ph,'type','body')||'body';
    const entry={textStyle:placeholderTextStyle(n,masterXml,type)};
    if(first(n,'xfrm'))Object.assign(entry,xfrmObj(n));
    map[k]=entry;
  });
  return map;
}
function mergePlaceholderMaps(){
  const out={};
  for(const m of arguments){for(const [k,v] of Object.entries(m||{})){
    const prev=out[k]||{},pt=prev.textStyle||{},vt=v.textStyle||{};
    const levels=Array.from({length:9},(_,i)=>({...((pt.levels&&pt.levels[i])||{}),...((vt.levels&&vt.levels[i])||{}),bullet:cloneBullet(((vt.levels&&vt.levels[i])||{}).bullet!==undefined?vt.levels[i].bullet:((pt.levels&&pt.levels[i])||{}).bullet)}));
    out[k]={...prev,...v,textStyle:{...pt,...vt,levels}};
  }}
  return out;
}
function groupTransform(n,parent=null){const x=first(first(n,'grpSpPr')||n,'xfrm');if(!x)return parent;const off=first(x,'off'),ext=first(x,'ext'),chOff=first(x,'chOff'),chExt=first(x,'chExt');const own={x:+attr(off,'x','0'),y:+attr(off,'y','0'),w:+attr(ext,'cx','1'),h:+attr(ext,'cy','1'),cx:+attr(chOff,'x','0'),cy:+attr(chOff,'y','0'),cw:+attr(chExt,'cx',attr(ext,'cx','1')),ch:+attr(chExt,'cy',attr(ext,'cy','1')),rot:+attr(x,'rot','0')/60000};return parent?applyGroupToGroup(own,parent):own;}
function applyGroupRect(t,g){if(!g)return t;const sxg=(g.w||1)/(g.cw||g.w||1),syg=(g.h||1)/(g.ch||g.h||1);return {x:g.x+(t.x-g.cx)*sxg,y:g.y+(t.y-g.cy)*syg,w:t.w*sxg,h:t.h*syg,rot:(t.rot||0)+(g.rot||0)};}
function applyGroupToGroup(g,p){const r=applyGroupRect({x:g.x,y:g.y,w:g.w,h:g.h,rot:g.rot},p);return {...g,x:r.x,y:r.y,w:r.w,h:r.h,rot:r.rot,cx:g.cx,cy:g.cy,cw:g.cw,ch:g.ch};}
function cleanPptText(v){return String(v||'').replace(/\u00ad/g,'').replace(/\u000b/g,'\n')}
function normalizeFontName(v){return window.LocalPresentationsCompatibility?window.LocalPresentationsCompatibility.normalizeFontName(v):String(v||'Arial').trim()}
function safeFont(v){return window.LocalPresentationsCompatibility?window.LocalPresentationsCompatibility.safeFont(v,activeTheme):'Arial, Helvetica, sans-serif'}
function colorFromNode(container,def='#222222'){
  if(!container)return def;
  const srgb=first(container,'srgbClr');
  if(srgb)return transformedColor(hex(srgb,def),srgb);
  const sys=first(container,'sysClr');
  if(sys){const last=attr(sys,'lastClr','');if(/^[0-9a-fA-F]{6}$/.test(last))return transformedColor('#'+last,sys);}
  const scheme=first(container,'schemeClr');
  if(scheme){const key=attr(scheme,'val','');const base=window.LocalPresentationsCompatibility?window.LocalPresentationsCompatibility.schemeColor(key,activeTheme,def):def;return transformedColor(base,scheme);}
  return def;
}
function parseThemeXml(xml){
  const result={fonts:{majorLatin:'Arial',minorLatin:'Arial',majorEastAsia:'Arial',minorEastAsia:'Arial',majorComplex:'Arial',minorComplex:'Arial'},colors:{},backgroundFills:{}};
  if(!xml)return result;
  const fontScheme=first(xml,'fontScheme'),major=fontScheme&&first(fontScheme,'majorFont'),minor=fontScheme&&first(fontScheme,'minorFont');
  const readFace=(parent,nodeName,fallback)=>{const n=parent&&first(parent,nodeName);return n&&attr(n,'typeface')?attr(n,'typeface'):fallback};
  result.fonts.majorLatin=readFace(major,'latin','Arial');result.fonts.minorLatin=readFace(minor,'latin','Arial');
  result.fonts.majorEastAsia=readFace(major,'ea',result.fonts.majorLatin);result.fonts.minorEastAsia=readFace(minor,'ea',result.fonts.minorLatin);
  result.fonts.majorComplex=readFace(major,'cs',result.fonts.majorLatin);result.fonts.minorComplex=readFace(minor,'cs',result.fonts.minorLatin);
  const clrScheme=first(xml,'clrScheme');
  if(clrScheme)Array.from(clrScheme.children).forEach(entry=>{const srgb=first(entry,'srgbClr'),sys=first(entry,'sysClr');if(srgb)result.colors[entry.localName]=hex(srgb,'#000000');else if(sys){const last=attr(sys,'lastClr','000000');result.colors[entry.localName]='#'+last;}});
  result.colors.bg1=result.colors.lt1||'#ffffff';result.colors.tx1=result.colors.dk1||'#000000';result.colors.bg2=result.colors.lt2||'#ffffff';result.colors.tx2=result.colors.dk2||'#000000';
  return result;
}
function imageDimensions(data,ext){try{if(ext==='png'&&data.length>24)return {w:(data[16]<<24)|(data[17]<<16)|(data[18]<<8)|data[19],h:(data[20]<<24)|(data[21]<<16)|(data[22]<<8)|data[23]};if(ext==='jpg'||ext==='jpeg'){let i=2;while(i+9<data.length){if(data[i]!==0xff){i++;continue;}const marker=data[i+1],len=(data[i+2]<<8)+data[i+3];if([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker))return {h:(data[i+5]<<8)+data[i+6],w:(data[i+7]<<8)+data[i+8]};i+=Math.max(2,len+2);}}}catch(error){console.warn('Image dimensions could not be parsed; using a fallback ratio.',error)}return {w:16,h:1};}
async function loadTheme(zip){
  const candidates=['ppt/theme/theme1.xml'];
  for(const path of candidates){const file=zip.file(path);if(!file)continue;const xml=parseXml(await file.async('text')),result=parseThemeXml(xml);const relPath=relationshipPartPath(path);let rmap={};if(zip.file(relPath))rmap=relMap(parseXml(await zip.file(relPath).async('text')));const list=first(first(xml,'fmtScheme'),'bgFillStyleLst');if(list){let index=0;for(const fill of Array.from(list.children||[])){index++;if(fill.localName!=='blipFill')continue;const blip=first(fill,'blip'),rid=blip&&(blip.getAttributeNS(NS.r,'embed')||attr(blip,'r:embed'));if(!rid||!rmap[rid])continue;const mediaPath=normalizePath(path.split('/').slice(0,-1).join('/'),rmap[rid]),media=zip.file(mediaPath);if(!media)continue;const ext=mediaPath.split('.').pop().toLowerCase(),bytes=await media.async('uint8array'),dim=imageDimensions(bytes,ext),mime=ext==='png'?'image/png':(ext==='jpg'||ext==='jpeg'?'image/jpeg':'image/'+ext),src='data:'+mime+';base64,'+await media.async('base64'),tile=first(fill,'tile'),scaleX=tile?Math.max(.01,+attr(tile,'sx','100000')/100000):1,scaleY=tile?Math.max(.01,+attr(tile,'sy','100000')/100000):1;result.backgroundFills[index]={type:'image',src,tile:Boolean(tile),tileWidth:Math.max(1,dim.w*scaleX),tileHeight:Math.max(1,dim.h*scaleY)};} }return result;}
  return parseThemeXml(null);
}
function parseText(txBody,inherited={}){
  const defaults={size:18,color:(activeTheme&&activeTheme.colors&&(activeTheme.colors.tx1||activeTheme.colors.dk1))||'#222',bold:false,italic:false,underline:false,align:'left',font:'+mn-lt',anchor:'top',margins:{l:91440,t:45720,r:91440,b:45720},lineSpacing:1,spaceBefore:0,spaceAfter:0,marL:0,indent:0,bullet:null};
  const base={...defaults,...inherited,margins:{...defaults.margins,...(inherited.margins||{})}};
  let levels=(inherited.levels&&inherited.levels.length?inherited.levels:Array.from({length:9},()=>({...base,bullet:cloneBullet(base.bullet)}))).map(v=>({...base,...v,bullet:cloneBullet(v.bullet)}));
  if(!txBody)return {text:'',paragraphs:[],fontScale:1,lineSpaceReduction:0,autoFit:'none',levels,...base};
  const bodyPr=child(txBody,'bodyPr');
  const margins={l:bodyPr&&bodyPr.hasAttribute('lIns')?+attr(bodyPr,'lIns'):base.margins.l,t:bodyPr&&bodyPr.hasAttribute('tIns')?+attr(bodyPr,'tIns'):base.margins.t,r:bodyPr&&bodyPr.hasAttribute('rIns')?+attr(bodyPr,'rIns'):base.margins.r,b:bodyPr&&bodyPr.hasAttribute('bIns')?+attr(bodyPr,'bIns'):base.margins.b};
  const anchorMap={ctr:'middle',b:'bottom',t:'top'},anchor=bodyPr&&attr(bodyPr,'anchor')?(anchorMap[attr(bodyPr,'anchor')]||'top'):(base.anchor||'top');
  const localList=child(txBody,'lstStyle');if(localList)levels=readLevelStyles(localList,levels);
  const normAutofit=bodyPr&&(child(bodyPr,'normAutofit')||first(bodyPr,'normAutofit')),shapeAutofit=bodyPr&&(child(bodyPr,'spAutoFit')||first(bodyPr,'spAutoFit'));
  const fontScale=normAutofit?Math.max(.1,+attr(normAutofit,'fontScale','100000')/100000):1;
  const lineSpaceReduction=normAutofit?Math.max(0,+attr(normAutofit,'lnSpcReduction','0')/100000):0;
  const paragraphs=[],plain=[];
  all(txBody,'p').forEach((p,paragraphIndex)=>{
    const pPr=child(p,'pPr'),level=Math.max(0,Math.min(8,+attr(pPr,'lvl','0')||0));
    const pStyle=paragraphStyleFromLevel(pPr,levels[level]||levels[0]||base),runs=[];
    Array.from(p.children).forEach(node=>{
      if(!['r','fld','br'].includes(node.localName))return;
      if(node.localName==='br'){runs.push({...pStyle,bullet:undefined,text:'\n'});return;}
      const rp=child(node,'rPr'),st=textStyleFromRPr(rp,pStyle),txt=cleanPptText(textContent(first(node,'t')));
      runs.push({...st,bullet:undefined,text:txt});
    });
    if(!runs.length){const end=child(p,'endParaRPr');if(end)runs.push({...textStyleFromRPr(end,pStyle),bullet:undefined,text:''});}
    const text=runs.map(r=>r.text).join('');plain.push(text);
    const bullet=pStyle.bullet&&text.trim()?{...pStyle.bullet}:null;
    if(bullet&&bullet.type==='auto')bullet.char=String((bullet.startAt||1)+paragraphIndex)+'.';
    paragraphs.push({level,align:pStyle.align||base.align,lineSpacing:pStyle.lineSpacing||1,spaceBefore:pStyle.spaceBefore||0,spaceAfter:pStyle.spaceAfter||0,marL:pStyle.marL||0,indent:pStyle.indent||0,bullet,runs});
  });
  const firstRun=paragraphs.flatMap(p=>p.runs).find(r=>r.text)||levels[0]||base;
  return {...base,...levels[0],...firstRun,text:plain.join('\n').replace(/\n+$/,''),paragraphs,margins,anchor,fontScale,lineSpaceReduction,autoFit:normAutofit?'normal':shapeAutofit?'shape':'none',levels};
}
function parseShape(n,fallback=null,forceText=false){
  const t=xfrmObj(n,fallback),tx=parseText(first(n,'txBody'),fallback&&fallback.textStyle?fallback.textStyle:{}),spPr=first(n,'spPr');
  const solid=spPr&&child(spPr,'solidFill'),noFill=spPr&&child(spPr,'noFill'),fill=solid?colorFromNode(solid,'transparent'):(noFill?'transparent':'transparent');
  const useBackgroundFill=attr(n,'useBgFill')==='1';
  let line='#000000',lineWidth=0;const ln=spPr&&child(spPr,'ln');
  if(ln&&!child(ln,'noFill')&&(child(ln,'solidFill')||first(ln,'solidFill'))){line=colorFromNode(child(ln,'solidFill')||first(ln,'solidFill'),'#333333');lineWidth=Math.max(.25,(+attr(ln,'w','9525'))/9525);}
  const prst=attr(spPr&&child(spPr,'prstGeom'),'prst','rect');
  if(tx.text||forceText){return {...t,id:uid(),type:'text',text:tx.text,font:tx.font,size:tx.size,color:tx.color,bold:tx.bold,italic:tx.italic,underline:tx.underline,align:tx.align,paragraphs:tx.paragraphs,margins:tx.margins,anchor:tx.anchor,fontScale:tx.fontScale,lineSpaceReduction:tx.lineSpaceReduction,fill,line,lineWidth,shape:prst,useBackgroundFill,fitText:tx.autoFit==='normal',z:idSeq};}
  if(fill!=='transparent'||lineWidth>0||useBackgroundFill)return {...t,id:uid(),type:'shape',shape:prst,fill,line,lineWidth,useBackgroundFill,z:idSeq};
  return null;
}
async function imageObjectFromBlip(zip,basePath,n,rmap,fallback=null){const t=xfrmObj(n,fallback);const blip=first(n,'blip');const rid=blip&&(blip.getAttributeNS(NS.r,'embed')||attr(blip,'r:embed'));if(!rid||!rmap[rid])return null;const mediaPath=normalizePath(basePath.split('/').slice(0,-1).join('/'),rmap[rid]);const f=zip.file(mediaPath);if(!f)return null;const ext=mediaPath.split('.').pop().toLowerCase();const mime=ext==='png'?'image/png':ext==='jpg'||ext==='jpeg'?'image/jpeg':ext==='gif'?'image/gif':'image/'+ext;const data='data:'+mime+';base64,'+await f.async('base64');const blipFill=first(n,'blipFill');const srcRect=first(blipFill,'srcRect')||first(n,'srcRect');const crop={l:+attr(srcRect,'l','0')/1000,t:+attr(srcRect,'t','0')/1000,r:+attr(srcRect,'r','0')/1000,b:+attr(srcRect,'b','0')/1000};const hasCrop=Boolean(srcRect&&(crop.l||crop.t||crop.r||crop.b));const fitMode=first(blipFill,'tile')?'tile':(hasCrop?'cover':'fill');return {...t,id:uid(),type:'image',src:data,mediaKey:mediaPath,ext,crop,fitMode,cropZoom:hasCrop?Math.max(1,100/Math.max(1,100-crop.l-crop.r),100/Math.max(1,100-crop.t-crop.b)):1,cropX:hasCrop?(crop.l+100-crop.r)/2:50,cropY:hasCrop?(crop.t+100-crop.b)/2:50,z:idSeq};}
async function parseImageFillShape(zip,basePath,n,rmap,fallback=null){const spPr=first(n,'spPr');if(!spPr||!first(spPr,'blipFill'))return null;return imageObjectFromBlip(zip,basePath,n,rmap,fallback);}
async function parsePic(zip,slidePath,n,rmap,fallback=null){return imageObjectFromBlip(zip,slidePath,n,rmap,fallback);}
function parseTable(n,fallback=null){const t=xfrmObj(n,fallback);const rows=all(n,'tr');if(!rows.length)return null;let cells=[];rows.forEach(r=>{let row=[];all(r,'tc').forEach(tc=>row.push(textContent(tc).trim()));cells.push(row)});return {...t,id:uid(),type:'table',cells,z:idSeq};}
function cachedChartValues(container){if(!container)return[];const cache=first(container,'strCache')||first(container,'numCache')||first(container,'multiLvlStrCache');if(!cache)return[];return all(cache,'pt').sort((a,b)=>(+attr(a,'idx','0'))-(+attr(b,'idx','0'))).map(pt=>{const v=textContent(first(pt,'v'));const n=Number(v);return v!==''&&Number.isFinite(n)?n:v})}
async function parseGraphicFrame(zip,slidePath,n,rmap,fallback=null){
  if(first(n,'tbl'))return parseTable(n,fallback);
  const chartRef=first(n,'chart');const rid=chartRef&&(chartRef.getAttributeNS(NS.r,'id')||attr(chartRef,'r:id'));if(!rid||!rmap[rid])return null;
  const chartPath=normalizePath(slidePath.split('/').slice(0,-1).join('/'),rmap[rid]),file=zip.file(chartPath);if(!file)return null;
  const xml=parseXml(await file.async('text')),t=xfrmObj(n,fallback),plot=first(xml,'plotArea');
  const chartNode=plot&&Array.from(plot.children||[]).find(x=>/Chart$/.test(x.localName));const chartType=chartNode?chartNode.localName.replace(/Chart$/,''):'chart';
  const titleNode=first(first(xml,'title'),'tx')||first(xml,'title');const title=titleNode?all(titleNode,'t').map(textContent).join(''):'';
  const series=[];for(const ser of all(chartNode||xml,'ser')){const tx=first(ser,'tx'),name=(cachedChartValues(tx)[0]??all(tx,'v').map(textContent)[0]??('Series '+(series.length+1)));const cat=first(ser,'cat')||first(ser,'xVal'),val=first(ser,'val')||first(ser,'yVal');series.push({name:String(name),categories:cachedChartValues(cat),values:cachedChartValues(val).map(v=>Number(v)||0)});}
  const categories=series.find(x=>x.categories.length)?.categories||[];
  return {...t,id:uid(),type:'chart',chartType,title,categories,series,chartPath,z:idSeq};
}
ui.file.onchange=e=>{const f=e.target.files[0];if(!f)return;loadPptx(f).catch(err=>{console.error(err);alert('Presentation could not be opened: '+err.message)}).finally(()=>{ui.file.value=''})};
function slideViewport(){const pw=pres&&pres.width?pres.width:12192000,ph=pres&&pres.height?pres.height:6858000,maxW=960,maxH=540,ratio=pw/ph||16/9;let w=maxW,h=w/ratio;if(h>maxH){h=maxH;w=h*ratio}return {w,h};}function sx(){return slideViewport().w/pres.width}function sy(){return slideViewport().h/pres.height}function activeRenderZoom(){return renderZoomOverride==null?zoom:renderZoomOverride}function pxX(x){return x*sx()*activeRenderZoom()}function pxY(y){return y*sy()*activeRenderZoom()}
function renderAll(){if(!pres)return;setPresentationTitleValue();syncTransitionControl();renderPresentations();renderSlide();renderPresenterNotes();}
function goToSlide(index,focusThumb=false){
  if(!pres||!pres.slides.length)return;
  currentSlide=Math.max(0,Math.min(pres.slides.length-1,index));
  selectionController.clear({render:false});editingId=null;
  renderAll();
  requestAnimationFrame(()=>{
    const thumb=ui.list.querySelector('[data-slide-index="'+currentSlide+'"]');
    if(thumb){thumb.scrollIntoView({block:'nearest',behavior:'smooth'});if(focusThumb)thumb.focus({preventScroll:true});}
  });
}
function renderPresentations(){if(thumbnailsController)thumbnailsController.render();}
function objectVisibleText(o){
  if(!o)return '';
  if(o.paragraphs&&o.paragraphs.length)return o.paragraphs.map(p=>(p.runs||[]).map(r=>r.text||'').join('')).join('\n');
  return cleanPptText(o.text||'');
}
function normalizedPresentationText(o){return objectVisibleText(o).replace(/\s+/g,' ').trim().toLocaleLowerCase();}
function isInstructionalPlaceholder(o){
  if(!o||o.type!=='text')return false;
  const t=normalizedPresentationText(o);
  if(!t)return Boolean(o.syntheticPlaceholder||o.placeholderPrompt);
  const prompt=/^(?:double[- ]?click|click|tap|double[- ]?tap|clique|dê um toque duplo|toque duas vezes)\s+(?:here\s+)?(?:to\s+)?(?:add|adicionar|editar|inserir)\b/i;
  return Boolean(o.syntheticPlaceholder||o.placeholderType||o.placeholderPrompt)&&prompt.test(t);
}
function rectOverlapRatio(a,b){
  const l=Math.max(a.x||0,b.x||0),t=Math.max(a.y||0,b.y||0),r=Math.min((a.x||0)+(a.w||0),(b.x||0)+(b.w||0)),bt=Math.min((a.y||0)+(a.h||0),(b.y||0)+(b.h||0));
  const inter=Math.max(0,r-l)*Math.max(0,bt-t),small=Math.min(Math.max(1,(a.w||0)*(a.h||0)),Math.max(1,(b.w||0)*(b.h||0)));
  return inter/small;
}
function presentationObjectScore(o){
  const layer=o.sourceLayer==='slide'?30:o.sourceLayer==='layout'?20:o.sourceLayer==='master'?10:25;
  return layer+(o.templateObject?0:8)+(o.placeholderType?2:0)+Math.min(4,Math.log10(Math.max(10,(o.w||1)*(o.h||1)))-10);
}
function presentationObjects(slideData){
  const result=[];
  for(const o of slideData.objects||[]){
    if(isInstructionalPlaceholder(o))continue;
    if(o.syntheticPlaceholder&&!normalizedPresentationText(o))continue;
    if(o.type==='text'){
      const key=normalizedPresentationText(o);
      if(key.length>=3){
        const duplicateIndex=result.findIndex(prev=>prev.type==='text'&&normalizedPresentationText(prev)===key&&rectOverlapRatio(prev,o)>.42);
        if(duplicateIndex>=0){
          if(presentationObjectScore(o)>presentationObjectScore(result[duplicateIndex]))result[duplicateIndex]=o;
          continue;
        }
      }
    }else if(o.type==='image'&&(o.mediaKey||o.src)){
      const key=o.mediaKey||o.src;
      const duplicateIndex=result.findIndex(prev=>prev.type==='image'&&(prev.mediaKey||prev.src)===key&&rectOverlapRatio(prev,o)>.28);
      if(duplicateIndex>=0){
        if(presentationObjectScore(o)>presentationObjectScore(result[duplicateIndex]))result[duplicateIndex]=o;
        continue;
      }
    }
    result.push(o);
  }
  return result;
}
function renderSlide(target=ui.canvas,slide=pres.slides[currentSlide],present=false,renderScale=null){
  const vp=slideViewport(),scale=renderScale==null?zoom:renderScale,previousOverride=renderZoomOverride;
  renderZoomOverride=scale;
  target.innerHTML='';
  target.style.width=(vp.w*scale)+'px';
  target.style.height=(vp.h*scale)+'px';
  target.style.backgroundColor=slide.background||'#fff';
  target.style.backgroundImage=slide.backgroundImage||'none';
  target.style.backgroundRepeat=slide.backgroundRepeat||'no-repeat';
  target.style.backgroundSize=slide.backgroundSize||'auto';
  target.style.transform='none';
  const objects=present?presentationObjects(slide):(slide.objects||[]);
  objects.forEach(o=>{const node=renderObject(o,present,slide);if(node)target.appendChild(node)});
  renderZoomOverride=previousOverride;
  if(target===ui.canvas){
    ui.status.textContent='Slide '+(currentSlide+1)+' of '+pres.slides.length;
    ui.zoomText.textContent=Math.round(zoom*100)+'%';
    $('zoomRange').value=Math.round(zoom*100);
    $('bottomZoomRange').value=Math.round(zoom*100);
    updateInspector();
  }
}
function renderObject(o,present=false,slideData=pres.slides[currentSlide]){
  if(present&&isInstructionalPlaceholder(o))return null;
  const rz=activeRenderZoom();
  const e=document.createElement('div');e.className='obj '+o.type+(o.id===selectionController.getId()&&!present?' selected':'')+(o.id===editingId?' editing':'');e.dataset.id=o.id;e.style.left=pxX(o.x)+'px';e.style.top=pxY(o.y)+'px';e.style.width=pxX(o.w)+'px';e.style.height=pxY(o.h)+'px';e.style.zIndex=String(Math.max(1,Number(o.z)||1));e.style.opacity=o.opacity==null?1:o.opacity;e.style.transform='rotate('+(o.rot||0)+'deg)';e.style.transformOrigin='center center';
  if(o.type==='text'){
    e.style.fontFamily=safeFont(o.font);e.style.fontSize=Math.max(1,(o.size||18)*(o.fontScale||1)*rz)+'px';e.style.color=o.color||'#222';e.style.fontWeight=o.bold?'800':'400';e.style.fontStyle=o.italic?'italic':'normal';e.style.textDecoration=o.underline?'underline':'none';e.style.textAlign=o.align||'left';e.style.background=o.fill==='transparent'?'transparent':(o.fill||'transparent');if(o.lineWidth)e.style.border=(o.lineWidth*rz)+'px solid '+(o.line||'#333');
    const m=o.margins||{l:0,t:0,r:0,b:0};e.style.padding=pxY(m.t)+'px '+pxX(m.r)+'px '+pxY(m.b)+'px '+pxX(m.l)+'px';
    const inn=document.createElement('div');inn.className='editable';inn.contentEditable=o.id===editingId&&!present?'true':'false';inn.style.display='flex';inn.style.flexDirection='column';inn.style.justifyContent=o.anchor==='middle'?'center':o.anchor==='bottom'?'flex-end':'flex-start';
    const emptyPlaceholder=o.placeholderPrompt&&!String(o.text||'').trim()&&o.id!==editingId&&!present;
    if(emptyPlaceholder){inn.classList.add('placeholder-empty');inn.textContent=o.placeholderPrompt;e.style.border='1px dotted rgba(70,70,70,.75)';inn.style.color=(o.placeholderPromptStyle&&o.placeholderPromptStyle.color)||o.color||'#666';}
    else if(o.paragraphs&&o.paragraphs.length&&o.id!==editingId){
      o.paragraphs.forEach(p=>{
        const pe=document.createElement('div');pe.className='text-paragraph';pe.style.position='relative';pe.style.boxSizing='border-box';pe.style.textAlign=p.align||o.align||'left';
        const ls=p.lineSpacing&&typeof p.lineSpacing==='object'?Math.max(.72,(p.lineSpacing.points||o.size||18)/(o.size||18)):Math.max(.72,(p.lineSpacing||1)-(o.lineSpaceReduction||0));pe.style.lineHeight=String(ls);
        pe.style.marginTop=((p.spaceBefore||0)*rz)+'px';pe.style.marginBottom=((p.spaceAfter||0)*rz)+'px';
        const marL=p.marL||0,indent=p.indent||0;pe.style.paddingLeft=pxX(Math.max(0,marL))+'px';
        if(p.bullet){const be=document.createElement('span');be.className='text-bullet';be.textContent=p.bullet.char||'•';be.style.position='absolute';be.style.left=pxX(Math.max(0,marL+indent))+'px';be.style.color=p.bullet.color||o.color||'#222';be.style.fontFamily=safeFont(p.bullet.font||o.font);be.style.fontSize=Math.max(1,(o.size||18)*(p.bullet.scale||1)*(o.fontScale||1)*rz)+'px';pe.appendChild(be);}else if(indent)pe.style.textIndent=pxX(indent)+'px';
        p.runs.forEach(r=>{const sp=document.createElement('span');sp.className='text-run';sp.textContent=r.text;sp.style.fontFamily=safeFont(r.font||o.font);sp.style.fontSize=Math.max(1,(r.size||o.size||18)*(o.fontScale||1)*rz)+'px';sp.style.color=r.color||o.color||'#222';sp.style.fontWeight=r.bold?'800':'400';sp.style.fontStyle=r.italic?'italic':'normal';sp.style.textDecoration=r.underline?'underline':'none';if(r.charSpacing)sp.style.letterSpacing=(r.charSpacing*rz)+'px';pe.appendChild(sp)});
        inn.appendChild(pe);
      });
    }else inn.innerText=o.text||'';
    e.appendChild(inn);e.ondblclick=ev=>{ev.stopPropagation();textEditBefore=historyController.capture();editingId=o.id;selectionController.setId(o.id,{render:false});renderSlide();requestAnimationFrame(()=>{const ed=ui.canvas.querySelector('[data-id="'+o.id+'"] .editable');if(ed){ed.focus();const r=document.createRange();r.selectNodeContents(ed);const sel=getSelection();sel.removeAllRanges();sel.addRange(r)}})};
    inn.onpointerdown=ev=>{if(inn.contentEditable==='true')ev.stopPropagation()};inn.onblur=()=>{if(editingId!==o.id)return;const nt=cleanPptText(inn.innerText),before=textEditBefore;textEditBefore=null;if(o.text!==nt){o.text=nt;o.paragraphs=null;o.fitText=false;markDirty();renderPresentations();historyController.push(before)}editingId=null;renderSlide()};
    if(o.fitText){const fit=()=>requestAnimationFrame(()=>fitTextElement(e,inn));if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit).catch(fit);else fit();}
  }else if(o.type==='image'){
    const img=new Image();img.src=o.src;img.draggable=false;img.style.objectFit=o.fitMode==='fill'?'fill':(o.fitMode==='contain'?'contain':'cover');img.style.transform='scale('+(o.cropZoom||1)+')';img.style.objectPosition=(o.cropX==null?50:o.cropX)+'% '+(o.cropY==null?50:o.cropY)+'%';e.appendChild(img);
    if(o.placeholderPrompt&&!present){const ps=o.placeholderPromptStyle||{},hint=document.createElement('div');hint.className='placeholder-prompt';hint.textContent=o.placeholderPrompt;hint.style.position='absolute';hint.style.inset='0';hint.style.boxSizing='border-box';hint.style.border='1px dotted rgba(70,70,70,.75)';hint.style.padding=(6*rz)+'px '+(8*rz)+'px';hint.style.color=ps.color||'#666';hint.style.fontFamily=safeFont(ps.font||'Arial');hint.style.fontSize=Math.max(11,(ps.size||22)*rz)+'px';hint.style.textAlign=ps.align||'center';hint.style.pointerEvents='none';hint.style.overflow='hidden';hint.style.zIndex='2';e.appendChild(hint);}
  }else if(o.type==='table'){
    e.classList.add('table');const cols=Math.max(...o.cells.map(r=>r.length));e.style.gridTemplateColumns='repeat('+cols+',1fr)';o.cells.forEach(r=>{for(let i=0;i<cols;i++){const c=document.createElement('div');c.textContent=r[i]||'';c.style.fontSize=12*rz+'px';e.appendChild(c)}});
  }else if(o.type==='chart'){
    renderChartObject(e,o,rz);
  }else{
    e.classList.add('shape',o.shape||'rect');if(o.useBackgroundFill){e.style.backgroundColor=slideData.background||'#fff';e.style.backgroundImage=slideData.backgroundImage||'none';e.style.backgroundRepeat=slideData.backgroundRepeat||'no-repeat';e.style.backgroundSize=slideData.backgroundSize||'auto';e.style.backgroundPosition=(-pxX(o.x))+'px '+(-pxY(o.y))+'px';}else e.style.background=o.fill||'transparent';e.style.border=(o.lineWidth&&o.lineWidth>0)?(Math.max(.25,o.lineWidth)*rz)+'px solid '+(o.line||'#333'):'none';
  }
  if(!present&&!o.templateObject){e.onclick=ev=>{ev.stopPropagation();selectionController.setId(o.id)};if(o.id!==editingId)e.onpointerdown=selectionController.startDrag;if(o.id===selectionController.getId()){selectionController.addHandles(e);const hint=document.createElement('div');hint.className='edit-hint';hint.textContent=o.type==='text'?'Double-click to edit · drag border to move':o.type==='image'?'Drag inside to move · circles resize · top handle rotates':'Drag inside to move · circles resize · top handle rotates';e.appendChild(hint)}}
  if(o.templateObject){e.classList.add('template-object');e.style.pointerEvents='none';}
  return e;
}
function renderChartObject(e,o,rz){
  e.classList.add('chart');e.style.background='rgba(255,255,255,.96)';e.style.border=Math.max(1,rz)+'px solid rgba(70,76,86,.35)';e.style.padding=(8*rz)+'px';e.style.boxSizing='border-box';e.style.overflow='hidden';
  if(o.title){const title=document.createElement('div');title.className='chart-title';title.textContent=o.title;title.style.fontSize=Math.max(9,15*rz)+'px';title.style.fontWeight='700';title.style.textAlign='center';title.style.height=(24*rz)+'px';e.appendChild(title)}
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 600 300');svg.setAttribute('preserveAspectRatio','none');svg.style.width='100%';svg.style.height=o.title?'calc(100% - '+(24*rz)+'px)':'100%';
  const categories=o.categories||[],series=o.series||[],values=series.flatMap(s=>(s.values||[]).map(Number)).filter(Number.isFinite),max=Math.max(1,...values.map(Math.abs)),left=42,bottom=42,top=15,right=12,plotW=600-left-right,plotH=300-top-bottom;
  const axis=document.createElementNS(svg.namespaceURI,'path');axis.setAttribute('d','M'+left+' '+top+' V'+(top+plotH)+' H'+(left+plotW));axis.setAttribute('fill','none');axis.setAttribute('stroke','currentColor');axis.setAttribute('stroke-width','1.5');svg.appendChild(axis);
  const groupW=plotW/Math.max(1,categories.length),barW=Math.max(4,groupW*.72/Math.max(1,series.length));
  series.forEach((ser,si)=>{(ser.values||[]).forEach((raw,ci)=>{const value=Number(raw)||0,height=Math.max(0,Math.abs(value)/max*plotH),rect=document.createElementNS(svg.namespaceURI,'rect');rect.setAttribute('x',String(left+ci*groupW+groupW*.14+si*barW));rect.setAttribute('y',String(top+plotH-height));rect.setAttribute('width',String(Math.max(2,barW-2)));rect.setAttribute('height',String(height));rect.setAttribute('fill','hsl('+((210+si*67)%360)+' 58% '+(48+si%2*8)+'%)');rect.setAttribute('data-series',ser.name||('Series '+(si+1)));svg.appendChild(rect)})});
  categories.forEach((cat,ci)=>{const text=document.createElementNS(svg.namespaceURI,'text');text.setAttribute('x',String(left+ci*groupW+groupW/2));text.setAttribute('y',String(top+plotH+18));text.setAttribute('text-anchor','middle');text.setAttribute('font-size','12');text.textContent=String(cat);svg.appendChild(text)});
  series.forEach((ser,si)=>{const text=document.createElementNS(svg.namespaceURI,'text');text.setAttribute('x',String(left+si*130));text.setAttribute('y','296');text.setAttribute('font-size','11');text.textContent=String(ser.name||('Series '+(si+1)));svg.appendChild(text)});e.appendChild(svg);
}
function fitTextElement(box,inn){
  const spans=[...inn.querySelectorAll('.text-run')];
  const overflow=()=>inn.scrollHeight>inn.clientHeight+2||inn.scrollWidth>inn.clientWidth+2;
  if(!overflow())return;
  let scale=1,loops=0;
  while(overflow()&&scale>.62&&loops++<22){
    scale-=.025;
    spans.forEach(sp=>{
      const base=parseFloat(sp.dataset.baseSize||sp.style.fontSize)||18;
      if(!sp.dataset.baseSize)sp.dataset.baseSize=base;
      sp.style.fontSize=(base*scale)+'px';
    });
    if(!spans.length){
      const base=parseFloat(inn.dataset.baseSize||getComputedStyle(box).fontSize)||18;
      if(!inn.dataset.baseSize)inn.dataset.baseSize=base;
      box.style.fontSize=(base*scale)+'px';
    }
  }
}
function renderPresenterNotes(){if(presenterNotesController)presenterNotesController.render();}
function slide(){return pres.slides[currentSlide]}function obj(){return selectionController.getSelectedObject()}
function updateInspector(){
  if(inspectorController)inspectorController.update();
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');['Home','Insert','Arrange','View','Present'].forEach(n=>$('tools'+n).classList.add('hidden'));$('tools'+t.dataset.tab[0].toUpperCase()+t.dataset.tab.slice(1)).classList.remove('hidden')});
$('addSlideBtn').onclick=()=>showTemplateDialog('slide');
$('dupSlideBtn').onclick=()=>{const c=JSON.parse(JSON.stringify(slide()));c.id=uid('s');c.objects.forEach(o=>o.id=uid());pres.slides.splice(currentSlide+1,0,c);currentSlide++;markDirty();renderAll()};
$('delSlideBtn').onclick=()=>{if(pres.slides.length<2)return;historyController.action(()=>{pres.slides.splice(currentSlide,1);currentSlide=Math.max(0,currentSlide-1);selectionController.clear({render:false});markDirty();renderAll()})};
$('insertTextBtn').onclick=()=>{slide().objects.push({id:uid(),type:'text',x:1800000,y:1800000,w:4200000,h:700000,text:'Text',font:'Arial',size:24,color:'#222',align:'left',fill:'transparent',z:idSeq});selectionController.setId(slide().objects.at(-1).id,{render:false});markDirty();renderAll()};
$('insertShapeBtn').onclick=()=>{const shape=$('shapeType').value;const dims=shape==='line'?{w:2600000,h:10000}:shape==='ellipse'?{w:1800000,h:1800000}:{w:2200000,h:1200000};slide().objects.push({id:uid(),type:'shape',shape,x:2200000,y:2200000,w:dims.w,h:dims.h,fill:shape==='line'?'transparent':'#f4e2d8',line:'#d64a24',lineWidth:2,z:idSeq});selectionController.setId(slide().objects.at(-1).id,{render:false});markDirty();renderAll()};
$('insertImageBtn').onclick=()=>{$('imageInput').value='';$('imageInput').click()};$('imageInput').onchange=e=>{const f=e.target.files[0];if(!f)return;const rd=new FileReader();rd.onload=()=>{slide().objects.push({id:uid(),type:'image',src:rd.result,ext:(f.name.split('.').pop()||'png').toLowerCase(),x:2400000,y:1600000,w:3600000,h:2100000,cropZoom:1,cropX:50,cropY:50,z:idSeq});selectionController.setId(slide().objects.at(-1).id,{render:false});markDirty();renderAll()};rd.readAsDataURL(f)};
$('deleteObjBtn').onclick=()=>{const selectedId=selectionController.getId();if(!selectedId)return;historyController.action(()=>{slide().objects=slide().objects.filter(o=>o.id!==selectedId);selectionController.clear({render:false});markDirty();renderAll()})};$('frontBtn').onclick=()=>{const o=obj();if(o){o.z=9999;markDirty();renderAll()}};$('backBtn').onclick=()=>{const o=obj();if(o){o.z=0;markDirty();renderAll()}};
function applyText(fn){const o=obj();if(o&&o.type==='text'){fn(o);markDirty();renderSlide();renderPresentations()}}$('fontFamily').onchange=()=>applyText(o=>o.font=$('fontFamily').value);$('fontSize').onchange=()=>applyText(o=>o.size=+$('fontSize').value);$('boldBtn').onclick=()=>applyText(o=>o.bold=!o.bold);$('italicBtn').onclick=()=>applyText(o=>o.italic=!o.italic);$('alignLeft').onclick=()=>applyText(o=>o.align='left');$('alignCenter').onclick=()=>applyText(o=>o.align='center');$('alignRight').onclick=()=>applyText(o=>o.align='right');
function setZoom(value){zoom=Math.max(.35,Math.min(2,value));renderSlide()}
$('zoomRange').oninput=()=>setZoom(+$('zoomRange').value/100);
$('bottomZoomRange').oninput=()=>setZoom(+$('bottomZoomRange').value/100);$('zoomOutBtn').onclick=()=>setZoom(zoom-.1);$('zoomInBtn').onclick=()=>setZoom(zoom+.1);
$('bottomZoomOutBtn').onclick=()=>setZoom(zoom-.1);$('bottomZoomInBtn').onclick=()=>setZoom(zoom+.1);
function fitSlide(){const r=ui.stageWrap.getBoundingClientRect(),vp=slideViewport();setZoom(Math.max(.35,Math.min(2,(r.width-80)/vp.w,(r.height-80)/vp.h)))}
$('fitBtn').onclick=fitSlide;$('bottomFitBtn').onclick=fitSlide;
function relayoutWorkspace(){
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    fitSlide();
    renderSlide();
  }));
}
const presentationWorkspace=document.querySelector('.workspace');
if(!window.InkDeskPresentationsThumbnails){
  throw new Error('Presentations thumbnails controller is unavailable.');
}
thumbnailsController=InkDeskPresentationsThumbnails.create({
  list:ui.list,
  workspace:presentationWorkspace,
  button:$('togglePresentationsBtn'),
  getPresentation:()=>pres,
  getCurrentSlide:()=>currentSlide,
  goToSlide,
  safeFont,
  relayout:relayoutWorkspace,
});
if(!window.InkDeskPresentationsNotes){
  throw new Error('Presentations presenter notes controller is unavailable.');
}
presenterNotesController=InkDeskPresentationsNotes.create({
  app:ui.app,
  textarea:ui.notes,
  count:ui.notesCount,
  button:$('toggleNotesBtn'),
  getPresentation:()=>pres,
  getCurrentSlideData:()=>pres?slide():null,
  markDirty,
  renderThumbnails:renderPresentations,
  relayout:relayoutWorkspace,
});
function setInspectorOpen(open,options={}){
  if(inspectorController)inspectorController.setOpen(open,options);
}
if(!window.InkDeskPresentationsInspector){
  throw new Error('Presentations inspector controller is unavailable.');
}
inspectorController=InkDeskPresentationsInspector.create({
  workspace:presentationWorkspace,
  button:$('toggleInspectorBtn'),
  canvas:ui.canvas,
  getSelectedObject:obj,
  emu:EMU,
  markDirty,
  renderSlide,
  relayout:relayoutWorkspace,
  cloneState:()=>historyController.capture(),
  pushHistory:before=>historyController.push(before),
});
function syncTransitionControl(){const control=$('transitionType');if(!control||!pres)return;const type=(slide().transition&&slide().transition.type)||'none';control.value=['none','fade','slide','zoom'].includes(type)?type:'fade'}
$('transitionType').onchange=()=>{if(!pres)return;const value=$('transitionType').value;historyController.action(()=>{slide().transition={type:value,rawType:value==='slide'?'push':value,duration:500,advanceAfter:null};markDirty()})};
if(!window.InkDeskPresentationsSlideshow){
  throw new Error('Presentations slideshow controller is unavailable.');
}
slideshowController=InkDeskPresentationsSlideshow.create({
  overlay:ui.present,
  slideTarget:ui.presentSlide,
  exitButton:ui.exitPresent,
  fullscreenButton:ui.fullscreenPresent,
  fullscreenLabel:ui.fullscreenPresentLabel,
  counter:ui.presentCounter,
  help:ui.presentHelp,
  startButtons:['presentFromStartTop','presentFromStartBtn'].map($),
  currentButtons:['presentFromCurrentTop','presentFromCurrentBtn','presentViewBtn'].map($),
  getPresentation:()=>pres,
  getCurrentSlide:()=>currentSlide,
  setCurrentSlide:index=>{currentSlide=index;},
  getSlideData:()=>pres&&pres.slides.length?slide():null,
  getTransitionType:()=>((slide().transition&&slide().transition.type)||$('transitionType').value),
  leaveTextEdit,
  clearSelection:()=>selectionController.clear({render:false}),
  slideViewport,
  renderSlide,
  renderAll,
});
async function savePptx(){return fileController.save()}
if(!window.InkDeskPresentationsPptxWriter)throw new Error('Presentations PPTX write adapter is unavailable.');
pptxWriteAdapter=InkDeskPresentationsPptxWriter.create({
  ns:NS,
  getPresentation:()=>pres,
  parseXml,all,first,attr,relationshipPartPath,serializeXml,
});
if(!window.InkDeskPresentationsFileIO)throw new Error('Presentations file controller is unavailable.');
fileController=InkDeskPresentationsFileIO.create({
  ns:NS,
  getPresentation:()=>pres,
  setPresentation:value=>{pres=value},
  getActiveTheme:()=>activeTheme,
  setActiveTheme:value=>{activeTheme=value},
  getTextDefaults:()=>presentationTextDefaults,
  setTextDefaults:value=>{presentationTextDefaults=value},
  getIdSequence:()=>idSeq,
  setIdSequence:value=>{idSeq=value},
  setCurrentSlide:value=>{currentSlide=value},
  resetSelection:()=>selectionController.clear({render:false}),
  resetHistory:()=>historyController.reset(),
  showApp,renderAll,markSaved,setReady,parseXml,relMap,normalizePath,first,all,attr,
  loadTheme,parseDefaultTextStyle,parseSlide,
  orderMatchesSource:()=>pptxWriteAdapter.orderMatchesSource(),
  patchImportedSlide:(zip,slideData)=>pptxWriteAdapter.patchImportedSlide(zip,slideData),
  shapeObjectXml:object=>pptxWriteAdapter.shapeObjectXml(object),
  pictureObjectXml:(object,rid,index)=>pptxWriteAdapter.pictureObjectXml(object,rid,index),
  onOpenedSource:(file,buffer)=>recoveryController?recoveryController.startOpenedFile(file,buffer):Promise.resolve(),
  isRecoveryRestore:()=>Boolean(recoveryController&&recoveryController.isRestoring()),
  markRecoveryClean:()=>{if(recoveryController)recoveryController.markClean()},
});
if(!window.InkDeskPresentationsRecovery)throw new Error('Presentations recovery controller is unavailable.');
recoveryController=InkDeskPresentationsRecovery.create({
  appVersion:'0.20.2.27',
  getPresentation:()=>pres,
  setPresentation:value=>{pres=value},
  getCurrentSlide:()=>currentSlide,
  setCurrentSlide:value=>{currentSlide=value},
  getSelectedId:()=>selectionController.getId(),
  resetSelection:id=>selectionController.reset(id,{render:false}),
  getZoom:()=>zoom,
  setZoom:value=>{zoom=value},
  setActiveTheme:value=>{activeTheme=value},
  resetHistory:()=>historyController.reset(),
  showApp,renderAll,
  markDirtyState:markDirty,
  setReady,
  loadFile:file=>fileController.load(file),
  setSourceBuffer:buffer=>fileController.setSourceBuffer(buffer),
  clearSource:()=>fileController.clearSource(),
});
recoveryController.promptLatest();
ui.save.onclick=savePptx;
// Advanced editor keyboard shortcuts are intentionally disabled in this beta to avoid iPadOS/WebKit conflicts.
})();

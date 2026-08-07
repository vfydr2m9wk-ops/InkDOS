(function(global){
'use strict';

class PresentationPptxWriteAdapter {
  constructor(options){
    this.ns=options.ns;
    this.getPresentation=options.getPresentation;
    this.parseXml=options.parseXml;
    this.all=options.all;
    this.first=options.first;
    this.attr=options.attr;
    this.relationshipPartPath=options.relationshipPartPath;
    this.serializeXml=options.serializeXml;
  }

  esc(value){
    return String(value||'').replace(/[&<>"']/g,char=>({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&apos;'
    }[char]));
  }

  emu(value){return Math.round(value)}

  sourceElementById(doc,id){
    if(!id)return null;
    const cNv=this.all(doc,'cNvPr').find(node=>this.attr(node,'id')===String(id));
    if(!cNv)return null;
    let node=cNv;
    while(node&&node!==doc){
      if(['sp','pic','graphicFrame','cxnSp'].includes(node.localName))return node;
      node=node.parentNode;
    }
    return null;
  }

  presentationFragment(doc,xml){
    const wrapper=this.parseXml(
      '<root xmlns:p="'+this.ns.p+'" xmlns:a="'+this.ns.a+'" xmlns:r="'+this.ns.r+'">'+xml+'</root>'
    );
    return doc.importNode(wrapper.documentElement.firstElementChild,true);
  }

  replaceTextBody(node,text){
    const txBody=this.first(node,'txBody');
    if(!txBody)return false;
    const existing=Array.from(txBody.children||[]).filter(child=>child.localName==='p');
    const template=existing[0]||null;
    existing.forEach(child=>child.remove());
    const lines=String(text==null?'':text).replace(/\r/g,'').split('\n');
    for(const line of (lines.length?lines:[''])){
      let paragraph;
      if(template){
        paragraph=template.cloneNode(true);
        const textNodes=this.all(paragraph,'t');
        if(textNodes.length){
          textNodes[0].textContent=line;
          for(let index=1;index<textNodes.length;index++)textNodes[index].textContent='';
        }else{
          const run=paragraph.ownerDocument.createElementNS(this.ns.a,'a:r');
          const textNode=paragraph.ownerDocument.createElementNS(this.ns.a,'a:t');
          textNode.textContent=line;
          run.appendChild(textNode);
          paragraph.appendChild(run);
        }
      }else{
        paragraph=txBody.ownerDocument.createElementNS(this.ns.a,'a:p');
        const run=txBody.ownerDocument.createElementNS(this.ns.a,'a:r');
        const textNode=txBody.ownerDocument.createElementNS(this.ns.a,'a:t');
        textNode.textContent=line;
        run.appendChild(textNode);
        paragraph.appendChild(run);
      }
      txBody.appendChild(paragraph);
    }
    return true;
  }

  sameRect(a,b){
    if(!a||!b)return false;
    return ['x','y','w','h','rot'].every(key=>Math.abs(Number(a[key]||0)-Number(b[key]||0))<1);
  }

  patchObjectTransform(node,object){
    if(object.sourceGrouped||this.sameRect(object.originalRect,object))return false;
    const transform=this.first(node,'xfrm');
    if(!transform)return false;
    let offset=this.first(transform,'off');
    let extent=this.first(transform,'ext');
    if(!offset){
      offset=transform.ownerDocument.createElementNS(this.ns.a,'a:off');
      transform.insertBefore(offset,transform.firstChild);
    }
    if(!extent){
      extent=transform.ownerDocument.createElementNS(this.ns.a,'a:ext');
      transform.appendChild(extent);
    }
    offset.setAttribute('x',String(Math.round(object.x||0)));
    offset.setAttribute('y',String(Math.round(object.y||0)));
    extent.setAttribute('cx',String(Math.round(object.w||0)));
    extent.setAttribute('cy',String(Math.round(object.h||0)));
    if(object.rot)transform.setAttribute('rot',String(Math.round(object.rot*60000)));
    else transform.removeAttribute('rot');
    return true;
  }

  patchSlideTransition(doc,transition){
    const root=doc.documentElement;
    const old=Array.from(root.children||[]).find(node=>node.localName==='transition');
    if(old)old.remove();
    const type=(transition&&transition.type)||'none';
    if(type==='none')return;
    const element=doc.createElementNS(this.ns.p,'p:transition');
    const raw=(transition&&transition.rawType)||({slide:'push',fade:'fade',zoom:'zoom'}[type]||'fade');
    element.appendChild(doc.createElementNS(this.ns.p,'p:'+raw));
    if(transition&&transition.advanceAfter!=null){
      element.setAttribute('advTm',String(transition.advanceAfter));
    }
    const after=Array.from(root.children||[]).find(node=>['timing','extLst'].includes(node.localName));
    root.insertBefore(element,after||null);
  }

  dataUrlPayload(src){
    const match=String(src||'').match(/^data:([^;,]+)?(;base64)?,(.*)$/s);
    if(!match)return null;
    const mime=match[1]||'image/png';
    const raw=match[2]?atob(match[3]):decodeURIComponent(match[3]);
    const bytes=new Uint8Array(raw.length);
    for(let index=0;index<raw.length;index++)bytes[index]=raw.charCodeAt(index);
    return {mime,bytes};
  }

  maxRelationshipId(doc){
    return Math.max(0,...this.all(doc,'Relationship').map(rel=>{
      const match=this.attr(rel,'Id').match(/^rId(\d+)$/i);
      return match?+match[1]:0;
    }));
  }

  maxMediaIndex(zip){
    return Math.max(0,...Object.keys(zip.files).map(name=>{
      const match=name.match(/^ppt\/media\/image(\d+)\./i);
      return match?+match[1]:0;
    }));
  }

  ensurePresentationContentType(doc,partName,contentType){
    const root=doc.documentElement;
    if(this.all(root,'Override').some(node=>this.attr(node,'PartName')===partName))return;
    const override=doc.createElementNS(root.namespaceURI,'Override');
    override.setAttribute('PartName',partName);
    override.setAttribute('ContentType',contentType);
    root.appendChild(override);
  }

  async appendNewObjectsToSlide(zip,slideDoc,slidePath,slideData){
    const tree=this.first(slideDoc,'spTree');
    if(!tree)return;
    const relPath=this.relationshipPartPath(slidePath);
    const relFile=zip.file(relPath);
    const relDoc=relFile
      ?this.parseXml(await relFile.async('text'))
      :this.parseXml('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>');
    let relNumber=this.maxRelationshipId(relDoc);
    let mediaNumber=this.maxMediaIndex(zip);
    let shapeId=Math.max(1,...this.all(slideDoc,'cNvPr').map(node=>+this.attr(node,'id','0')||0));
    let changedRels=false;
    for(const object of slideData.objects||[]){
      if(object.templateObject||object.syntheticPlaceholder||object.sourceNvId)continue;
      if(object.type==='image'){
        const payload=this.dataUrlPayload(object.src);
        if(!payload)continue;
        const ext=(object.ext||(/jpeg/i.test(payload.mime)?'jpg':/gif/i.test(payload.mime)?'gif':'png')).replace('jpeg','jpg');
        const name='image'+(++mediaNumber)+'.'+ext;
        const rid='rId'+(++relNumber);
        zip.file('ppt/media/'+name,payload.bytes);
        const rel=relDoc.createElementNS(relDoc.documentElement.namespaceURI,'Relationship');
        rel.setAttribute('Id',rid);
        rel.setAttribute('Type','http://schemas.openxmlformats.org/officeDocument/2006/relationships/image');
        rel.setAttribute('Target','../media/'+name);
        relDoc.documentElement.appendChild(rel);
        const fragment=this.presentationFragment(slideDoc,this.pictureObjectXml(object,rid,mediaNumber));
        const nv=this.first(fragment,'cNvPr');
        if(nv)nv.setAttribute('id',String(++shapeId));
        tree.appendChild(fragment);
        changedRels=true;
        object.sourceNvId=String(shapeId);
        object.sourceLayer='slide';
        object.sourcePartPath=slidePath;
        object.originalRect={x:object.x,y:object.y,w:object.w,h:object.h,rot:object.rot||0};
        continue;
      }
      if(['text','shape','table'].includes(object.type)){
        const fragment=this.presentationFragment(slideDoc,this.shapeObjectXml(object));
        const nv=this.first(fragment,'cNvPr');
        if(nv)nv.setAttribute('id',String(++shapeId));
        tree.appendChild(fragment);
        object.sourceNvId=String(shapeId);
        object.sourceLayer='slide';
        object.sourcePartPath=slidePath;
        object.originalText=typeof object.text==='string'?object.text:null;
        object.originalRect={x:object.x,y:object.y,w:object.w,h:object.h,rot:object.rot||0};
      }
    }
    if(changedRels)zip.file(relPath,this.serializeXml(relDoc));
  }

  notesBodyShape(doc){
    return this.all(doc,'sp').find(shape=>{
      const placeholder=this.first(shape,'ph');
      return placeholder&&this.attr(placeholder,'type')==='body';
    })||this.all(doc,'sp').find(shape=>this.first(shape,'txBody'))||null;
  }

  async patchImportedSlide(zip,slideData){
    const path=slideData.sourcePath;
    const file=path&&zip.file(path);
    if(!file)return false;
    const doc=this.parseXml(await file.async('text'));
    let changed=false;
    for(const object of slideData.objects||[]){
      if(object.sourceLayer!=='slide'||!object.sourceNvId)continue;
      const node=this.sourceElementById(doc,object.sourceNvId);
      if(!node)continue;
      if(object.type==='text'&&object.originalText!==null&&String(object.text||'')!==String(object.originalText||'')){
        changed=this.replaceTextBody(node,object.text)||changed;
        object.originalText=object.text;
      }
      if(this.patchObjectTransform(node,object)){
        changed=true;
        object.originalRect={x:object.x,y:object.y,w:object.w,h:object.h,rot:object.rot||0};
      }
    }
    const transitionChanged=JSON.stringify(slideData.transition||null)!==JSON.stringify(slideData.originalTransition||null);
    if(transitionChanged){
      this.patchSlideTransition(doc,slideData.transition);
      slideData.originalTransition=slideData.transition?JSON.parse(JSON.stringify(slideData.transition)):null;
      changed=true;
    }
    const newObjects=(slideData.objects||[]).filter(object=>!object.sourceNvId&&!object.templateObject&&!object.syntheticPlaceholder).length;
    if(newObjects){
      await this.appendNewObjectsToSlide(zip,doc,path,slideData);
      changed=true;
    }
    if(changed)zip.file(path,this.serializeXml(doc));
    if(slideData.notesPath&&String(slideData.notes||'')!==String(slideData.originalNotes||'')){
      const noteFile=zip.file(slideData.notesPath);
      if(noteFile){
        const noteDoc=this.parseXml(await noteFile.async('text'));
        const body=this.notesBodyShape(noteDoc);
        if(body){
          this.replaceTextBody(body,slideData.notes);
          zip.file(slideData.notesPath,this.serializeXml(noteDoc));
          slideData.originalNotes=slideData.notes;
        }
      }
    }
    return changed;
  }

  orderMatchesSource(){
    const presentation=this.getPresentation();
    if(!presentation||!presentation.slides.every(slide=>slide.sourcePresentationRid&&slide.sourcePath))return false;
    const rids=presentation.slides.map(slide=>slide.sourcePresentationRid);
    const original=presentation.originalSlideRids||[];
    return rids.length===original.length&&new Set(rids).size===rids.length&&rids.every((rid,index)=>rid===original[index]);
  }

  shapeObjectXml(object){
    const id=Math.floor(Math.random()*100000)+10;
    const fill=object.fill&&object.fill!=='transparent'
      ?'<a:solidFill><a:srgbClr val="'+object.fill.replace('#','')+'"/></a:solidFill>'
      :'<a:noFill/>';
    const line=object.line
      ?'<a:ln w="'+Math.round((object.lineWidth||1)*9525)+'"><a:solidFill><a:srgbClr val="'+object.line.replace('#','')+'"/></a:solidFill></a:ln>'
      :'<a:ln><a:noFill/></a:ln>';
    let textBody='';
    if(object.type==='text'){
      const paragraphs=String(object.text||'').split('\n').map(lineText=>[
        '<a:p><a:pPr algn="',
        (object.align==='center'?'ctr':object.align==='right'?'r':'l'),
        '"/><a:r><a:rPr lang="en-US" sz="',
        Math.round((object.size||18)*100),
        '" ',
        (object.bold?'b="1" ':''),
        (object.italic?'i="1" ':''),
        '><a:solidFill><a:srgbClr val="',
        (object.color||'#222222').replace('#',''),
        '"/></a:solidFill><a:latin typeface="',
        this.esc(object.font||'Arial'),
        '"/></a:rPr><a:t>',
        this.esc(lineText),
        '</a:t></a:r></a:p>'
      ].join('')).join('');
      textBody='<p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>'+paragraphs+'</p:txBody>';
    }else if(object.type==='table'){
      textBody='<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>'+this.esc(object.cells.map(row=>row.join(' | ')).join('\n'))+'</a:t></a:r></a:p></p:txBody>';
    }
    return [
      '<p:sp><p:nvSpPr><p:cNvPr id="',id,'" name="Shape ',id,
      '"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm rot="',
      Math.round((object.rot||0)*60000),'"><a:off x="',this.emu(object.x),
      '" y="',this.emu(object.y),'"/><a:ext cx="',this.emu(object.w),'" cy="',
      this.emu(object.h),'"/></a:xfrm><a:prstGeom prst="',(object.shape||'rect'),
      '"><a:avLst/></a:prstGeom>',fill,line,'</p:spPr>',textBody,'</p:sp>'
    ].join('');
  }

  pictureObjectXml(object,rid,index){
    return [
      '<p:pic><p:nvPicPr><p:cNvPr id="',(500+index),'" name="Picture ',index,
      '"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>',
      '<p:blipFill><a:blip r:embed="',rid,'"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>',
      '<p:spPr><a:xfrm rot="',Math.round((object.rot||0)*60000),'"><a:off x="',
      this.emu(object.x),'" y="',this.emu(object.y),'"/><a:ext cx="',this.emu(object.w),
      '" cy="',this.emu(object.h),'"/></a:xfrm><a:prstGeom prst="',(object.shape||'rect'),
      '"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
    ].join('');
  }
}

global.InkDeskPresentationsPptxWriter={
  create(options){return new PresentationPptxWriteAdapter(options)},
  PresentationPptxWriteAdapter,
};
})(window);

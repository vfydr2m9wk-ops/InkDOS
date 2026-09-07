'use strict';
const fs=require('fs');
const vm=require('vm');
const path=require('path');
const root=path.resolve(__dirname,'..');
const PDFLib=require(path.join(root,'vendor/pdf-lib/pdf-lib.min.js'));
globalThis.PDFLib=PDFLib;
vm.runInThisContext(fs.readFileSync(path.join(root,'engine/page-tools-engine.js'),'utf8'),{filename:'engine/page-tools-engine.js'});
const Engine=globalThis.InkDOS2PdfP4.PageToolsEngine;
function assert(condition,message){if(!condition)throw new Error(message)}
async function load(bytes){return PDFLib.PDFDocument.load(bytes,{updateMetadata:false})}
(async()=>{
 const sourceDoc=await PDFLib.PDFDocument.create();
 sourceDoc.addPage([200,300]);sourceDoc.addPage([210,310]);sourceDoc.addPage([220,320]);
 const source=new Uint8Array(await sourceDoc.save());
 let result=await Engine.rotatePage(source,2,90),doc=await load(result.bytes);
 assert(doc.getPageCount()===3,'rotate must preserve page count');
 assert(doc.getPage(1).getRotation().angle===90,'rotate must persist 90-degree rotation');
 result=await Engine.movePage(source,3,1);doc=await load(result.bytes);
 assert(doc.getPageCount()===3,'move must preserve page count');
 assert(Math.round(doc.getPage(0).getWidth())===220,'move must reorder the selected page');
 result=await Engine.deletePage(source,2);doc=await load(result.bytes);
 assert(doc.getPageCount()===2,'delete must reduce page count');
 assert(Math.round(doc.getPage(1).getWidth())===220,'delete must preserve remaining page order');
 result=await Engine.extractPages(source,[2]);doc=await load(result.bytes);
 assert(doc.getPageCount()===1,'extract must create a one-page PDF');
 assert(Math.round(doc.getPage(0).getWidth())===210,'extract must copy the requested page');
 const split=await Engine.splitAfter(source,1),left=await load(split.parts[0].bytes),right=await load(split.parts[1].bytes);
 assert(left.getPageCount()===1&&right.getPageCount()===2,'split must create complementary PDFs');
 const extra=await Engine.extractPages(source,[1]);result=await Engine.merge(source,[extra.bytes]);doc=await load(result.bytes);
 assert(doc.getPageCount()===4,'merge must append additional PDF pages');
 assert(Math.round(doc.getPage(3).getWidth())===200,'merge must preserve appended page geometry');
 const single=await PDFLib.PDFDocument.create();single.addPage([100,100]);let threw=false;
 try{await Engine.deletePage(new Uint8Array(await single.save()),1)}catch(_){threw=true}
 assert(threw,'delete must reject removal of the only page');
 threw=false;try{await Engine.splitAfter(source,3)}catch(_){threw=true}
 assert(threw,'split must reject the final-page boundary');
 console.log('PDF P2 page-tools engine smoke test passed.');
})().catch(error=>{console.error(error);process.exit(1)});

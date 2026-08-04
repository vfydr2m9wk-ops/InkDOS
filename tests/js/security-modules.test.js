'use strict';
const assert=require('assert');
global.window=global;
require('../../shared/file-lifecycle.js');
require('../../shared/formula-engine.js');
require('../../shared/office-runtime.js');
let assertions=0;const ok=(value,message)=>{assert.ok(value,message);assertions++};const eq=(a,b,message)=>{assert.strictEqual(a,b,message);assertions++};const throws=(fn,pattern)=>{assert.throws(fn,pattern);assertions++};

// Shared file lifecycle: unverified browser downloads never clear the warning.
{
  const a=InkDeskFileLifecycle.create(),b=InkDeskFileLifecycle.create();
  eq(a.state,'clean');a.markDirty();eq(a.state,'dirty');ok(a.shouldWarnBeforeUnload());eq(b.state,'clean','workspace state leaked');
  a.beginExport();eq(a.state,'export-preparing');ok(a.shouldWarnBeforeUnload());
  a.downloadRequested({fileName:'copy.docx',bytes:123,sha256:'aaa'});eq(a.state,'download-requested-unverified');ok(a.shouldWarnBeforeUnload());
  a.beginExport();a.downloadRequested({fileName:'copy-2.docx',bytes:124,sha256:'bbb'});eq(a.snapshot().lastExport.fileName,'copy-2.docx');ok(a.shouldWarnBeforeUnload());
  a.exportFailed(new Error('blocked'));eq(a.state,'export-failed');ok(a.shouldWarnBeforeUnload());
  throws(()=>a.verifyReopened({fileName:'copy-2.docx',bytes:124,sha256:'wrong'}),/fingerprint/i);ok(a.shouldWarnBeforeUnload());a.verifyReopened({fileName:'copy-2.docx',bytes:124,sha256:'bbb'});eq(a.state,'export-verified');ok(!a.shouldWarnBeforeUnload());
  b.markDirty();ok(b.shouldWarnBeforeUnload());ok(!a.shouldWarnBeforeUnload(),'workspace verification leaked');
}

// Deterministic formula evaluator.
{
  const f=InkDeskFormula.evaluateArithmetic;
  eq(f('0'),0);eq(f('2+3*4'),14);eq(f('(2+3)*4'),20);eq(f('-2^2'),4);eq(f('8/2/2'),2);eq(f('5%2'),1);eq(f('1/0'),'#DIV/0!');
  throws(()=>f('1+'),/Expected|Malformed|Unexpected/i);throws(()=>f('process.exit()'),/Unsupported|token/i);throws(()=>f('1;globalThis.pwned=1'),/Unsupported token/i);throws(()=>f('('.repeat(70)+'1'+')'.repeat(70)),/nesting/i);throws(()=>f('1+'.repeat(1100)+'1'),/tokens|length/i);throws(()=>f('2^'.repeat(80)+'2'),/nesting|step/i);
  eq(global.pwned,undefined,'formula injection executed');
}

function le16(n){const b=Buffer.alloc(2);b.writeUInt16LE(n>>>0);return b}function le32(n){const b=Buffer.alloc(4);b.writeUInt32LE(n>>>0);return b}
function makeZip(entries,opts={}){
  const locals=[],centrals=[];let offset=0;
  entries.forEach((entry,i)=>{
    const name=Buffer.from(entry.name,'utf8'),localName=Buffer.from(entry.localName??entry.name,'utf8'),data=Buffer.from(entry.data??'x'),method=entry.method??0,flags=entry.flags??0,compressed=entry.compressed??data.length,uncompressed=entry.uncompressed??data.length,extra=entry.extra??Buffer.alloc(0);
    const local=Buffer.concat([le32(0x04034b50),le16(20),le16(flags),le16(method),Buffer.alloc(8),le32(compressed),le32(uncompressed),le16(localName.length),le16(extra.length),localName,extra,data.subarray(0,compressed)]);
    locals.push(local);
    const localOffset=entry.localOffsetOverride??offset;
    const central=Buffer.concat([le32(0x02014b50),le16(20),le16(20),le16(flags),le16(method),Buffer.alloc(8),le32(compressed),le32(uncompressed),le16(name.length),le16(extra.length),le16(0),le16(0),le16(0),le32(0),le32(localOffset),name,extra]);
    centrals.push(central);offset+=local.length;
  });
  const body=Buffer.concat(locals),directory=Buffer.concat(centrals),eocd=Buffer.concat([le32(0x06054b50),le16(0),le16(0),le16(entries.length),le16(entries.length),le32(directory.length),le32(body.length),le16(0)]);
  return Buffer.concat([body,directory,eocd]);
}
const validate=(buffer,limits)=>InkDeskRuntime.validateZipPackage(buffer,'test package',limits);
{
  const normal=makeZip([{name:'[Content_Types].xml'},{name:'word/document.xml'}]);eq(validate(normal).entries,2);
  throws(()=>validate(makeZip([{name:'a.xml'},{name:'a.xml'}])),/duplicate/i);
  throws(()=>validate(makeZip([{name:'A.xml'},{name:'a.xml'}])),/case-insensitive/i);
  throws(()=>validate(makeZip([{name:'caf\u00e9.xml',flags:0x800},{name:'cafe\u0301.xml',flags:0x800}])),/Unicode-normalization/i);
  throws(()=>validate(makeZip([{name:'../evil.xml'}])),/unsafe package path/i);
  throws(()=>validate(makeZip([{name:'safe.xml',localName:'other.xml'}])),/inconsistent local and central/i);
  throws(()=>validate(makeZip([{name:'safe.xml',method:12}])),/compression method/i);
  throws(()=>validate(makeZip([{name:'safe.xml',flags:1}])),/encrypted/i);
  throws(()=>validate(makeZip([{name:'nested.zip'}])),/nested archive/i);
  throws(()=>validate(makeZip([{name:'large.xml',compressed:1,uncompressed:3*1024*1024,data:'x'}]),{maxCompressionRatio:10,maxEntryUncompressedBytes:4*1024*1024}),/compression ratio/i);
  throws(()=>validate(makeZip([{name:'one.xml'},{name:'two.xml',localOffsetOverride:0}])),/overlapping|inconsistent local/i);
  throws(()=>validate(makeZip([{name:'zip64.xml',extra:Buffer.from([1,0,0,0])}])),/ZIP64/i);
  throws(()=>validate(makeZip([{name:'1.xml'},{name:'2.xml'}]),{maxEntries:1}),/too many/i);
}

// Download feature detection: unavailable mechanisms fail rather than claim success.
{
  const realDocument=global.document;global.document={createElement(){return{click(){},remove(){}}},body:{appendChild(){}}};
  throws(()=>InkDeskRuntime.requestDownload(new Blob(['x']),'x.docx'),/unavailable|cannot request/i);global.document=realDocument;
}
console.log(JSON.stringify({assertions}));

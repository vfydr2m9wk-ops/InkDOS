(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
const DEFAULT_BUDGETS=Object.freeze({
  maxInputBytes:64*1024*1024,
  maxEntries:4096,
  maxEntryUncompressedBytes:32*1024*1024,
  maxTotalUncompressedBytes:128*1024*1024,
  maxCompressionRatio:250
});
function fail(code,message){const e=new Error(message);e.code=code;throw e}
function abort(signal){if(signal&&signal.aborted)fail('aborted','DOCX operation aborted')}
function u16(v,o){return v.getUint16(o,true)}
function u32(v,o){return v.getUint32(o,true)}
function normalizePath(raw){
  const s=String(raw||'');
  if(!s||/[\x00-\x1f\x7f]/.test(s))fail('unsafe-path','ZIP entry contains an empty/control-character path');
  if(s.includes('\\'))fail('unsafe-path','ZIP entry contains a backslash path');
  if(s.startsWith('/')||/^[A-Za-z]:/.test(s))fail('unsafe-path','ZIP entry uses an absolute path');
  const out=[];
  for(const part of s.split('/')){if(!part||part==='.')continue;if(part==='..')fail('unsafe-path','ZIP entry attempts path traversal');out.push(part)}
  if(!out.length)fail('unsafe-path','ZIP entry path resolves to empty');
  return out.join('/');
}
function resolvePath(base,target){
  const raw=String(target||'');
  if(!raw||/^[A-Za-z][A-Za-z0-9+.-]*:/.test(raw)||raw.startsWith('//'))fail('external-target','External relationship targets are not opened');
  const out=[];for(const part of (String(base||'')+'/'+raw).split('/')){if(!part||part==='.')continue;if(part==='..'){if(!out.length)fail('unsafe-path','Relationship target escapes package root');out.pop()}else out.push(part)}
  return normalizePath(out.join('/'));
}
function decodeName(bytes){try{return new TextDecoder('utf-8',{fatal:true}).decode(bytes)}catch(_){fail('invalid-name','ZIP entry name is not valid UTF-8')}}
function crc32(bytes){let c=0xffffffff;for(let i=0;i<bytes.length;i++){c^=bytes[i];for(let k=0;k<8;k++)c=(c>>>1)^((c&1)?0xedb88320:0)}return (c^0xffffffff)>>>0}
async function inflateRaw(bytes,signal){abort(signal);if(global.pako&&typeof global.pako.inflateRaw==='function'){try{const out=new Uint8Array(global.pako.inflateRaw(bytes));abort(signal);return out}catch(e){fail('deflate-failed','The bundled DOCX decompressor could not inflate this entry.',e)}}if(typeof DecompressionStream!=='function')fail('deflate-unavailable','This browser does not provide a compatible local DOCX decompressor');let ds;try{ds=new DecompressionStream('deflate-raw')}catch(_){fail('deflate-unavailable','This browser cannot create a deflate-raw decompressor')}try{const ab=await new Response(new Blob([bytes]).stream().pipeThrough(ds)).arrayBuffer();abort(signal);return new Uint8Array(ab)}catch(e){fail('deflate-failed','The browser decompressor could not inflate this DOCX entry.',e)}}
function hasZip64Extra(bytes,start,length){let p=start,end=start+length;while(p+4<=end){const id=bytes[p]|bytes[p+1]<<8,n=bytes[p+2]|bytes[p+3]<<8;p+=4;if(p+n>end)fail('invalid-zip','Malformed ZIP extra field');if(id===0x0001)return true;p+=n}return false}
function locateEocd(bytes,view){const min=Math.max(0,bytes.length-65557);for(let i=bytes.length-22;i>=min;i--){if(u32(view,i)===0x06054b50){const comment=u16(view,i+20);if(i+22+comment===bytes.length)return i}}fail('invalid-zip','DOCX ZIP end-of-central-directory not found')}
async function open(buffer,options={}){
  const signal=options.signal||null,b={...DEFAULT_BUDGETS,...(options.budgets||{})};abort(signal);
  const ab=buffer instanceof ArrayBuffer?buffer:buffer&&buffer.buffer instanceof ArrayBuffer?buffer.buffer.slice(buffer.byteOffset||0,(buffer.byteOffset||0)+(buffer.byteLength||buffer.length||0)):null;
  if(!ab)fail('invalid-input','DOCX input must be an ArrayBuffer or typed array');
  if(ab.byteLength<=0||ab.byteLength>b.maxInputBytes)fail('input-budget','DOCX input exceeds the compressed-byte budget');
  const bytes=new Uint8Array(ab),view=new DataView(ab),eocd=locateEocd(bytes,view);
  const disk=u16(view,eocd+4),centralDisk=u16(view,eocd+6),diskCount=u16(view,eocd+8),count=u16(view,eocd+10),centralSize=u32(view,eocd+12),centralOffset=u32(view,eocd+16);
  if(disk||centralDisk||diskCount!==count)fail('multidisk','Multi-disk DOCX is not supported');
  if(count===0xffff||centralSize===0xffffffff||centralOffset===0xffffffff)fail('zip64','ZIP64 DOCX is outside the current scope');
  if(count<1||count>b.maxEntries)fail('entry-budget','DOCX entry count exceeds budget');
  if(centralOffset+centralSize>eocd)fail('invalid-zip','ZIP central directory is out of bounds');
  let p=centralOffset,totalUncompressed=0;const entries=new Map(),ordered=[];
  for(let i=0;i<count;i++){abort(signal);if(p+46>eocd||u32(view,p)!==0x02014b50)fail('invalid-zip','Invalid ZIP central directory entry');
    const flags=u16(view,p+8),method=u16(view,p+10),crc=u32(view,p+16),compSize=u32(view,p+20),size=u32(view,p+24),nameLen=u16(view,p+28),extraLen=u16(view,p+30),commentLen=u16(view,p+32),diskStart=u16(view,p+34),localOffset=u32(view,p+42);
    if(flags&1||flags&0x40)fail('encrypted','Encrypted DOCX entries are not supported');if(diskStart)fail('multidisk','Multi-disk entry is not supported');
    if(compSize===0xffffffff||size===0xffffffff||localOffset===0xffffffff||hasZip64Extra(bytes,p+46+nameLen,extraLen))fail('zip64','ZIP64 entry is outside the current scope');
    if(method!==0&&method!==8)fail('compression','Unsupported ZIP compression method '+method);
    if(p+46+nameLen+extraLen+commentLen>eocd)fail('invalid-zip','ZIP central entry exceeds directory bounds');
    const rawName=decodeName(bytes.slice(p+46,p+46+nameLen)),isDirectory=rawName.endsWith('/');
    if(isDirectory){p+=46+nameLen+extraLen+commentLen;continue}
    const path=normalizePath(rawName);if(entries.has(path))fail('duplicate-path','Duplicate normalized ZIP path: '+path);
    if(size>b.maxEntryUncompressedBytes)fail('entry-budget','ZIP entry exceeds single-entry budget: '+path);
    totalUncompressed+=size;if(totalUncompressed>b.maxTotalUncompressedBytes)fail('expanded-budget','DOCX declared expanded bytes exceed budget');
    if(size>1024&&compSize>0&&size/compSize>b.maxCompressionRatio)fail('compression-ratio','Suspicious compression ratio in '+path);
    if(localOffset+30>centralOffset||u32(view,localOffset)!==0x04034b50)fail('invalid-zip','ZIP local header is invalid for '+path);
    const localNameLen=u16(view,localOffset+26),localExtraLen=u16(view,localOffset+28),dataStart=localOffset+30+localNameLen+localExtraLen;
    if(dataStart+compSize>centralOffset)fail('invalid-zip','ZIP entry data overlaps central directory: '+path);
    const localName=normalizePath(decodeName(bytes.slice(localOffset+30,localOffset+30+localNameLen)));if(localName!==path)fail('invalid-zip','ZIP local/central path mismatch: '+path);
    const rec=Object.freeze({path,method,flags,crc32:crc>>>0,compressedSize:compSize,uncompressedSize:size,localOffset,dataStart});entries.set(path,rec);ordered.push(rec);p+=46+nameLen+extraLen+commentLen;
  }
  if(p!==centralOffset+centralSize)fail('invalid-zip','ZIP central directory size does not match parsed entries');
  const cache=new Map();
  async function read(path,readOptions={}){abort(readOptions.signal||signal);const safe=normalizePath(path),rec=entries.get(safe);if(!rec)fail('missing-entry','DOCX entry not found: '+safe);if(cache.has(safe))return cache.get(safe).slice();const raw=bytes.slice(rec.dataStart,rec.dataStart+rec.compressedSize),out=rec.method===0?raw:await inflateRaw(raw,readOptions.signal||signal);abort(readOptions.signal||signal);if(out.length!==rec.uncompressedSize)fail('size-mismatch','Uncompressed size mismatch for '+safe);if(crc32(out)!==rec.crc32)fail('crc-mismatch','CRC-32 mismatch for '+safe);cache.set(safe,out.slice());return out.slice()}
  if(!entries.has('[Content_Types].xml'))fail('docx-structure','DOCX [Content_Types].xml is missing');
  if(!entries.has('word/document.xml')&&!entries.has('documents/document.xml'))fail('docx-structure','DOCX main document part is missing');
  return Object.freeze({inputBytes:ab.byteLength,totalUncompressedBytes:totalUncompressed,entryCount:entries.size,entries,ordered:Object.freeze(ordered.slice()),read,has:path=>{try{return entries.has(normalizePath(path))}catch(_){return false}},resolvePath,sourceBytes:ab.slice(0),budget:Object.freeze({...b})});
}
NS.PackageReader={open,normalizePath,resolvePath,crc32,DEFAULT_BUDGETS};
})(globalThis);

(function(global){'use strict';
const NS=global.InkDOS2Epub=global.InkDOS2Epub||{};
const DEFAULT_BUDGETS=Object.freeze({
  maxInputBytes:100*1024*1024,
  maxEntries:4096,
  maxEntryUncompressedBytes:32*1024*1024,
  maxTotalUncompressedBytes:256*1024*1024,
  maxCompressionRatio:250
});
function fail(code,message){const e=new Error(message);e.code=code;throw e}
function abort(signal){if(signal&&signal.aborted)fail('aborted','EPUB operation aborted')}
function u16(v,o){return v.getUint16(o,true)} function u32(v,o){return v.getUint32(o,true)}
function u64(v,o){const lo=v.getUint32(o,true),hi=v.getUint32(o+4,true),n=lo+hi*0x100000000;if(!Number.isSafeInteger(n))fail('zip64-range','ZIP64 value exceeds the safe local numeric range');return n}
function normalizePath(raw){
  const s=String(raw||'');
  if(!s||/[\x00-\x1f\x7f]/.test(s))fail('unsafe-path','ZIP entry contains an empty/control-character path');
  if(s.includes('\\'))fail('unsafe-path','ZIP entry contains a backslash path');
  if(s.startsWith('/')||/^[A-Za-z]:/.test(s))fail('unsafe-path','ZIP entry uses an absolute path');
  const out=[]; for(const part of s.split('/')){if(!part||part==='.')continue;if(part==='..')fail('unsafe-path','ZIP entry attempts path traversal');out.push(part)}
  if(!out.length)fail('unsafe-path','ZIP entry path resolves to empty');
  return out.join('/');
}
function decodeName(bytes){try{return new TextDecoder('utf-8',{fatal:true}).decode(bytes)}catch(_){fail('invalid-name','ZIP entry name is not valid UTF-8')}}
function crc32(bytes){let c=0xffffffff;for(let i=0;i<bytes.length;i++){c^=bytes[i];for(let k=0;k<8;k++)c=(c>>>1)^((c&1)?0xedb88320:0)}return (c^0xffffffff)>>>0}
let inflaterLoad=null;
async function ensureBundledInflater(signal){abort(signal);if(global.pako&&typeof global.pako.inflateRaw==='function')return true;if(typeof document==='undefined')return false;if(!inflaterLoad){inflaterLoad=new Promise(resolve=>{const script=document.createElement('script');script.src='vendor/pako_inflate.min.js';script.async=false;script.addEventListener('load',()=>resolve(!!(global.pako&&typeof global.pako.inflateRaw==='function')),{once:true});script.addEventListener('error',()=>resolve(false),{once:true});(document.head||document.documentElement).appendChild(script)})}const ready=await inflaterLoad;abort(signal);return ready}
async function inflateRaw(bytes,signal){abort(signal);if(await ensureBundledInflater(signal)){try{const out=new Uint8Array(global.pako.inflateRaw(bytes));abort(signal);return out}catch(e){fail('deflate-failed','The bundled EPUB decompressor could not inflate this entry.')}}if(typeof DecompressionStream!=='function')fail('deflate-unavailable','This host does not provide a compatible local EPUB decompressor');let ds;try{ds=new DecompressionStream('deflate-raw')}catch(_){fail('deflate-unavailable','This host cannot create a deflate-raw decompressor')}try{const ab=await new Response(new Blob([bytes]).stream().pipeThrough(ds)).arrayBuffer();abort(signal);return new Uint8Array(ab)}catch(e){fail('deflate-failed','The browser decompressor could not inflate this EPUB entry.')}}
function locateEocd(bytes,view){const min=Math.max(0,bytes.length-65557);for(let i=bytes.length-22;i>=min;i--){if(u32(view,i)===0x06054b50){const comment=u16(view,i+20);if(i+22+comment===bytes.length)return i}}fail('invalid-zip','EPUB ZIP end-of-central-directory not found')}
function directoryInfo(bytes,view,eocd){
  let disk=u16(view,eocd+4),centralDisk=u16(view,eocd+6),diskCount=u16(view,eocd+8),count=u16(view,eocd+10),centralSize=u32(view,eocd+12),centralOffset=u32(view,eocd+16);
  const needsZip64=disk===0xffff||centralDisk===0xffff||diskCount===0xffff||count===0xffff||centralSize===0xffffffff||centralOffset===0xffffffff;
  if(!needsZip64)return {disk,centralDisk,diskCount,count,centralSize,centralOffset,zip64:false};
  const locator=eocd-20;if(locator<0||u32(view,locator)!==0x07064b50)fail('invalid-zip','ZIP64 locator is missing');
  const locatorDisk=u32(view,locator+4),recordOffset=u64(view,locator+8),totalDisks=u32(view,locator+16);
  if(locatorDisk!==0||totalDisks!==1)fail('multidisk','Multi-disk ZIP64/EPUB is not supported');
  if(recordOffset<0||recordOffset+56>locator||u32(view,recordOffset)!==0x06064b50)fail('invalid-zip','ZIP64 end-of-central-directory record is invalid');
  const recordSize=u64(view,recordOffset+4);if(recordSize<44||recordOffset+12+recordSize!==locator)fail('invalid-zip','ZIP64 end-of-central-directory size is invalid');
  disk=u32(view,recordOffset+16);centralDisk=u32(view,recordOffset+20);diskCount=u64(view,recordOffset+24);count=u64(view,recordOffset+32);centralSize=u64(view,recordOffset+40);centralOffset=u64(view,recordOffset+48);
  return {disk,centralDisk,diskCount,count,centralSize,centralOffset,zip64:true};
}
function zip64EntryValues(bytes,view,start,length,need){
  let p=start,end=start+length;while(p+4<=end){const id=bytes[p]|bytes[p+1]<<8,n=bytes[p+2]|bytes[p+3]<<8;p+=4;if(p+n>end)fail('invalid-zip','Malformed ZIP extra field');if(id===0x0001){let q=p;const limit=p+n,out={};function take64(key){if(q+8>limit)fail('invalid-zip','Truncated ZIP64 entry extra field');out[key]=u64(view,q);q+=8}if(need.size)take64('size');if(need.compSize)take64('compSize');if(need.localOffset)take64('localOffset');if(need.diskStart){if(q+4>limit)fail('invalid-zip','Truncated ZIP64 disk-start field');out.diskStart=u32(view,q);q+=4}return out}p+=n}
  if(need.size||need.compSize||need.localOffset||need.diskStart)fail('invalid-zip','ZIP64 entry is missing its ZIP64 extra field');return {};
}
async function open(buffer,options={}){
  const signal=options.signal||null,b={...DEFAULT_BUDGETS,...(options.budgets||{})};abort(signal);
  const ab=buffer instanceof ArrayBuffer?buffer:buffer&&buffer.buffer instanceof ArrayBuffer?buffer.buffer.slice(buffer.byteOffset||0,(buffer.byteOffset||0)+(buffer.byteLength||buffer.length||0)):null;
  if(!ab)fail('invalid-input','EPUB input must be an ArrayBuffer or typed array');
  if(ab.byteLength<=0||ab.byteLength>b.maxInputBytes)fail('input-budget','EPUB input exceeds the provisional compressed-byte budget');
  const bytes=new Uint8Array(ab),view=new DataView(ab),eocd=locateEocd(bytes,view),dir=directoryInfo(bytes,view,eocd);
  const {disk,centralDisk,diskCount,count,centralSize,centralOffset}=dir;
  if(disk||centralDisk||diskCount!==count)fail('multidisk','Multi-disk ZIP/EPUB is not supported');
  if(count<1||count>b.maxEntries)fail('entry-budget','EPUB entry count exceeds the provisional budget');
  if(centralOffset+centralSize>eocd||centralOffset<0)fail('invalid-zip','ZIP central directory is out of bounds');
  let p=centralOffset,totalUncompressed=0;const entries=new Map(),ordered=[];
  for(let i=0;i<count;i++){abort(signal);if(p+46>centralOffset+centralSize||u32(view,p)!==0x02014b50)fail('invalid-zip','Invalid ZIP central directory entry');
    const flags=u16(view,p+8),method=u16(view,p+10),crc=u32(view,p+16),rawCompSize=u32(view,p+20),rawSize=u32(view,p+24),nameLen=u16(view,p+28),extraLen=u16(view,p+30),commentLen=u16(view,p+32),rawDiskStart=u16(view,p+34),rawLocalOffset=u32(view,p+42);
    if(flags&1)fail('encrypted','Encrypted/DRM ZIP entries are not supported');if(flags&0x40)fail('encrypted','Strong-encryption ZIP entries are not supported');
    if(method!==0&&method!==8)fail('compression','Unsupported ZIP compression method '+method);
    if(p+46+nameLen+extraLen+commentLen>centralOffset+centralSize)fail('invalid-zip','ZIP central entry exceeds directory bounds');
    const need={size:rawSize===0xffffffff,compSize:rawCompSize===0xffffffff,localOffset:rawLocalOffset===0xffffffff,diskStart:rawDiskStart===0xffff},z=zip64EntryValues(bytes,view,p+46+nameLen,extraLen,need);
    const compSize=need.compSize?z.compSize:rawCompSize,size=need.size?z.size:rawSize,localOffset=need.localOffset?z.localOffset:rawLocalOffset,diskStart=need.diskStart?z.diskStart:rawDiskStart;
    if(diskStart)fail('multidisk','Multi-disk entry is not supported');
    const rawName=decodeName(bytes.slice(p+46,p+46+nameLen)),path=normalizePath(rawName),isDirectory=rawName.endsWith('/');
    if(entries.has(path))fail('duplicate-path','Duplicate normalized ZIP path: '+path);
    if(size>b.maxEntryUncompressedBytes)fail('entry-budget','ZIP entry exceeds single-entry budget: '+path);
    totalUncompressed+=size;if(totalUncompressed>b.maxTotalUncompressedBytes)fail('expanded-budget','EPUB declared expanded bytes exceed provisional budget');
    if(size>1024&&compSize>0&&size/compSize>b.maxCompressionRatio)fail('compression-ratio','Suspicious compression ratio in '+path);
    if(localOffset+30>centralOffset||u32(view,localOffset)!==0x04034b50)fail('invalid-zip','ZIP local header is invalid for '+path);
    const localNameLen=u16(view,localOffset+26),localExtraLen=u16(view,localOffset+28),dataStart=localOffset+30+localNameLen+localExtraLen;
    if(dataStart+compSize>centralOffset)fail('invalid-zip','ZIP entry data overlaps central directory: '+path);
    const localName=normalizePath(decodeName(bytes.slice(localOffset+30,localOffset+30+localNameLen)));if(localName!==path)fail('invalid-zip','ZIP local/central path mismatch: '+path);
    const rec=Object.freeze({path,rawName,method,flags,crc32:crc>>>0,compressedSize:compSize,uncompressedSize:size,localOffset,dataStart,isDirectory});entries.set(path,rec);ordered.push(rec);p+=46+nameLen+extraLen+commentLen;
  }
  if(p!==centralOffset+centralSize)fail('invalid-zip','ZIP central directory size does not match parsed entries');
  const cache=new Map();
  async function read(path,readOptions={}){abort(readOptions.signal||signal);const safe=normalizePath(path),rec=entries.get(safe);if(!rec||rec.isDirectory)fail('missing-entry','EPUB entry not found: '+safe);if(cache.has(safe))return cache.get(safe).slice();const raw=bytes.slice(rec.dataStart,rec.dataStart+rec.compressedSize);let out=rec.method===0?raw:await inflateRaw(raw,readOptions.signal||signal);abort(readOptions.signal||signal);if(out.length!==rec.uncompressedSize)fail('size-mismatch','Uncompressed size mismatch for '+safe);if(crc32(out)!==rec.crc32)fail('crc-mismatch','CRC-32 mismatch for '+safe);cache.set(safe,out.slice());return out.slice()}
  const mimeRec=entries.get('mimetype');if(!mimeRec||mimeRec.method!==0||mimeRec.localOffset!==0)fail('epub-mimetype','EPUB mimetype must be the first stored ZIP entry');const mime=new TextDecoder('utf-8',{fatal:true}).decode(await read('mimetype'));if(mime!=='application/epub+zip')fail('epub-mimetype','Invalid EPUB mimetype payload');
  return Object.freeze({inputBytes:ab.byteLength,totalUncompressedBytes:totalUncompressed,entryCount:entries.size,entries,ordered:Object.freeze(ordered.slice()),read,has:path=>{try{return entries.has(normalizePath(path))}catch(_){return false}},budget:Object.freeze({...b}),sourceBytes:ab.slice(0)});
}
NS.PackageReader={open,normalizePath,crc32,DEFAULT_BUDGETS};
})(globalThis);

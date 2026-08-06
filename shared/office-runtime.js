(function(global){
'use strict';

const DEFAULT_LIMITS={
  maxCompressedBytes:100*1024*1024,
  maxEntries:10000,
  maxUncompressedBytes:400*1024*1024,
  maxEntryUncompressedBytes:128*1024*1024,
  maxCompressionRatio:2000
};

function asBytes(buffer){
  if(buffer instanceof Uint8Array)return buffer;
  if(buffer instanceof ArrayBuffer)return new Uint8Array(buffer);
  if(ArrayBuffer.isView(buffer))return new Uint8Array(buffer.buffer,buffer.byteOffset,buffer.byteLength);
  throw new TypeError('Expected an ArrayBuffer or typed array.');
}
function u16(bytes,offset){return bytes[offset]|(bytes[offset+1]<<8)}
function u32(bytes,offset){return (bytes[offset]|(bytes[offset+1]<<8)|(bytes[offset+2]<<16)|(bytes[offset+3]<<24))>>>0}
function safeLabel(label){return String(label||'Office package').replace(/[\r\n]+/g,' ').trim()||'Office package'}
function validateInputSize(size,label,maxBytes=DEFAULT_LIMITS.maxCompressedBytes){
  const bytes=Number(size)||0;
  if(bytes<=0)throw new Error(safeLabel(label)+' is empty.');
  if(bytes>maxBytes)throw new Error(safeLabel(label)+' is too large for safe in-browser processing ('+Math.ceil(bytes/1024/1024)+' MB).');
  return bytes;
}
function validateZipPackage(buffer,label,customLimits){
  const limits=Object.assign({},DEFAULT_LIMITS,customLimits||{}),bytes=asBytes(buffer),name=safeLabel(label);
  validateInputSize(bytes.byteLength,name,limits.maxCompressedBytes);
  let eocd=-1;
  for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--){if(u32(bytes,i)===0x06054b50){eocd=i;break}}
  if(eocd<0)throw new Error(name+' is not a valid ZIP-based Office package.');
  const entries=u16(bytes,eocd+10),directorySize=u32(bytes,eocd+12),directoryOffset=u32(bytes,eocd+16);
  if(entries===0xffff||directorySize===0xffffffff||directoryOffset===0xffffffff)throw new Error(name+' uses ZIP64, which is outside the safe browser-processing limit.');
  if(entries>limits.maxEntries)throw new Error(name+' contains too many package entries ('+entries+').');
  if(directoryOffset+directorySize>bytes.length)throw new Error(name+' has an invalid central directory.');
  const decoder=new TextDecoder('utf-8'),unsafePath=/(^|\/)\.\.(\/|$)|^[\\/]|^[A-Za-z]:[\\/]/;
  let offset=directoryOffset,totalUncompressed=0;
  for(let index=0;index<entries;index++){
    if(offset+46>bytes.length||u32(bytes,offset)!==0x02014b50)throw new Error(name+' has an invalid central-directory entry.');
    const flags=u16(bytes,offset+8),compressed=u32(bytes,offset+20),uncompressed=u32(bytes,offset+24),nameLength=u16(bytes,offset+28),extraLength=u16(bytes,offset+30),commentLength=u16(bytes,offset+32);
    const end=offset+46+nameLength+extraLength+commentLength;
    if(end>bytes.length)throw new Error(name+' has a truncated central-directory entry.');
    const entryName=decoder.decode(bytes.subarray(offset+46,offset+46+nameLength));
    const localOffset=u32(bytes,offset+42);
    if(flags&1)throw new Error(name+' contains an encrypted entry, which is unsupported.');
    if(!entryName||/[\u0000-\u001f\u007f]/.test(entryName)||unsafePath.test(entryName.replace(/\\/g,'/')))throw new Error(name+' contains an unsafe package path.');
    if(localOffset+30>bytes.length||u32(bytes,localOffset)!==0x04034b50)throw new Error(name+' has an invalid local-file entry.');
    const localNameLength=u16(bytes,localOffset+26),localExtraLength=u16(bytes,localOffset+28),dataOffset=localOffset+30+localNameLength+localExtraLength;
    if(dataOffset>bytes.length||compressed>bytes.length-dataOffset)throw new Error(name+' contains truncated package data.');
    if(uncompressed>limits.maxEntryUncompressedBytes)throw new Error(name+' contains an entry that is too large to process safely.');
    totalUncompressed+=uncompressed;
    if(totalUncompressed>limits.maxUncompressedBytes)throw new Error(name+' expands beyond the safe in-browser memory limit.');
    if(uncompressed>1024*1024&&uncompressed/Math.max(1,compressed)>limits.maxCompressionRatio)throw new Error(name+' contains an entry with an unsafe compression ratio.');
    offset=end;
  }
  if(offset>directoryOffset+directorySize)throw new Error(name+' has inconsistent central-directory sizing.');
  return{entries,compressedBytes:bytes.byteLength,uncompressedBytes:totalUncompressed};
}
function parseXml(text,context){
  const doc=new DOMParser().parseFromString(String(text||''),'application/xml');
  const parserError=doc.querySelector('parsererror');
  if(parserError)throw new Error('Invalid XML in '+safeLabel(context)+'.');
  return doc;
}
function sanitizeFileName(name,fallback='Download'){
  const cleaned=String(name||'').replace(/[\u0000-\u001f<>:"/\\|?*]+/g,' ').replace(/\s+/g,' ').trim().replace(/[. ]+$/,'');
  return cleaned||fallback;
}
function requestDownload(blob,fileName,options){
  if(!(blob instanceof Blob)||blob.size<=0)throw new Error('The generated download is empty.');
  const settings=Object.assign({revokeAfterMs:15000},options||{}),anchor=document.createElement('a'),url=URL.createObjectURL(blob);
  anchor.href=url;anchor.download=sanitizeFileName(fileName);anchor.rel='noopener';anchor.hidden=true;document.body.appendChild(anchor);
  try{anchor.click()}finally{anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),Math.max(1000,settings.revokeAfterMs))}
  return{fileName:anchor.download,bytes:blob.size};
}
function revokeObjectUrls(values){
  const unique=new Set(values||[]);
  for(const url of unique)if(typeof url==='string'&&url.startsWith('blob:')){try{URL.revokeObjectURL(url)}catch(error){console.warn('Could not revoke object URL',error)}}
}

global.InkDeskRuntime=Object.freeze({DEFAULT_LIMITS,parseXml,requestDownload,revokeObjectUrls,sanitizeFileName,validateInputSize,validateZipPackage});
})(window);

(function(global){
'use strict';

const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{};
const EMU_PER_POINT=12700;
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));

function intrinsic(slide){
  if(!slide)throw new Error('Slide required.');
  return {width:slide.widthEmu/EMU_PER_POINT,height:slide.heightEmu/EMU_PER_POINT};
}

function compute(metrics,slide,view){
  const s=intrinsic(slide),mode=view?.mode||'fit-page';
  let scale;
  if(mode==='manual')scale=clamp(Number(view.manual)||1,.5,2);
  else if(mode==='fit-width')scale=metrics.width/s.width;
  else scale=Math.min(metrics.width/s.width,metrics.height/s.height);
  return Object.freeze({
    mode,scale,
    width:s.width*scale,
    height:s.height*scale,
    intrinsicWidth:s.width,
    intrinsicHeight:s.height,
    overflowX:s.width*scale>metrics.width,
    overflowY:s.height*scale>metrics.height
  });
}

NS.PresentationPolicy=Object.freeze({
  EMU_PER_POINT,
  intrinsic,
  compute,
  MANUAL_MIN:.5,
  MANUAL_MAX:2
});

/*
 * PPTX security gate.
 *
 * presentation-policy.js is loaded before pptx-open-controller.js. Install a
 * namespace setter here so the controller is wrapped at registration time,
 * without coupling the parser/renderer to the security policy.
 */
const PPTX_LIMITS=Object.freeze({
  maxInputBytes:64*1024*1024,
  maxEntries:4096,
  maxEntryBytes:64*1024*1024,
  maxInflatedBytes:256*1024*1024,
  maxXmlBytes:16*1024*1024,
  maxCompressionRatio:250
});

function pptxFail(code,message){
  const error=new Error(message);
  error.code=code;
  throw error;
}

function asBytes(input){
  if(input instanceof Uint8Array)return input;
  if(input instanceof ArrayBuffer)return new Uint8Array(input);
  if(input?.buffer instanceof ArrayBuffer){
    return new Uint8Array(input.buffer,input.byteOffset||0,input.byteLength||input.length||0);
  }
  pptxFail('PPTX_INPUT','PPTX input must be an ArrayBuffer or typed array.');
}

function u16(bytes,offset){return bytes[offset]|(bytes[offset+1]<<8)}
function u32(bytes,offset){
  return (bytes[offset]|bytes[offset+1]<<8|bytes[offset+2]<<16|bytes[offset+3]<<24)>>>0;
}

function findEocd(bytes){
  const min=Math.max(0,bytes.length-65557);
  for(let i=bytes.length-22;i>=min;i--){
    if(u32(bytes,i)!==0x06054b50)continue;
    const comment=u16(bytes,i+20);
    if(i+22+comment===bytes.length)return i;
  }
  pptxFail('PPTX_ZIP_EOCD','PPTX ZIP end-of-central-directory is missing.');
}

function decodeZipName(bytes){
  try{return new TextDecoder('utf-8',{fatal:true}).decode(bytes)}
  catch(_){pptxFail('PPTX_ZIP_NAME','PPTX ZIP entry name is not valid UTF-8.')}
}

function safeZipPath(raw){
  const value=String(raw||'');
  if(!value||/[\x00-\x1f\x7f]/.test(value)||value.includes('\\')||
     value.startsWith('/')||/^[A-Za-z]:/.test(value)){
    pptxFail('PPTX_ZIP_PATH',`Unsafe PPTX package path: ${value}`);
  }
  const core=value.endsWith('/')?value.slice(0,-1):value;
  if(!core)pptxFail('PPTX_ZIP_PATH','PPTX package path resolves to empty.');
  const parts=core.split('/');
  if(parts.some(part=>!part||part==='.'||part==='..')){
    pptxFail('PPTX_ZIP_PATH',`Unsafe PPTX package path: ${value}`);
  }
  return core;
}

function hasZip64Extra(bytes,start,length){
  let cursor=start,end=start+length;
  while(cursor+4<=end){
    const id=u16(bytes,cursor),size=u16(bytes,cursor+2);
    cursor+=4;
    if(cursor+size>end)pptxFail('PPTX_ZIP_EXTRA','Malformed PPTX ZIP extra field.');
    if(id===0x0001)return true;
    cursor+=size;
  }
  return false;
}

function inspectPptxZip(input){
  const bytes=asBytes(input);
  if(bytes.byteLength<=0||bytes.byteLength>PPTX_LIMITS.maxInputBytes){
    pptxFail('PPTX_INPUT_BUDGET','PPTX exceeds the compressed input-byte budget.');
  }
  const eocd=findEocd(bytes);
  const disk=u16(bytes,eocd+4),centralDisk=u16(bytes,eocd+6);
  const diskCount=u16(bytes,eocd+8),count=u16(bytes,eocd+10);
  const centralSize=u32(bytes,eocd+12),centralOffset=u32(bytes,eocd+16);
  if(disk||centralDisk||diskCount!==count)pptxFail('PPTX_MULTIDISK','Multi-disk PPTX is not supported.');
  if(count===0xffff||centralSize===0xffffffff||centralOffset===0xffffffff){
    pptxFail('PPTX_ZIP64','ZIP64 PPTX is outside the supported security envelope.');
  }
  if(count<1||count>PPTX_LIMITS.maxEntries){
    pptxFail('PPTX_ENTRY_BUDGET','PPTX ZIP entry count exceeds the safety budget.');
  }
  if(centralOffset+centralSize>eocd){
    pptxFail('PPTX_ZIP_CENTRAL','PPTX ZIP central directory is out of bounds.');
  }

  let cursor=centralOffset,total=0;
  const folded=new Set(),records=[];
  for(let index=0;index<count;index++){
    if(cursor+46>eocd||u32(bytes,cursor)!==0x02014b50){
      pptxFail('PPTX_ZIP_CENTRAL','Malformed PPTX ZIP central-directory entry.');
    }
    const flags=u16(bytes,cursor+8),method=u16(bytes,cursor+10);
    const compressed=u32(bytes,cursor+20),uncompressed=u32(bytes,cursor+24);
    const nameLen=u16(bytes,cursor+28),extraLen=u16(bytes,cursor+30),commentLen=u16(bytes,cursor+32);
    const diskStart=u16(bytes,cursor+34),localOffset=u32(bytes,cursor+42);
    if(cursor+46+nameLen+extraLen+commentLen>eocd){
      pptxFail('PPTX_ZIP_CENTRAL','Truncated PPTX ZIP central-directory entry.');
    }
    if(flags&1||flags&0x40)pptxFail('PPTX_ENCRYPTED','Encrypted PPTX entries are not supported.');
    if(diskStart)pptxFail('PPTX_MULTIDISK','Multi-disk PPTX entries are not supported.');
    if(method!==0&&method!==8)pptxFail('PPTX_COMPRESSION',`Unsupported PPTX ZIP compression method ${method}.`);
    if(compressed===0xffffffff||uncompressed===0xffffffff||localOffset===0xffffffff||
       hasZip64Extra(bytes,cursor+46+nameLen,extraLen)){
      pptxFail('PPTX_ZIP64','ZIP64 PPTX entries are outside the supported security envelope.');
    }

    const rawName=decodeZipName(bytes.subarray(cursor+46,cursor+46+nameLen));
    const directory=rawName.endsWith('/');
    const path=safeZipPath(rawName);
    const key=path.toLowerCase();
    if(folded.has(key))pptxFail('PPTX_ZIP_COLLISION',`Duplicate/case-colliding PPTX path: ${path}`);
    folded.add(key);

    if(uncompressed>PPTX_LIMITS.maxEntryBytes){
      pptxFail('PPTX_ENTRY_BUDGET',`PPTX entry exceeds the single-entry budget: ${path}`);
    }
    total+=uncompressed;
    if(total>PPTX_LIMITS.maxInflatedBytes){
      pptxFail('PPTX_EXPANDED_BUDGET','PPTX declared expanded bytes exceed the safety budget.');
    }
    if(uncompressed>1024&&compressed>0&&uncompressed/compressed>PPTX_LIMITS.maxCompressionRatio){
      pptxFail('PPTX_COMPRESSION_RATIO',`Suspicious PPTX compression ratio: ${path}`);
    }
    if(localOffset+30>centralOffset||u32(bytes,localOffset)!==0x04034b50){
      pptxFail('PPTX_ZIP_LOCAL',`Invalid PPTX ZIP local header: ${path}`);
    }
    const localNameLen=u16(bytes,localOffset+26),localExtraLen=u16(bytes,localOffset+28);
    const dataStart=localOffset+30+localNameLen+localExtraLen;
    if(dataStart+compressed>centralOffset){
      pptxFail('PPTX_ZIP_LOCAL',`PPTX entry overlaps the central directory: ${path}`);
    }
    const localName=safeZipPath(decodeZipName(bytes.subarray(localOffset+30,localOffset+30+localNameLen)));
    if(localName!==path)pptxFail('PPTX_ZIP_LOCAL',`PPTX local/central path mismatch: ${path}`);

    records.push(Object.freeze({path,directory,compressed,uncompressed,method}));
    cursor+=46+nameLen+extraLen+commentLen;
  }
  if(cursor!==centralOffset+centralSize){
    pptxFail('PPTX_ZIP_CENTRAL','PPTX central-directory size does not match parsed entries.');
  }
  return Object.freeze({bytes,records:Object.freeze(records),totalInflated:total});
}

async function validatePptx(input){
  const inspected=inspectPptxZip(input);
  if(!global.JSZip)pptxFail('PPTX_JSZIP','Private PPTX ZIP engine is unavailable.');
  const zip=await global.JSZip.loadAsync(inspected.bytes,{checkCRC32:true,createFolders:false});
  for(const record of inspected.records){
    if(record.directory||!/(?:\.xml|\.rels)$/i.test(record.path))continue;
    if(record.uncompressed>PPTX_LIMITS.maxXmlBytes){
      pptxFail('PPTX_XML_BUDGET',`PPTX XML part exceeds the XML safety budget: ${record.path}`);
    }
    const part=zip.file(record.path);
    if(!part)pptxFail('PPTX_ZIP_PART',`PPTX part is missing after ZIP verification: ${record.path}`);
    const text=await part.async('text');
    if(/<!DOCTYPE\b|<!ENTITY\b/i.test(text)){
      pptxFail('PPTX_XML_DTD',`DTD/entity declarations are forbidden in PPTX XML: ${record.path}`);
    }
  }
  return inspected;
}

function secureController(original){
  async function decodePptx(bytes,fileName){
    await validatePptx(bytes);
    return original.decodePptx(bytes,fileName);
  }
  async function decode(bytes,fileName){
    if(/\.ppt$/i.test(String(fileName||'')))return original.decode(bytes,fileName);
    return decodePptx(bytes,fileName);
  }
  function create(options={}){
    const inner=original.create(options);
    async function openFile(file){
      if(!file)return false;
      if(/\.ppt$/i.test(String(file.name||'')))return inner.openFile(file);
      try{
        if(Number(file.size)>PPTX_LIMITS.maxInputBytes){
          pptxFail('PPTX_INPUT_BUDGET','PPTX exceeds the compressed input-byte budget.');
        }
        const bytes=new Uint8Array(await file.arrayBuffer());
        await validatePptx(bytes);
      }catch(error){
        options.chrome?.showError(error,file);
        if(options.fileInput)options.fileInput.value='';
        return false;
      }
      return inner.openFile(file);
    }
    function install(){
      options.fileInput?.addEventListener('change',()=>{
        const file=options.fileInput.files?.[0];
        if(file)openFile(file);
      });
    }
    return Object.freeze({...inner,install,openFile,decode,decodePptx});
  }
  return Object.freeze({create,decode,decodePptx});
}

let pptxController;
Object.defineProperty(NS,'PptxOpenController',{
  configurable:true,
  enumerable:true,
  get(){return pptxController},
  set(value){
    if(!value||typeof value.create!=='function'||typeof value.decodePptx!=='function'){
      pptxFail('PPTX_CONTROLLER','Invalid PPTX open controller registration.');
    }
    pptxController=secureController(value);
    Object.defineProperty(NS,'PptxOpenController',{
      configurable:false,
      enumerable:true,
      writable:false,
      value:pptxController
    });
  }
});

NS.PptxSecurity=Object.freeze({
  LIMITS:PPTX_LIMITS,
  inspectPptxZip,
  validatePptx
});

})(globalThis);

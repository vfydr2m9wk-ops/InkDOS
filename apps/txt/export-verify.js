(function(g){'use strict';const NS=g.InkDOS2=g.InkDOS2||{};
function verify(bytes,snapshot){const b=bytes instanceof Uint8Array?bytes:new Uint8Array(bytes);const enc=snapshot.encoding||'utf-8',bom=!!snapshot.bom,le=snapshot.lineEnding||'\n';let body=b;
if(enc==='utf-8'&&bom){assertPrefix(b,[0xef,0xbb,0xbf]);body=b.subarray(3)}
else if(enc==='utf-16le'&&bom){assertPrefix(b,[0xff,0xfe]);body=b.subarray(2)}
else if(enc==='utf-16be'&&bom){assertPrefix(b,[0xfe,0xff]);body=b.subarray(2)}
if((enc==='utf-16le'||enc==='utf-16be')&&body.length%2)throw new Error('Export verification failed: odd UTF-16 byte length.');
let decoded;try{decoded=new TextDecoder(enc,{fatal:true}).decode(body)}catch(e){throw new Error('Export verification failed: invalid '+enc+' bytes.',{cause:e})}
const expected=String(snapshot.text).replace(/\n/g,le);if(decoded!==expected)throw new Error('Export verification failed: bytes do not match immutable text snapshot.');return Object.freeze({encoding:enc,bom,lineEnding:le,byteLength:b.byteLength,textLength:decoded.length})}
function assertPrefix(bytes,prefix){if(bytes.length<prefix.length||prefix.some((v,i)=>bytes[i]!==v))throw new Error('Export verification failed: expected BOM missing.');}
NS.TxtExportVerify={verify};})(globalThis);

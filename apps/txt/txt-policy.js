(function(g){'use strict';
const NS=g.InkDOS2=g.InkDOS2||{};
function apply(editor,{wrap,fontSize}){editor.classList.toggle('no-wrap',!wrap);editor.style.setProperty('--text-size',fontSize+'px');return {wrap,fontSize}}
function isXmlName(name){return /\.xml$/i.test(String(name||''))}
function declaredXmlEncoding(text){const m=String(text).match(/^\s*<\?xml\b[^?]*\bencoding\s*=\s*(["'])([^"']+)\1[^?]*\?>/i);return m?m[2]:null}
function xmlEncodingCompatible(declared,encoding){if(!declared)return true;const d=String(declared).toLowerCase().replace(/_/g,'-'),s=String(encoding||'utf-8').toLowerCase();if(d==='utf-8')return s==='utf-8';if(d==='utf-16')return s==='utf-16le'||s==='utf-16be';if(d==='utf-16le')return s==='utf-16le';if(d==='utf-16be')return s==='utf-16be';return false}
function xmlEncodingLabel(encoding){const s=String(encoding||'utf-8').toLowerCase();return s==='utf-16le'?'UTF-16LE':s==='utf-16be'?'UTF-16BE':'UTF-8'}
function assertXmlStorage({fileName,text,encoding,bom}={}){if(!isXmlName(fileName))return true;const declared=declaredXmlEncoding(text);if(declared&&!xmlEncodingCompatible(declared,encoding))throw new Error(`XML declaration encoding ${declared} does not match selected save encoding ${String(encoding).toUpperCase()}.`);if(/^utf-16/.test(String(encoding||'').toLowerCase())&&!bom)throw new Error('UTF-16 XML requires BOM in InkDOS for safe round-trip reopening.');return true}
NS.TxtPolicy=Object.freeze({apply,isXmlName,declaredXmlEncoding,xmlEncodingCompatible,xmlEncodingLabel,assertXmlStorage});
})(globalThis);

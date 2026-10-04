(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
let readerUrl=null;
function makeUrl(bytes,fallback){if(bytes&&bytes.byteLength)return URL.createObjectURL(new Blob([bytes],{type:'text/javascript'}));return fallback}
function configure(){if(!global.pdfjsLib)throw new Error('PDFJS_NOT_LOADED');if(!readerUrl)readerUrl=makeUrl(global.__INKDOS_PDF_READER_WORKER_BYTES__,'./vendor/pdfjs/pdf.worker.min.mjs');pdfjsLib.GlobalWorkerOptions.workerSrc=readerUrl;return readerUrl}
// decoders for JPEG 2000 / JBIG2 images and ICC colors (WebAssembly with JS fallbacks), fetched from this origin
function wasmUrl(){return new URL('./vendor/pdfjs/wasm/',global.location.href).href}
function dispose(){if(readerUrl?.startsWith('blob:'))URL.revokeObjectURL(readerUrl);readerUrl=null}
NS.PdfWorker=Object.freeze({configure,dispose,wasmUrl});
})(globalThis);

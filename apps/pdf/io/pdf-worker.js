(function(global){'use strict';
const NS=global.InkDOS2PdfP4=global.InkDOS2PdfP4||{};
let readerUrl=null;
function makeUrl(bytes,fallback){if(bytes&&bytes.byteLength)return URL.createObjectURL(new Blob([bytes],{type:'text/javascript'}));return fallback}
function configure(){if(!global.pdfjsLib)throw new Error('PDFJS_NOT_LOADED');if(!readerUrl)readerUrl=makeUrl(global.__INKDOS_PDF_READER_WORKER_BYTES__,'./vendor/pdfjs/pdf.worker.min.js');pdfjsLib.GlobalWorkerOptions.workerSrc=readerUrl;return readerUrl}
function dispose(){if(readerUrl?.startsWith('blob:'))URL.revokeObjectURL(readerUrl);readerUrl=null}
NS.PdfWorker=Object.freeze({configure,dispose});
})(globalThis);

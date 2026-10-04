// PDF.js ships only as an ES module: publish it as the pdfjsLib global used by the workspace scripts,
// which load with `defer` after this module and therefore run after it, in document order.
import * as pdfjsLib from '../vendor/pdfjs/pdf.min.mjs';
globalThis.pdfjsLib = pdfjsLib;

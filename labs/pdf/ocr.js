/* InkDOS PDF Lab (beta): OCR that makes scanned PDFs searchable, entirely in the browser.
 *
 * Pages without a text layer are rendered with pdf.js and recognised by Tesseract (LSTM, int8
 * "best" models for Portuguese and English) in a small pool of workers; each recognised word is
 * written back as invisible text (render mode 3) scaled to its box, so the page looks unchanged
 * but can be searched, selected and copied. Pages that already carry text are left as they are.
 */
(function (global) {
  'use strict';

  const BASE = new URL('.', document.currentScript ? document.currentScript.src : location.href).href;
  // wasm SIMD probe (same bytes as wasm-feature-detect): pick the SIMD core when the browser has it
  const SIMD = new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0, 1, 5, 1, 96, 0, 1, 123, 3, 2, 1, 0, 10, 10, 1, 8, 0, 65, 0, 253, 15, 253, 98, 11]);
  const corePath = () => BASE + 'vendor/tesseract/core/' + (WebAssembly.validate(SIMD) ? 'tesseract-core-simd-lstm.wasm.js' : 'tesseract-core-lstm.wasm.js');

  async function pageHasText(page) {
    const tc = await page.getTextContent();
    return tc.items.reduce((n, it) => n + String(it.str || '').trim().length, 0) >= 20;
  }

  // renders a page at about 300 dpi, capped so large pages stay fast
  async function renderPage(page) {
    const base = page.getViewport({ scale: 1 }), scale = Math.min(300 / 72, 2600 / Math.max(base.width, base.height));
    const viewport = page.getViewport({ scale }), canvas = document.createElement('canvas');
    canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height);
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    await page.render({ canvasContext: ctx, viewport }).promise;
    return { canvas, viewport };
  }

  function words(data) {
    const out = [];
    for (const b of data.blocks || []) for (const p of b.paragraphs || []) for (const l of p.lines || []) for (const w of l.words || []) {
      const t = String(w.text || '').trim();
      if (t && w.confidence > 30) out.push({ text: t, bbox: w.bbox, baseline: l.baseline });
    }
    return out;
  }

  async function ocrPdf(bytes, options) {
    const o = Object.assign({ languages: 'por+eng', allPages: false, onProgress: () => {} }, options);
    const pdfjs = global.pdfjsLib, Tesseract = global.Tesseract, PDFLib = global.PDFLib;
    const src = await pdfjs.getDocument({ data: bytes.slice() }).promise;
    const total = src.numPages, todo = [];
    for (let i = 1; i <= total; i++) {
      const page = await src.getPage(i);
      if (o.allPages || !(await pageHasText(page))) todo.push(i);
    }
    if (!todo.length) { await src.destroy(); return { bytes, pages: 0, words: 0, skipped: total }; }

    const workers = Math.max(1, Math.min(4, (navigator.hardwareConcurrency || 2) - 1, todo.length));
    const scheduler = Tesseract.createScheduler(), core = corePath();
    o.onProgress({ phase: 'load', done: 0, total: todo.length });
    for (let i = 0; i < workers; i++) {
      scheduler.addWorker(await Tesseract.createWorker(o.languages, 1, {
        workerPath: BASE + 'vendor/tesseract/worker.min.js', corePath: core, langPath: BASE + 'vendor/tesseract/lang',
        workerBlobURL: false, gzip: true, cacheMethod: 'none'
      }));
    }

    const results = new Map();
    let done = 0;
    try {
      // render ahead of the workers, never holding more canvases than there are workers
      const queue = [];
      for (const n of todo) {
        const page = await src.getPage(n), { canvas, viewport } = await renderPage(page);
        const job = scheduler.addJob('recognize', canvas, {}, { blocks: true, text: false }).then(r => {
          results.set(n, { words: words(r.data), viewport });
          canvas.width = canvas.height = 0;
          o.onProgress({ phase: 'recognize', done: ++done, total: todo.length });
        });
        queue.push(job);
        if (queue.length >= workers) await queue.shift();
      }
      await Promise.all(queue);
    } finally {
      await scheduler.terminate();
      await src.destroy();
    }

    // invisible text layer
    o.onProgress({ phase: 'write', done, total: todo.length });
    const doc = await PDFLib.PDFDocument.load(bytes, { updateMetadata: false });
    const font = await doc.embedFont(PDFLib.StandardFonts.Helvetica);
    const encodable = s => [...s].map(ch => { try { font.encodeText(ch); return ch; } catch (_) { return '?'; } }).join('');
    let count = 0;
    for (const [n, r] of results) {
      if (!r.words.length) continue;
      const page = doc.getPage(n - 1), key = page.node.newFontDictionary('InkOCR', font.ref);
      const ops = [PDFLib.pushGraphicsState(), PDFLib.beginText(), PDFLib.setTextRenderingMode(PDFLib.TextRenderingMode.Invisible)];
      for (const w of r.words) {
        const [x0, yTop] = r.viewport.convertToPdfPoint(w.bbox.x0, w.bbox.y0), [x1, yBottom] = r.viewport.convertToPdfPoint(w.bbox.x1, w.bbox.y1);
        const left = Math.min(x0, x1), bottom = Math.min(yTop, yBottom), width = Math.abs(x1 - x0), height = Math.abs(yTop - yBottom);
        if (width < 1 || height < 1) continue;
        const text = encodable(w.text), size = height * 0.9, natural = font.widthOfTextAtSize(text, size) || 1;
        ops.push(PDFLib.setFontAndSize(key, size), PDFLib.setCharacterSqueeze(Math.max(10, Math.min(1000, (width / natural) * 100))),
          PDFLib.setTextMatrix(1, 0, 0, 1, left, bottom + height * 0.18), PDFLib.showText(font.encodeText(text + ' ')));
        count++;
      }
      ops.push(PDFLib.endText(), PDFLib.popGraphicsState());
      page.pushOperators(...ops);
    }
    const out = await doc.save();
    return { bytes: out, pages: results.size, words: count, skipped: total - todo.length };
  }

  global.InkDOSPdfLabOcr = Object.freeze({ ocrPdf });
})(globalThis);

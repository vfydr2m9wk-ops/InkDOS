/* InkDOS PDF: OCR that makes scanned pages searchable, entirely in the browser (web edition).
 *
 * Pages without a text layer are rendered at about 300 dpi and recognised by Tesseract (LSTM,
 * Portuguese + English "best_int" models) in a small worker pool. Each page is read as rendered;
 * when Tesseract's mean confidence is low it is read again after a 3x3 median denoise and an Otsu
 * threshold, and the reading with the higher confidence is kept: cleaning rescues noisy or faint
 * scans, while the plain reading stays best for clean and low-resolution pages, whose thin strokes
 * the filter would erase. Recognised words are written back as invisible text (render mode 3)
 * scaled to their boxes, so pages look unchanged but can be searched, selected and copied.
 * Pages that already carry text are left untouched.
 */
(function (global) {
  'use strict';
  const NS = global.InkDOS2PdfP4 = global.InkDOS2PdfP4 || {};
  const BASE = new URL('../../vendor/tesseract/', document.currentScript ? document.currentScript.src : global.location.href).href;
  const PDFJS_WASM = new URL('../../vendor/pdfjs/wasm/', document.currentScript ? document.currentScript.src : global.location.href).href;
  // wasm SIMD probe (same bytes as wasm-feature-detect): pick the SIMD core when the browser has it
  const SIMD = new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0, 1, 5, 1, 96, 0, 1, 123, 3, 2, 1, 0, 10, 10, 1, 8, 0, 65, 0, 253, 15, 253, 98, 11]);
  const LOW_CONFIDENCE = 70;

  const corePath = () => BASE + 'core/' + (WebAssembly.validate(SIMD) ? 'tesseract-core-simd-lstm.wasm.js' : 'tesseract-core-lstm.wasm.js');

  function loadTesseract() {
    if (global.Tesseract) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = BASE + 'tesseract.min.js';
      s.onload = () => global.Tesseract ? resolve() : reject(new Error('The OCR engine did not load.'));
      s.onerror = () => reject(new Error('The OCR engine could not be loaded.'));
      document.head.appendChild(s);
    });
  }

  async function pageHasText(page) {
    const tc = await page.getTextContent();
    return tc.items.reduce((n, it) => n + String(it.str || '').trim().length, 0) >= 20;
  }

  // about 300 dpi, capped so large pages stay fast
  async function renderPage(page) {
    const base = page.getViewport({ scale: 1 }), scale = Math.min(300 / 72, 2600 / Math.max(base.width, base.height));
    const viewport = page.getViewport({ scale }), canvas = document.createElement('canvas');
    canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height);
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    await page.render({ canvasContext: ctx, viewport }).promise;
    return { canvas, viewport };
  }

  // at half the 300 dpi rendering (grain of upscaled low-resolution scans shrinks back to pixel size):
  // grayscale, 3x3 median (removes speckle), Otsu threshold (separates ink from background)
  function cleaned(source) {
    const W = Math.max(1, Math.round(source.width / 2)), H = Math.max(1, Math.round(source.height / 2)), out = document.createElement('canvas');
    out.width = W; out.height = H;
    const ctx = out.getContext('2d', { willReadFrequently: true });
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(source, 0, 0, W, H);
    const image = ctx.getImageData(0, 0, W, H), px = image.data, gray = new Uint8Array(W * H), med = new Uint8Array(W * H), hist = new Uint32Array(256);
    for (let i = 0; i < W * H; i++) gray[i] = (px[i * 4] * 299 + px[i * 4 + 1] * 587 + px[i * 4 + 2] * 114) / 1000 | 0;
    const win = new Uint8Array(9);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        let n = 0;
        for (let dy = -1; dy <= 1; dy++) {
          const row = Math.min(H - 1, Math.max(0, y + dy)) * W;
          for (let dx = -1; dx <= 1; dx++) win[n++] = gray[row + Math.min(W - 1, Math.max(0, x + dx))];
        }
        win.sort();
        med[y * W + x] = win[4]; hist[win[4]]++;
      }
    }
    let sum = 0;
    for (let t = 0; t < 256; t++) sum += t * hist[t];
    let sumB = 0, wB = 0, best = 0, threshold = 128;
    for (let t = 0; t < 256; t++) {
      wB += hist[t]; if (!wB) continue;
      const wF = W * H - wB; if (!wF) break;
      sumB += t * hist[t];
      const between = wB * wF * (sumB / wB - (sum - sumB) / wF) ** 2;
      if (between > best) { best = between; threshold = t; }
    }
    for (let i = 0; i < W * H; i++) { const v = med[i] <= threshold ? 0 : 255; px[i * 4] = px[i * 4 + 1] = px[i * 4 + 2] = v; px[i * 4 + 3] = 255; }
    ctx.putImageData(image, 0, 0);
    return out;
  }

  // word boxes in the coordinates of the 300 dpi rendering (`scale` undoes a reduced cleaned reading)
  function words(data, scale) {
    const out = [];
    for (const b of data.blocks || []) for (const p of b.paragraphs || []) for (const l of p.lines || []) for (const w of l.words || []) {
      const t = String(w.text || '').trim();
      if (t && w.confidence > 30) out.push({ text: t, bbox: { x0: w.bbox.x0 * scale, y0: w.bbox.y0 * scale, x1: w.bbox.x1 * scale, y1: w.bbox.y1 * scale } });
    }
    return out;
  }

  async function recognizePage(scheduler, canvas) {
    const plain = (await scheduler.addJob('recognize', canvas, {}, { blocks: true, text: false })).data;
    if (plain.confidence >= LOW_CONFIDENCE) return { data: plain, cleaned: false, scale: 1 };
    const reduced = cleaned(canvas), scale = canvas.width / reduced.width;
    const clean = (await scheduler.addJob('recognize', reduced, {}, { blocks: true, text: false })).data;
    reduced.width = reduced.height = 0;
    return clean.confidence > plain.confidence ? { data: clean, cleaned: true, scale } : { data: plain, cleaned: false, scale: 1 };
  }

  async function pagesNeedingText(bytes) {
    const src = await global.pdfjsLib.getDocument({ data: bytes.slice(), isEvalSupported: false, enableScripting: false, wasmUrl: PDFJS_WASM }).promise;
    try {
      const todo = [];
      for (let i = 1; i <= src.numPages; i++) if (!(await pageHasText(await src.getPage(i)))) todo.push(i);
      return { total: src.numPages, todo };
    } finally { await src.loadingTask.destroy(); }
  }

  async function run(bytes, options) {
    const o = Object.assign({ languages: 'por+eng', onProgress: () => {} }, options);
    const PDFLib = global.PDFLib;
    const src = await global.pdfjsLib.getDocument({ data: bytes.slice(), isEvalSupported: false, enableScripting: false, wasmUrl: PDFJS_WASM }).promise;
    const total = src.numPages, todo = [];
    for (let i = 1; i <= total; i++) if (!(await pageHasText(await src.getPage(i)))) todo.push(i);
    if (!todo.length) { await src.loadingTask.destroy(); return { bytes, pages: 0, words: 0, cleaned: 0, skipped: total }; }

    o.onProgress({ phase: 'load', done: 0, total: todo.length });
    await loadTesseract();
    const Tesseract = global.Tesseract, workers = Math.max(1, Math.min(4, (navigator.hardwareConcurrency || 2) - 1, todo.length));
    const scheduler = Tesseract.createScheduler(), core = corePath(), results = new Map();
    let done = 0;
    try {
      for (let i = 0; i < workers; i++) {
        const worker = await Tesseract.createWorker(o.languages, 1, {
          workerPath: BASE + 'worker.min.js', corePath: core, langPath: BASE + 'lang', workerBlobURL: false, gzip: true, cacheMethod: 'none'
        });
        // Tesseract's own diagnostics (e.g. tiny noise blobs it skips) are not for the user's console
        await worker.setParameters({ debug_file: '/dev/null' });
        scheduler.addWorker(worker);
      }
      // render ahead of the workers, never holding more canvases than there are workers
      const queue = [];
      for (const n of todo) {
        const page = await src.getPage(n), { canvas, viewport } = await renderPage(page);
        queue.push(recognizePage(scheduler, canvas).then(r => {
          results.set(n, { words: words(r.data, r.scale), viewport, cleaned: r.cleaned });
          canvas.width = canvas.height = 0;
          o.onProgress({ phase: 'recognize', done: ++done, total: todo.length });
        }));
        if (queue.length >= workers) await queue.shift();
      }
      await Promise.all(queue);
    } finally {
      await scheduler.terminate();
      await src.loadingTask.destroy();
    }

    o.onProgress({ phase: 'write', done, total: todo.length });
    const doc = await PDFLib.PDFDocument.load(bytes, { updateMetadata: false });
    const font = await doc.embedFont(PDFLib.StandardFonts.Helvetica);
    const encodable = s => [...s].map(ch => { try { font.encodeText(ch); return ch; } catch (_) { return '?'; } }).join('');
    let count = 0, cleanedPages = 0;
    for (const [n, r] of results) {
      if (r.cleaned) cleanedPages++;
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
    return { bytes: out, pages: results.size, words: count, cleaned: cleanedPages, skipped: total - todo.length, pageCount: doc.getPageCount() };
  }

  // a signature covers the file's bytes: adding a text layer would invalidate it
  function isSigned(bytes) {
    const text = new TextDecoder('latin1').decode(bytes);
    return /\/ByteRange\s*\[/.test(text) && /\/Type\s*\/Sig\b|\/FT\s*\/Sig\b/.test(text);
  }

  NS.PdfOcrEngine = Object.freeze({ run, pagesNeedingText, isSigned, _test: { cleaned } });
})(globalThis);

(function (global) {
  'use strict';

  const VERSION = '0.19.4.12';
  const DEFAULT_DPI = 144;
  const DEFAULT_JPEG_QUALITY = 0.91;
  const DEFAULT_MAX_PAGE_PIXELS = 8000000;
  const encoder = new TextEncoder();

  function clamp(value, minimum, maximum) {
    return Math.max(
      Number(minimum) || 0,
      Math.min(Number(maximum) || 0, Number(value) || 0)
    );
  }

  function ascii(value) {
    return encoder.encode(String(value || ''));
  }

  function asBytes(value) {
    if (value instanceof Uint8Array) return value;
    if (value instanceof ArrayBuffer) return new Uint8Array(value);
    if (ArrayBuffer.isView(value)) {
      return new Uint8Array(
        value.buffer,
        value.byteOffset,
        value.byteLength
      );
    }
    return ascii(value);
  }

  function concatBytes(parts) {
    const normalized = parts.map(asBytes);
    const length = normalized.reduce(
      (total, part) => total + part.length,
      0
    );
    const output = new Uint8Array(length);
    let offset = 0;

    normalized.forEach(function (part) {
      output.set(part, offset);
      offset += part.length;
    });

    return output;
  }

  function formatNumber(value) {
    const number = Number(value) || 0;
    const fixed = number.toFixed(4);
    return fixed.replace(/\.?0+$/, '') || '0';
  }

  function buildPdfFromJpegPages(pageRecords) {
    const records = Array.isArray(pageRecords)
      ? pageRecords
      : [];

    if (!records.length) {
      throw new Error('At least one rendered page is required.');
    }

    const parts = [];
    const offsets = [];
    let length = 0;

    function append(value) {
      const bytes = asBytes(value);
      parts.push(bytes);
      length += bytes.length;
    }

    function addObject(number, bodyParts) {
      offsets[number] = length;
      append(number + ' 0 obj\n');

      const values = Array.isArray(bodyParts)
        ? bodyParts
        : [bodyParts];

      values.forEach(append);
      append('\nendobj\n');
    }

    append(
      new Uint8Array([
        0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x34, 0x0a,
        0x25, 0xe2, 0xe3, 0xcf, 0xd3, 0x0a
      ])
    );

    const pageObjectNumbers = records.map(function (_, index) {
      return 3 + index * 3;
    });

    addObject(
      1,
      '<< /Type /Catalog /Pages 2 0 R >>'
    );

    addObject(
      2,
      [
        '<< /Type /Pages /Count ',
        String(records.length),
        ' /Kids [',
        pageObjectNumbers.map(function (number) {
          return number + ' 0 R';
        }).join(' '),
        '] >>'
      ]
    );

    records.forEach(function (record, index) {
      const pageObject = 3 + index * 3;
      const contentObject = pageObject + 1;
      const imageObject = pageObject + 2;
      const jpeg = asBytes(record.jpeg);
      const pageWidth = Math.max(1, Number(record.pageWidth) || 1);
      const pageHeight = Math.max(1, Number(record.pageHeight) || 1);
      const pixelWidth = Math.max(1, Math.round(record.pixelWidth || 1));
      const pixelHeight = Math.max(1, Math.round(record.pixelHeight || 1));
      const imageName = 'Im' + (index + 1);

      addObject(
        imageObject,
        [
          '<< /Type /XObject /Subtype /Image',
          ' /Width ', String(pixelWidth),
          ' /Height ', String(pixelHeight),
          ' /ColorSpace /DeviceRGB',
          ' /BitsPerComponent 8',
          ' /Filter /DCTDecode',
          ' /Interpolate true',
          ' /Length ', String(jpeg.length),
          ' >>\nstream\n',
          jpeg,
          '\nendstream'
        ]
      );

      const content = ascii(
        [
          'q',
          formatNumber(pageWidth), '0',
          '0', formatNumber(pageHeight),
          '0 0 cm',
          '/' + imageName, 'Do',
          'Q'
        ].join(' ') + '\n'
      );

      addObject(
        contentObject,
        [
          '<< /Length ',
          String(content.length),
          ' >>\nstream\n',
          content,
          'endstream'
        ]
      );

      addObject(
        pageObject,
        [
          '<< /Type /Page',
          ' /Parent 2 0 R',
          ' /MediaBox [0 0 ',
          formatNumber(pageWidth),
          ' ',
          formatNumber(pageHeight),
          ']',
          ' /Resources << /XObject << /',
          imageName,
          ' ',
          String(imageObject),
          ' 0 R >> >>',
          ' /Contents ',
          String(contentObject),
          ' 0 R',
          ' >>'
        ]
      );
    });

    const objectCount = 2 + records.length * 3;
    const xrefOffset = length;

    append('xref\n0 ' + (objectCount + 1) + '\n');
    append('0000000000 65535 f \n');

    for (let number = 1; number <= objectCount; number += 1) {
      append(
        String(offsets[number] || 0).padStart(10, '0') +
        ' 00000 n \n'
      );
    }

    append(
      [
        'trailer',
        '<< /Size ' + (objectCount + 1) + ' /Root 1 0 R >>',
        'startxref',
        String(xrefOffset),
        '%%EOF',
        ''
      ].join('\n')
    );

    return concatBytes(parts);
  }

  function annotationRects(annotation) {
    if (
      annotation &&
      Array.isArray(annotation.rects) &&
      annotation.rects.length
    ) {
      return annotation.rects;
    }

    if (
      annotation &&
      Number.isFinite(Number(annotation.x)) &&
      Number.isFinite(Number(annotation.y)) &&
      Number.isFinite(Number(annotation.w)) &&
      Number.isFinite(Number(annotation.h))
    ) {
      return [{
        x: Number(annotation.x),
        y: Number(annotation.y),
        w: Number(annotation.w),
        h: Number(annotation.h)
      }];
    }

    return [];
  }

  function rectToPixels(rect, width, height) {
    return Object.freeze({
      x: clamp(rect.x, 0, 1) * width,
      y: clamp(rect.y, 0, 1) * height,
      width: Math.max(1, clamp(rect.w, 0, 1) * width),
      height: Math.max(1, clamp(rect.h, 0, 1) * height)
    });
  }

  function wrapText(context, text, maximumWidth) {
    const words = String(text || '')
      .replace(/\s+/g, ' ')
      .trim()
      .split(' ')
      .filter(Boolean);

    if (!words.length) return [];

    const lines = [];
    let line = '';

    words.forEach(function (word) {
      const candidate = line ? line + ' ' + word : word;

      if (
        line &&
        context.measureText(candidate).width > maximumWidth
      ) {
        lines.push(line);
        line = word;
      } else {
        line = candidate;
      }
    });

    if (line) lines.push(line);
    return lines;
  }

  function drawCommentBox(
    context,
    annotation,
    lastRect,
    canvasWidth,
    canvasHeight
  ) {
    if (
      Number.isFinite(Number(annotation.pageSegmentIndex)) &&
      Number(annotation.pageSegmentIndex) > 0
    ) {
      return;
    }

    const comment = String(annotation.comment || 'Comment').trim();
    const scale = Math.max(1, canvasWidth / 900);
    const padding = Math.round(8 * scale);
    const fontSize = Math.round(11 * scale);
    const titleSize = Math.round(10 * scale);
    const boxWidth = clamp(
      canvasWidth * 0.28,
      150 * scale,
      270 * scale
    );

    context.save();
    context.font = fontSize + 'px Arial, sans-serif';
    const lines = wrapText(
      context,
      comment,
      boxWidth - padding * 2
    ).slice(0, 8);

    const lineHeight = fontSize * 1.28;
    const boxHeight =
      padding * 2 +
      titleSize * 1.3 +
      Math.max(lineHeight, lines.length * lineHeight);

    let x = lastRect.x + lastRect.width + 10 * scale;

    if (x + boxWidth > canvasWidth - 8 * scale) {
      x = lastRect.x - boxWidth - 10 * scale;
    }

    x = clamp(x, 8 * scale, canvasWidth - boxWidth - 8 * scale);

    let y = lastRect.y - 4 * scale;
    y = clamp(y, 8 * scale, canvasHeight - boxHeight - 8 * scale);

    context.fillStyle = 'rgba(255, 245, 179, 0.96)';
    context.strokeStyle = 'rgba(180, 35, 24, 0.95)';
    context.lineWidth = Math.max(1, 1.2 * scale);
    context.fillRect(x, y, boxWidth, boxHeight);
    context.strokeRect(x, y, boxWidth, boxHeight);

    context.fillStyle = '#7a1b12';
    context.font = 'bold ' + titleSize + 'px Arial, sans-serif';
    context.fillText('Comment', x + padding, y + padding + titleSize);

    context.fillStyle = '#2f2f2f';
    context.font = fontSize + 'px Arial, sans-serif';

    lines.forEach(function (line, index) {
      context.fillText(
        line,
        x + padding,
        y + padding + titleSize * 1.6 + (index + 1) * lineHeight
      );
    });

    context.restore();
  }

  function drawTextAnnotation(
    context,
    annotation,
    rect,
    canvasWidth
  ) {
    const text = String(annotation.text || '').trim();
    if (!text) return;

    const scale = Math.max(1, canvasWidth / 900);
    const padding = Math.max(3, 4 * scale);
    const fontSize = clamp(
      rect.height * 0.55,
      10 * scale,
      24 * scale
    );

    context.save();
    context.font = fontSize + 'px Arial, sans-serif';

    const width = Math.max(rect.width, 90 * scale);
    const lines = wrapText(
      context,
      text,
      Math.max(20, width - padding * 2)
    ).slice(0, 12);

    const lineHeight = fontSize * 1.25;
    const height = Math.max(
      rect.height,
      padding * 2 + Math.max(1, lines.length) * lineHeight
    );

    context.fillStyle = 'rgba(255, 255, 255, 0.9)';
    context.strokeStyle = 'rgba(180, 35, 24, 0.86)';
    context.lineWidth = Math.max(1, scale);
    context.fillRect(rect.x, rect.y, width, height);
    context.strokeRect(rect.x, rect.y, width, height);

    context.fillStyle = '#202020';
    lines.forEach(function (line, index) {
      context.fillText(
        line,
        rect.x + padding,
        rect.y + padding + fontSize + index * lineHeight
      );
    });

    context.restore();
  }

  function drawAnnotations(
    context,
    annotations,
    canvasWidth,
    canvasHeight
  ) {
    const list = Array.isArray(annotations)
      ? annotations
      : [];

    list.forEach(function (annotation) {
      const rects = annotationRects(annotation)
        .map(function (rect) {
          return rectToPixels(rect, canvasWidth, canvasHeight);
        });

      if (!rects.length) return;

      if (
        annotation.type === 'highlight' ||
        annotation.type === 'marker'
      ) {
        context.save();
        context.globalCompositeOperation = 'multiply';
        context.fillStyle =
          annotation.type === 'marker'
            ? 'rgba(255, 181, 62, 0.38)'
            : 'rgba(255, 224, 47, 0.42)';

        rects.forEach(function (rect) {
          context.fillRect(
            rect.x,
            rect.y,
            rect.width,
            rect.height
          );
        });

        context.restore();
        return;
      }

      if (annotation.type === 'underline') {
        context.save();
        context.strokeStyle = '#c5221f';
        context.lineCap = 'round';

        rects.forEach(function (rect) {
          context.lineWidth = clamp(
            rect.height * 0.09,
            1.5,
            5
          );
          const y = rect.y + rect.height - context.lineWidth;
          context.beginPath();
          context.moveTo(rect.x, y);
          context.lineTo(rect.x + rect.width, y);
          context.stroke();
        });

        context.restore();
        return;
      }

      if (annotation.type === 'comment') {
        context.save();
        context.globalCompositeOperation = 'multiply';
        context.fillStyle = 'rgba(255, 226, 94, 0.25)';

        rects.forEach(function (rect) {
          context.fillRect(
            rect.x,
            rect.y,
            rect.width,
            rect.height
          );
        });

        context.restore();

        drawCommentBox(
          context,
          annotation,
          rects[rects.length - 1],
          canvasWidth,
          canvasHeight
        );
        return;
      }

      if (annotation.type === 'text') {
        drawTextAnnotation(
          context,
          annotation,
          rects[0],
          canvasWidth
        );
      }
    });
  }

  function dataUrlBytes(dataUrl) {
    const encoded = String(dataUrl || '').split(',')[1] || '';
    const binary = global.atob(encoded);
    const bytes = new Uint8Array(binary.length);

    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }

    return bytes;
  }

  function canvasToJpegBytes(canvas, quality) {
    if (typeof canvas.toBlob === 'function') {
      return new Promise(function (resolve, reject) {
        canvas.toBlob(
          async function (blob) {
            if (!blob) {
              reject(new Error('The page could not be encoded as JPEG.'));
              return;
            }

            resolve(new Uint8Array(await blob.arrayBuffer()));
          },
          'image/jpeg',
          quality
        );
      });
    }

    return Promise.resolve(
      dataUrlBytes(
        canvas.toDataURL('image/jpeg', quality)
      )
    );
  }

  function exportScale(baseViewport, options) {
    const dpi = clamp(
      options && options.dpi,
      96,
      240
    ) || DEFAULT_DPI;

    let scale = dpi / 72;
    const maximumPixels =
      Number(options && options.maxPagePixels) ||
      DEFAULT_MAX_PAGE_PIXELS;

    const pixelCount =
      baseViewport.width *
      baseViewport.height *
      scale *
      scale;

    if (pixelCount > maximumPixels) {
      scale *= Math.sqrt(maximumPixels / pixelCount);
    }

    return Math.max(1, scale);
  }

  async function exportDocument(options) {
    const settings = options || {};
    const pdfDocument = settings.pdfDocument;
    const documentObject =
      settings.documentObject || global.document;
    const pdfRuntime =
      settings.pdfjsLib || global.pdfjsLib;

    if (!pdfDocument || !documentObject || !pdfRuntime) {
      throw new Error('PDF export runtime is unavailable.');
    }

    const pageCount = Number(pdfDocument.numPages) || 0;
    if (!pageCount) {
      throw new Error('The PDF has no pages to save.');
    }

    const annotations = Array.isArray(settings.annotations)
      ? settings.annotations
      : [];

    const pageRecords = [];

    for (
      let pageNumber = 1;
      pageNumber <= pageCount;
      pageNumber += 1
    ) {
      if (typeof settings.onProgress === 'function') {
        settings.onProgress({
          page: pageNumber,
          total: pageCount,
          phase: 'render'
        });
      }

      const page = await pdfDocument.getPage(pageNumber);
      const baseViewport = page.getViewport({ scale: 1 });
      const scale = exportScale(baseViewport, settings);
      const viewport = page.getViewport({ scale });

      const canvas = documentObject.createElement('canvas');
      canvas.width = Math.max(1, Math.ceil(viewport.width));
      canvas.height = Math.max(1, Math.ceil(viewport.height));

      const context = canvas.getContext('2d', {
        alpha: false,
        willReadFrequently: false
      });

      context.save();
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.restore();

      const annotationMode =
        pdfRuntime.AnnotationMode &&
        pdfRuntime.AnnotationMode.ENABLE_STORAGE;

      const renderOptions = {
        canvasContext: context,
        viewport,
        background: '#ffffff',
        annotationStorage: pdfDocument.annotationStorage
      };

      if (annotationMode !== undefined) {
        renderOptions.annotationMode = annotationMode;
      }

      await page.render(renderOptions).promise;

      drawAnnotations(
        context,
        annotations.filter(function (annotation) {
          return Number(annotation.page) === pageNumber;
        }),
        canvas.width,
        canvas.height
      );

      if (typeof settings.onProgress === 'function') {
        settings.onProgress({
          page: pageNumber,
          total: pageCount,
          phase: 'encode'
        });
      }

      const jpeg = await canvasToJpegBytes(
        canvas,
        clamp(
          settings.jpegQuality || DEFAULT_JPEG_QUALITY,
          0.72,
          0.98
        )
      );

      pageRecords.push({
        jpeg,
        pixelWidth: canvas.width,
        pixelHeight: canvas.height,
        pageWidth: baseViewport.width,
        pageHeight: baseViewport.height
      });

      canvas.width=0;
      canvas.height = 0;

      await new Promise(function (resolve) {
        global.setTimeout(resolve, 0);
      });
    }

    const bytes = buildPdfFromJpegPages(pageRecords);
    const originalName = String(
      settings.fileName || 'document.pdf'
    ).replace(/\.pdf$/i, '');

    return Object.freeze({
      bytes,
      fileName: originalName + '-modified.pdf',
      pageCount,
      annotationCount: annotations.length,
      flattened: true,
      textSelectable: false
    });
  }

  const api = Object.freeze({
    version: VERSION,
    concatBytes,
    buildPdfFromJpegPages,
    annotationRects,
    rectToPixels,
    wrapText,
    drawAnnotations,
    exportScale,
    exportDocument
  });

  global.InkDeskPdfFlattenExport = api;
})(typeof window !== 'undefined' ? window : globalThis);

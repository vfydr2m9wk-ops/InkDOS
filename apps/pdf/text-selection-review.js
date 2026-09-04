(function (global) {
  'use strict';

  const VERSION = '0.20.0';

  function clamp(value, minimum, maximum) {
    return Math.max(minimum, Math.min(maximum, Number(value) || 0));
  }

  function normalizeText(value) {
    return String(value || '')
      .replace(/\u00a0/g, ' ')
      .replace(/[ \t\f\v]+/g, ' ')
      .replace(/\s*\n\s*/g, ' ')
      .trim();
  }

  function finiteRect(rect) {
    if (!rect) return null;

    const x = Number(rect.x);
    const y = Number(rect.y);
    const width = Number(rect.width);
    const height = Number(rect.height);

    if (
      !Number.isFinite(x) ||
      !Number.isFinite(y) ||
      !Number.isFinite(width) ||
      !Number.isFinite(height) ||
      width <= 0.5 ||
      height <= 0.5
    ) {
      return null;
    }

    return { x, y, width, height };
  }

  function verticalOverlap(a, b) {
    return Math.max(
      0,
      Math.min(a.y + a.height, b.y + b.height) -
        Math.max(a.y, b.y)
    );
  }

  function sameLine(a, b) {
    const overlap = verticalOverlap(a, b);
    const minimumHeight = Math.min(a.height, b.height);
    const centerA = a.y + a.height / 2;
    const centerB = b.y + b.height / 2;

    return (
      overlap >= minimumHeight * 0.42 ||
      Math.abs(centerA - centerB) <= Math.max(2, minimumHeight * 0.32)
    );
  }

  function mergeRects(rects) {
    const sorted = (Array.isArray(rects) ? rects : [])
      .map(finiteRect)
      .filter(Boolean)
      .sort(function (a, b) {
        const vertical = a.y - b.y;
        if (Math.abs(vertical) > Math.max(2, Math.min(a.height, b.height) * 0.35)) {
          return vertical;
        }
        return a.x - b.x;
      });

    const merged = [];

    sorted.forEach(function (rect) {
      const previous = merged[merged.length - 1];

      if (!previous || !sameLine(previous, rect)) {
        merged.push({ ...rect });
        return;
      }

      const gap = rect.x - (previous.x + previous.width);
      const allowedGap = Math.max(3, Math.min(previous.height, rect.height) * 0.48);

      if (gap > allowedGap) {
        merged.push({ ...rect });
        return;
      }

      const left = Math.min(previous.x, rect.x);
      const top = Math.min(previous.y, rect.y);
      const right = Math.max(
        previous.x + previous.width,
        rect.x + rect.width
      );
      const bottom = Math.max(
        previous.y + previous.height,
        rect.y + rect.height
      );

      previous.x = left;
      previous.y = top;
      previous.width = right - left;
      previous.height = bottom - top;
    });

    return merged;
  }

  function intersectRect(rect, bounds) {
    const source = finiteRect(rect);
    const target = finiteRect(bounds);
    if (!source || !target) return null;

    const left = Math.max(source.x, target.x);
    const top = Math.max(source.y, target.y);
    const right = Math.min(
      source.x + source.width,
      target.x + target.width
    );
    const bottom = Math.min(
      source.y + source.height,
      target.y + target.height
    );

    if (right - left <= 0.5 || bottom - top <= 0.5) return null;

    return {
      x: left,
      y: top,
      width: right - left,
      height: bottom - top
    };
  }

  function normalizeRect(rect, bounds) {
    const intersection = intersectRect(rect, bounds);
    if (!intersection) return null;

    return {
      x: clamp((intersection.x - bounds.x) / bounds.width, 0, 1),
      y: clamp((intersection.y - bounds.y) / bounds.height, 0, 1),
      w: clamp(intersection.width / bounds.width, 0, 1),
      h: clamp(intersection.height / bounds.height, 0, 1)
    };
  }

  function rangeIntersectsNode(range, node, documentObject) {
    if (!range || !node) return false;

    if (typeof range.intersectsNode === 'function') {
      try {
        return range.intersectsNode(node);
      } catch (error) {
        /* Fall through to boundary comparison. */
      }
    }

    try {
      const nodeRange = documentObject.createRange();
      nodeRange.selectNodeContents(node);

      const sourceEndsBeforeNodeStarts =
        range.compareBoundaryPoints(
          global.Range.END_TO_START,
          nodeRange
        ) <= 0;

      const sourceStartsAfterNodeEnds =
        range.compareBoundaryPoints(
          global.Range.START_TO_END,
          nodeRange
        ) >= 0;

      return (
        !sourceEndsBeforeNodeStarts &&
        !sourceStartsAfterNodeEnds
      );
    } catch (error) {
      return false;
    }
  }

  function selectedNodeRange(sourceRange, node, documentObject) {
    if (
      !rangeIntersectsNode(
        sourceRange,
        node,
        documentObject
      )
    ) {
      return null;
    }

    const part = documentObject.createRange();
    part.selectNodeContents(node);

    try {
      if (sourceRange.startContainer === node) {
        part.setStart(node, sourceRange.startOffset);
      }

      if (sourceRange.endContainer === node) {
        part.setEnd(node, sourceRange.endOffset);
      }
    } catch (error) {
      return null;
    }

    return part.collapsed ? null : part;
  }

  function textNodes(element, documentObject) {
    const result = [];
    const walker = documentObject.createTreeWalker(
      element,
      global.NodeFilter.SHOW_TEXT
    );

    let node = walker.nextNode();
    while (node) {
      if (String(node.nodeValue || '').length) result.push(node);
      node = walker.nextNode();
    }

    return result;
  }

  function captureSelection(selection, documentObject) {
    const doc = documentObject || global.document;

    if (
      !doc ||
      !selection ||
      selection.rangeCount < 1 ||
      selection.isCollapsed
    ) {
      return null;
    }

    const selectedText = normalizeText(selection.toString());
    if (!selectedText) return null;

    const sourceRange = selection.getRangeAt(0);
    const pages = [];

    const textLayers = Array.from(
      doc.querySelectorAll('.pdf-page-shell .textLayer')
    );

    textLayers.forEach(function (textLayer) {
      const shell = textLayer.closest('.pdf-page-shell');
      const reviewLayer = shell &&
        shell.querySelector('.page-review-layer');

      if (!shell || !reviewLayer) return;

      const reviewBounds = finiteRect(
        reviewLayer.getBoundingClientRect()
      );
      const textBounds = finiteRect(
        textLayer.getBoundingClientRect()
      );

      if (!reviewBounds || !textBounds) return;

      const pixelRects = [];

      const spans = Array.from(
        textLayer.querySelectorAll('span')
      );

      spans.forEach(function (span) {
        textNodes(span, doc).forEach(function (node) {
          const part = selectedNodeRange(
            sourceRange,
            node,
            doc
          );
          if (!part) return;

          Array.from(part.getClientRects()).forEach(
            function (clientRect) {
              const clipped = intersectRect(
                clientRect,
                textBounds
              );
              if (!clipped) return;

              pixelRects.push({
                x: clipped.x - reviewBounds.x,
                y: clipped.y - reviewBounds.y,
                width: clipped.width,
                height: clipped.height
              });
            }
          );
        });
      });

      const merged = mergeRects(pixelRects)
        .map(function (rect) {
          return normalizeRect(
            {
              x: rect.x + reviewBounds.x,
              y: rect.y + reviewBounds.y,
              width: rect.width,
              height: rect.height
            },
            reviewBounds
          );
        })
        .filter(Boolean)
        .filter(function (rect) {
          return rect.w > 0.0005 && rect.h > 0.0005;
        });

      if (!merged.length) return;

      pages.push({
        page: Number(shell.dataset.page) || 1,
        rects: merged
      });
    });

    if (!pages.length) return null;

    const signature = [
      selectedText,
      pages.map(function (page) {
        return [
          page.page,
          page.rects.map(function (rect) {
            return [
              rect.x.toFixed(5),
              rect.y.toFixed(5),
              rect.w.toFixed(5),
              rect.h.toFixed(5)
            ].join(',');
          }).join(';')
        ].join(':');
      }).join('|')
    ].join('::');

    return Object.freeze({
      text: selectedText,
      pages: Object.freeze(
        pages.map(function (page) {
          return Object.freeze({
            page: page.page,
            rects: Object.freeze(
              page.rects.map(function (rect) {
                return Object.freeze({ ...rect });
              })
            )
          });
        })
      ),
      signature
    });
  }

  function buildAnnotations(
    capture,
    type,
    options
  ) {
    if (
      !capture ||
      !Array.isArray(capture.pages) ||
      !capture.pages.length
    ) {
      return [];
    }

    if (!['highlight', 'underline', 'comment'].includes(type)) {
      throw new Error('Unsupported selected-text annotation type.');
    }

    const settings = options || {};
    const makeId =
      typeof settings.makeId === 'function'
        ? settings.makeId
        : function () {
            return (
              global.crypto &&
              typeof global.crypto.randomUUID === 'function'
                ? global.crypto.randomUUID()
                : String(Date.now()) + '-' + Math.random().toString(36).slice(2)
            );
          };

    const groupId = settings.groupId || makeId();
    const comment = type === 'comment'
      ? String(settings.comment || '')
      : '';

    return capture.pages.map(function (page, pageIndex) {
      return {
        id: makeId(),
        groupId,
        page: page.page,
        type,
        source: 'text-selection',
        selectedText: capture.text,
        comment,
        rects: page.rects.map(function (rect) {
          return {
            x: clamp(rect.x, 0, 1),
            y: clamp(rect.y, 0, 1),
            w: clamp(rect.w, 0, 1),
            h: clamp(rect.h, 0, 1)
          };
        }),
        pageSegmentIndex: pageIndex,
        pageSegmentCount: capture.pages.length
      };
    });
  }

  const api = Object.freeze({
    version: VERSION,
    normalizeText,
    mergeRects,
    intersectRect,
    normalizeRect,
    captureSelection,
    buildAnnotations
  });

  global.InkDOSPdfTextSelection = api;
})(typeof window !== 'undefined' ? window : globalThis);

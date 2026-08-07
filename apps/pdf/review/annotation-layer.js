(function (global) {
  'use strict';

  function createAnnotationLayer({
    state,
    clamp,
    makeId,
    isFreeAnnotationTool,
    markDirty,
    renderSideLists
  }) {
    if (
      !state ||
      !clamp ||
      !makeId ||
      !isFreeAnnotationTool ||
      !markDirty ||
      !renderSideLists
    ) {
      throw new Error(
        'InkDesk PDF annotation layer requires state and review callbacks.'
      );
    }

    function annotationRects(annotation) {
      if (
        Array.isArray(annotation.rects) &&
        annotation.rects.length
      ) {
        return annotation.rects;
      }

      if (
        Number.isFinite(Number(annotation.x)) &&
        Number.isFinite(Number(annotation.y)) &&
        Number.isFinite(Number(annotation.w)) &&
        Number.isFinite(Number(annotation.h))
      ) {
        return [
          {
            x: Number(annotation.x),
            y: Number(annotation.y),
            w: Number(annotation.w),
            h: Number(annotation.h)
          }
        ];
      }

      return [];
    }

    function renderPageReview(pageNumber) {
      const shell = state.pages.get(pageNumber);
      const layer = shell?.querySelector('.page-review-layer');
      if (!layer) return;

      layer.replaceChildren();

      for (
        const annotation of state.annotations.filter(
          item => item.page === pageNumber
        )
      ) {
        const rects = annotationRects(annotation);

        rects.forEach((rect, rectIndex) => {
          const element = document.createElement('div');

          element.className =
            `review-annotation ${annotation.type}` +
            (annotation.source === 'text-selection'
              ? ' text-selection-segment'
              : '') +
            (rectIndex === rects.length - 1
              ? ' selection-segment-last'
              : '');

          element.style.cssText = [
            `left:${clamp(rect.x, 0, 1) * 100}%`,
            `top:${clamp(rect.y, 0, 1) * 100}%`,
            `width:${clamp(rect.w, 0, 1) * 100}%`,
            `height:${clamp(rect.h, 0, 1) * 100}%`
          ].join(';');

          if (
            annotation.text &&
            annotation.source !== 'text-selection'
          ) {
            element.textContent = annotation.text;
          }

          const titleParts = [];
          if (annotation.comment) {
            titleParts.push(annotation.comment);
          }
          if (annotation.selectedText) {
            titleParts.push(
              `Selected text: ${annotation.selectedText}`
            );
          }

          element.title = titleParts.join('\n');
          layer.append(element);
        });
      }
    }

    function wireReviewLayer(layer, pageNumber) {
      let start = null;

      layer.onpointerdown = event => {
        if (!isFreeAnnotationTool(state.tool)) return;

        const bounds = layer.getBoundingClientRect();
        start = {
          x: clamp(
            (event.clientX - bounds.left) / bounds.width,
            0,
            1
          ),
          y: clamp(
            (event.clientY - bounds.top) / bounds.height,
            0,
            1
          ),
          id: event.pointerId
        };

        layer.setPointerCapture?.(event.pointerId);
      };

      layer.onpointerup = event => {
        if (!start) return;

        const bounds = layer.getBoundingClientRect();
        const endX = clamp(
          (event.clientX - bounds.left) / bounds.width,
          0,
          1
        );
        const endY = clamp(
          (event.clientY - bounds.top) / bounds.height,
          0,
          1
        );

        const item = {
          id: makeId(),
          page: pageNumber,
          type: state.tool,
          source: 'free',
          x: Math.min(start.x, endX),
          y: Math.min(start.y, endY),
          w: Math.max(0.012, Math.abs(endX - start.x)),
          h: Math.max(0.012, Math.abs(endY - start.y))
        };

        if (state.tool === 'text') {
          const insertedText = prompt('Text:', '');
          if (insertedText === null) {
            start = null;
            return;
          }
          item.text = insertedText;
        }

        state.undo.push({
          kind: 'annotation',
          id: item.id
        });
        state.annotations.push(item);
        start = null;

        markDirty();
        renderPageReview(pageNumber);
        renderSideLists();
      };
    }

    return Object.freeze({
      annotationRects,
      renderPageReview,
      wireReviewLayer
    });
  }

  global.InkDeskPdfAnnotationLayer = Object.freeze({
    version: '0.20.2.12',
    createAnnotationLayer
  });
})(globalThis);

(function (global) {
  'use strict';

  function createAnnotationLayer({
    state,
    clamp,
    isFreeAnnotationTool,
    commitFreeAnnotation,
    requestTextAnnotation,
    requestTextEdit
  }) {
    if (
      !state ||
      !clamp ||
      !isFreeAnnotationTool ||
      !commitFreeAnnotation ||
      !requestTextAnnotation ||
      !requestTextEdit
    ) {
      throw new Error(
        'InkDOS PDF annotation layer requires state and review callbacks.'
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

          if (annotation.id) {
            element.dataset.annotationId = annotation.id;
          }

          if (
            annotation.text &&
            annotation.source !== 'text-selection'
          ) {
            element.textContent = annotation.text;
          }

          const titleParts = [];
          if (annotation.type === 'text') {
            titleParts.push('Tap to edit text');
          }
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

      function resetPointer() {
        start = null;
      }

      layer.onpointerdown = event => {
        if (!isFreeAnnotationTool(state.tool)) return;

        const editableText =
          state.tool === 'text' &&
          event.target.closest?.(
            '.review-annotation.text[data-annotation-id]'
          );

        if (editableText) {
          start = {
            editId: editableText.dataset.annotationId,
            id: event.pointerId
          };
          layer.setPointerCapture?.(event.pointerId);
          event.preventDefault();
          return;
        }

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

        if (start.editId) {
          const editId = start.editId;
          resetPointer();
          requestTextEdit(editId);
          return;
        }

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

        let x = Math.min(start.x, endX);
        let y = Math.min(start.y, endY);
        let w = Math.abs(endX - start.x);
        let h = Math.abs(endY - start.y);

        if (state.tool === 'text') {
          w = Math.max(0.18, w);
          h = Math.max(0.06, h);
          x = clamp(x, 0, Math.max(0, 1 - w));
          y = clamp(y, 0, Math.max(0, 1 - h));
        } else {
          w = Math.max(0.012, w);
          h = Math.max(0.012, h);
        }

        const item = {
          page: pageNumber,
          type: state.tool,
          source: 'free',
          x,
          y,
          w,
          h
        };

        resetPointer();

        if (item.type === 'text') {
          requestTextAnnotation(item);
          return;
        }

        commitFreeAnnotation(item);
      };

      layer.onpointercancel = resetPointer;
      layer.onlostpointercapture = () => {
        if (start?.editId) resetPointer();
      };
    }

    return Object.freeze({
      annotationRects,
      renderPageReview,
      wireReviewLayer
    });
  }

  global.InkDOSPdfAnnotationLayer = Object.freeze({
    version: '0.20.3.0',
    createAnnotationLayer
  });
})(globalThis);

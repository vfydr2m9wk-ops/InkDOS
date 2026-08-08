(function (global) {
  'use strict';

  const VERSION = '0.20.2.19';

  function create(options) {
    const config = options || {};
    const documentObject = config.documentObject;
    const ruler = config.ruler;
    const track = config.track;
    const pagesHost = config.pagesHost;
    const model = config.model;
    const scheduleSync = config.scheduleSync;
    const sync = config.sync;
    const currentBlockState = config.currentBlockState;
    const updateHandles = config.updateHandles;
    const getMetrics = config.getMetrics;
    const setMetrics = config.setMetrics;
    const getActivePage = config.getActivePage;

    if (
      !documentObject ||
      !ruler ||
      !track ||
      !pagesHost ||
      !model ||
      typeof scheduleSync !== 'function' ||
      typeof sync !== 'function' ||
      typeof currentBlockState !== 'function' ||
      typeof updateHandles !== 'function' ||
      typeof getMetrics !== 'function' ||
      typeof setMetrics !== 'function' ||
      typeof getActivePage !== 'function'
    ) {
      return null;
    }

    let drag = null;

    function startDrag(event) {
      const target =
        event.target &&
        typeof event.target.closest === 'function' &&
        event.target.closest('.ruler-handle');

      if (!target || !track.contains(target)) return;

      scheduleSync();
      sync();

      const metrics = getMetrics();
      if (!metrics) return;

      const selected = currentBlockState();

      if (!selected.block) {
        const status =
          documentObject.getElementById('statusText');
        if (status) {
          status.textContent =
            'Place the cursor in a paragraph before changing indentation.';
        }
        event.preventDefault();
        event.stopImmediatePropagation();
        return;
      }

      const kind =
        target.id === 'firstIndent'
          ? 'first'
          : target.id === 'hangingIndent'
            ? 'hanging'
            : target.id === 'leftIndent'
              ? 'left'
              : target.id === 'rightIndent'
                ? 'right'
                : '';

      if (!kind) return;

      drag = {
        kind,
        pointerId: event.pointerId,
        startClientX: event.clientX,
        block: selected.block,
        initial: selected.state,
        state: selected.state,
        metrics
      };

      if (
        typeof target.setPointerCapture === 'function'
      ) {
        try {
          target.setPointerCapture(event.pointerId);
        } catch (error) {
          /* Window listeners still preserve dragging. */
        }
      }

      event.preventDefault();
      event.stopImmediatePropagation();
    }

    function moveDrag(event) {
      if (
        !drag ||
        (
          drag.pointerId !== undefined &&
          event.pointerId !== undefined &&
          drag.pointerId !== event.pointerId
        )
      ) {
        return;
      }

      const nextMetrics =
        model.rulerMetrics(getActivePage(), global) ||
        drag.metrics;

      const state = {
        left: drag.state.left,
        first: drag.state.first,
        right: drag.state.right
      };

      const local = model.pointerToDocumentIndent(
        event.clientX,
        nextMetrics
      );

      if (drag.kind === 'first') {
        state.first = local;
      } else if (drag.kind === 'hanging') {
        state.left = local;
      } else if (drag.kind === 'left') {
        const delta =
          (
            event.clientX -
            drag.startClientX
          ) / Math.max(nextMetrics.zoom, 0.001);

        state.left =
          drag.initial.left + delta;
        state.first =
          drag.initial.first + delta;
      } else if (drag.kind === 'right') {
        state.right =
          nextMetrics.contentWidth - local;
      }

      drag.state = model.clampIndentState(
        state,
        nextMetrics
      );

      setMetrics(nextMetrics);
      updateHandles(drag.state);
      model.applyDocumentIndent(
        drag.block,
        drag.state,
        pagesHost
      );

      const status =
        documentObject.getElementById('statusText');

      if (status) {
        status.textContent =
          'Paragraph indentation updated';
      }

      event.preventDefault();
      event.stopImmediatePropagation();
    }

    function endDrag(event) {
      if (!drag) return;

      if (
        drag.pointerId !== undefined &&
        event.pointerId !== undefined &&
        drag.pointerId !== event.pointerId
      ) {
        return;
      }

      drag = null;
      scheduleSync();

      event.preventDefault();
      event.stopImmediatePropagation();
    }

    ruler.addEventListener(
      'pointerdown',
      startDrag,
      true
    );

    global.addEventListener(
      'pointermove',
      moveDrag,
      true
    );

    global.addEventListener(
      'pointerup',
      endDrag,
      true
    );

    global.addEventListener(
      'pointercancel',
      endDrag,
      true
    );

    return Object.freeze({
      version: VERSION,
      active: function () { return Boolean(drag); },
      destroy: function () {
        ruler.removeEventListener(
          'pointerdown',
          startDrag,
          true
        );
        global.removeEventListener(
          'pointermove',
          moveDrag,
          true
        );
        global.removeEventListener(
          'pointerup',
          endDrag,
          true
        );
        global.removeEventListener(
          'pointercancel',
          endDrag,
          true
        );
        drag = null;
      }
    });
  }

  global.InkDeskDocumentRulerDragController = Object.freeze({
    version: VERSION,
    create
  });
})(typeof window !== 'undefined' ? window : globalThis);

(function (global) {
  'use strict';

  const VERSION = '0.20.1';
  const REFERENCE_CLASS = 'formula-reference-range';
  const TARGET_CLASS = 'formula-target-cell';
  const COLOR_COUNT = 6;

  function clamp(value, minimum, maximum) {
    return Math.max(Number(minimum) || 0, Math.min(Number(maximum) || 0, Number(value) || 0));
  }

  function encodeColumn(index) {
    let value = Math.max(0, Number(index) || 0) + 1;
    let result = '';
    while (value > 0) {
      const remainder = (value - 1) % 26;
      result = String.fromCharCode(65 + remainder) + result;
      value = Math.floor((value - 1) / 26);
    }
    return result;
  }

  function encodeCell(row, column) {
    return encodeColumn(column) + (Math.max(0, Number(row) || 0) + 1);
  }

  function normalizeRange(start, end) {
    const first = start || { r: 0, c: 0 };
    const last = end || first;
    return Object.freeze({
      r1: Math.min(Number(first.r) || 0, Number(last.r) || 0),
      c1: Math.min(Number(first.c) || 0, Number(last.c) || 0),
      r2: Math.max(Number(first.r) || 0, Number(last.r) || 0),
      c2: Math.max(Number(first.c) || 0, Number(last.c) || 0)
    });
  }

  function formatRange(start, end) {
    const range = normalizeRange(start, end);
    const first = encodeCell(range.r1, range.c1);
    const last = encodeCell(range.r2, range.c2);
    return first === last ? first : first + ':' + last;
  }

  function referenceTokenBefore(value, cursor) {
    const before = String(value || '').slice(0, cursor);
    const match = before.match(/(?:(?:'((?:[^']|'')+)'|[A-Za-z0-9_ .-]+)!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?$/i);
    if (!match) return null;
    return { start: cursor - match[0].length, end: cursor, text: match[0] };
  }

  function needsSeparator(prefix) {
    const trimmed = String(prefix || '').replace(/\s+$/g, '');
    if (!trimmed) return false;
    return !/[=(,+\-*/^&;:]$/.test(trimmed);
  }

  function insertReference(value, selectionStart, selectionEnd, reference, options) {
    const source = String(value || '');
    const settings = options || {};
    const additive = settings.additive === true;
    let start = clamp(selectionStart, 0, source.length);
    let end = clamp(selectionEnd, start, source.length);
    if (!additive && settings.replaceToken === true && start === end) {
      const token = referenceTokenBefore(source, start);
      if (token) {
        start = token.start;
        end = token.end;
      }
    }
    const before = source.slice(0, start);
    const after = source.slice(end);
    const separator = additive && needsSeparator(before) ? ',' : '';
    const insertion = separator + String(reference || '');
    return Object.freeze({
      value: before + insertion + after,
      caret: before.length + insertion.length,
      referenceStart: before.length + separator.length,
      referenceEnd: before.length + insertion.length,
      separator
    });
  }

  function cellCoordinates(element) {
    if (!element || !element.dataset) return null;
    const row = Number(element.dataset.r);
    const column = Number(element.dataset.c);
    if (!Number.isFinite(row) || !Number.isFinite(column)) return null;
    return Object.freeze({ r: row, c: column });
  }

  function createController(documentObject) {
    const doc = documentObject || global.document;
    if (!doc || !doc.getElementById) return null;
    const grid = doc.getElementById('grid');
    const viewport = doc.getElementById('gridViewport');
    const addRange = doc.getElementById('addFormulaRangeBtn');
    const status = doc.getElementById('formulaReferenceStatus');
    if (!grid || !viewport) return null;

    const state = {
      active: false,
      targetReference: '',
      drag: null,
      references: [],
      nextAdditive: false,
      colorIndex: 0,
      frame: 0,
      pendingPoint: null
    };

    function editor() {
      return global.InkDOSSpreadsheetFormulaEditor || null;
    }

    function setStatus(message) {
      if (!status) return;
      status.hidden = !message;
      status.textContent = String(message || '');
    }

    function clearVisualReferences() {
      grid.querySelectorAll('.' + REFERENCE_CLASS + ',.' + TARGET_CLASS).forEach(function (cell) {
        cell.classList.remove(
          REFERENCE_CLASS,
          TARGET_CLASS,
          'formula-reference-color-1',
          'formula-reference-color-2',
          'formula-reference-color-3',
          'formula-reference-color-4',
          'formula-reference-color-5',
          'formula-reference-color-6'
        );
        delete cell.dataset.formulaReference;
      });
    }

    function findCell(reference) {
      const match = /^\$?([A-Z]{1,3})\$?(\d+)$/i.exec(String(reference || '').trim());
      if (!match) return null;
      let column = 0;
      for (const character of match[1].toUpperCase()) {
        column = column * 26 + character.charCodeAt(0) - 64;
      }
      return grid.querySelector(
        `.cell[data-r="${Number(match[2]) - 1}"][data-c="${column - 1}"]`
      );
    }

    function markRange(range, colorIndex) {
      const colorClass = 'formula-reference-color-' + ((colorIndex % COLOR_COUNT) + 1);
      grid.querySelectorAll('.cell').forEach(function (cell) {
        const point = cellCoordinates(cell);
        if (!point) return;
        if (
          point.r >= range.r1 && point.r <= range.r2 &&
          point.c >= range.c1 && point.c <= range.c2
        ) {
          cell.classList.add(REFERENCE_CLASS, colorClass);
          cell.dataset.formulaReference = formatRange(
            { r: range.r1, c: range.c1 },
            { r: range.r2, c: range.c2 }
          );
        }
      });
    }

    function render(activeRange, activeColor) {
      clearVisualReferences();
      const target = findCell(state.targetReference);
      if (target) target.classList.add(TARGET_CLASS);
      state.references.forEach(function (entry) {
        markRange(entry.range, entry.colorIndex);
      });
      if (activeRange) markRange(activeRange, activeColor);
    }

    function begin(targetReference) {
      const nextTarget = String(targetReference || '').toUpperCase();
      if (state.targetReference !== nextTarget) {
        state.references = [];
        state.colorIndex = 0;
      }
      state.targetReference = nextTarget;
      state.active = true;
      const currentEditor = editor();
      const armed = Boolean(
        currentEditor &&
        currentEditor.isActive() &&
        currentEditor.canSelectReference()
      );
      doc.body.dataset.formulaReferenceMode = armed ? 'armed' : 'standby';
      if (addRange) addRange.hidden = !armed;
      render();
      return armed;
    }

    function pause() {
      state.active = false;
      state.drag = null;
      state.nextAdditive = false;
      clearVisualReferences();
      delete doc.body.dataset.formulaReferenceMode;
      if (addRange) addRange.hidden = true;
    }

    function end(message) {
      pause();
      state.references = [];
      state.targetReference = '';
      setStatus(message || '');
    }

    function pointFromTarget(target) {
      return cellCoordinates(target?.closest?.('.cell'));
    }

    function pointFromEvent(event) {
      const direct = pointFromTarget(event.target);
      if (direct) return direct;
      if (doc.elementFromPoint && Number.isFinite(event.clientX) && Number.isFinite(event.clientY)) {
        return pointFromTarget(doc.elementFromPoint(event.clientX, event.clientY));
      }
      return null;
    }

    function updateDrag(point) {
      if (!state.drag || !point) return;
      const range = normalizeRange(state.drag.start, point);
      const reference = formatRange(state.drag.start, point);
      const result = insertReference(
        state.drag.baseValue,
        state.drag.baseStart,
        state.drag.baseEnd,
        reference,
        { additive: state.drag.additive, replaceToken: false }
      );
      state.drag.range = range;
      state.drag.result = result;
      editor()?.applyReference(result);
      render(range, state.drag.colorIndex);
      setStatus('Reference ' + reference + ' selected. Release to keep it; click another cell to add it.');
    }

    function beginReference(event) {
      const currentEditor = editor();
      const cell = event.target?.closest?.('.cell');
      if (doc.body.dataset.formulaReferenceMode !== 'armed' || !state.active || !cell || !currentEditor || !currentEditor.isActive() || !currentEditor.canSelectReference()) return;
      const point = cellCoordinates(cell);
      if (!point) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      begin(currentEditor.getTargetReference());
      const selection = currentEditor.getSelection();
      const additive = Boolean(
        event.ctrlKey || event.metaKey || state.nextAdditive || currentEditor.shouldAppendReference()
      );
      state.nextAdditive = false;
      state.drag = {
        pointerId: event.pointerId,
        start: point,
        baseValue: currentEditor.getValue(),
        baseStart: selection.start,
        baseEnd: selection.end,
        additive,
        colorIndex: state.colorIndex % COLOR_COUNT,
        range: normalizeRange(point, point),
        result: null
      };
      updateDrag(point);
      if (typeof cell.setPointerCapture === 'function' && event.pointerId !== undefined) {
        try { cell.setPointerCapture(event.pointerId); } catch (error) { void error; }
      }
    }

    function moveReference(event) {
      if (!state.drag) return;
      if (
        state.drag.pointerId !== undefined &&
        event.pointerId !== undefined &&
        state.drag.pointerId !== event.pointerId
      ) return;
      state.pendingPoint = pointFromEvent(event);
      if (!state.pendingPoint || state.frame) return;
      const renderFrame = function () {
        state.frame = 0;
        const point = state.pendingPoint;
        state.pendingPoint = null;
        updateDrag(point);
      };
      state.frame = global.requestAnimationFrame
        ? global.requestAnimationFrame(renderFrame)
        : global.setTimeout(renderFrame, 0);
      event.preventDefault();
      event.stopImmediatePropagation();
    }

    function finishReference(event) {
      if (!state.drag) return;
      if (
        state.drag.pointerId !== undefined &&
        event.pointerId !== undefined &&
        state.drag.pointerId !== event.pointerId
      ) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      const finished = state.drag;
      state.drag = null;
      if (!finished.additive && state.references.length === 0) {
        state.references = [];
      }
      state.references.push({ range: finished.range, colorIndex: finished.colorIndex });
      state.colorIndex = (finished.colorIndex + 1) % COLOR_COUNT;
      render();
      const reference = formatRange(
        { r: finished.range.r1, c: finished.range.c1 },
        { r: finished.range.r2, c: finished.range.c2 }
      );
      editor()?.focus();
      setStatus(reference + ' added. Click or drag another cell, type ")", or press Enter.');
    }

    grid.addEventListener('pointerdown', beginReference, true);
    global.addEventListener('pointermove', moveReference, true);
    global.addEventListener('pointerup', finishReference, true);
    global.addEventListener('pointercancel', finishReference, true);

    if (addRange) {
      addRange.addEventListener('pointerdown', function (event) { event.preventDefault(); });
      addRange.addEventListener('click', function () {
        const currentEditor = editor();
        if (!currentEditor || !currentEditor.isActive() || !currentEditor.canSelectReference() || doc.body.dataset.formulaReferenceMode !== 'armed') return;
        state.nextAdditive = true;
        currentEditor.focus();
        setStatus('Add-range mode: click a cell or drag another range.');
      });
    }

    viewport.addEventListener('scroll', function () {
      if (state.active) render();
    }, { passive: true });

    const controller = Object.freeze({
      version: VERSION,
      state,
      begin,
      pause,
      end,
      insertReference,
      normalizeRange,
      formatRange
    });

    global.InkDOSSpreadsheetFormulaReferences = controller;
    return controller;
  }

  const api = Object.freeze({
    version: VERSION,
    encodeColumn,
    encodeCell,
    normalizeRange,
    formatRange,
    insertReference,
    cellCoordinates,
    createController
  });

  global.InkDOSFormulaReferences = api;

  function initialize() { createController(global.document); }
  if (global.document) {
    if (global.document.readyState === 'loading') {
      global.document.addEventListener('DOMContentLoaded', initialize, { once: true });
    } else initialize();
  }
})(typeof window !== 'undefined' ? window : globalThis);

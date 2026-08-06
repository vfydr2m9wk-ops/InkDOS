(function (global) {
  'use strict';

  const VERSION = '0.19.4.9';
  const REFERENCE_CLASS = 'formula-reference-range';
  const TARGET_CLASS = 'formula-target-cell';
  const COLOR_COUNT = 6;

  function clamp(value, minimum, maximum) {
    return Math.max(
      Number(minimum) || 0,
      Math.min(Number(maximum) || 0, Number(value) || 0)
    );
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
    const match = before.match(
      /(?:(?:'((?:[^']|'')+)'|[A-Za-z0-9_ .-]+)!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?$/i
    );

    if (!match) return null;

    return {
      start: cursor - match[0].length,
      end: cursor,
      text: match[0]
    };
  }

  function unmatchedParentheses(value) {
    let depth = 0;
    let quoted = false;

    for (let index = 0; index < String(value || '').length; index += 1) {
      const character = value[index];

      if (character === '"') {
        if (quoted && value[index + 1] === '"') {
          index += 1;
        } else {
          quoted = !quoted;
        }
        continue;
      }

      if (quoted) continue;
      if (character === '(') depth += 1;
      if (character === ')') depth = Math.max(0, depth - 1);
    }

    return depth;
  }

  function needsSeparator(prefix) {
    const trimmed = String(prefix || '').replace(/\s+$/g, '');
    if (!trimmed) return false;

    return !/[=(,+\-*/^&;:]$/.test(trimmed);
  }

  function insertReference(
    value,
    selectionStart,
    selectionEnd,
    reference,
    options
  ) {
    const source = String(value || '');
    const settings = options || {};
    const additive = settings.additive === true;

    let start = clamp(
      selectionStart,
      0,
      source.length
    );

    let end = clamp(
      selectionEnd,
      start,
      source.length
    );

    if (!additive && start === end) {
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
    let result = before + insertion + after;
    const referenceStart = before.length + separator.length;
    const referenceEnd = referenceStart + String(reference || '').length;
    let caret = referenceEnd;

    if (settings.autoClose !== false) {
      const missing = unmatchedParentheses(result);

      if (missing > 0 && !result.slice(caret).includes(')')) {
        result += ')'.repeat(missing);
      }
    }

    return Object.freeze({
      value: result,
      caret,
      referenceStart,
      referenceEnd,
      separator
    });
  }

  function cellCoordinates(element) {
    if (!element || !element.dataset) return null;

    const row = Number(element.dataset.r);
    const column = Number(element.dataset.c);

    if (!Number.isFinite(row) || !Number.isFinite(column)) {
      return null;
    }

    return Object.freeze({ r: row, c: column });
  }

  function createController(documentObject) {
    const doc = documentObject || global.document;
    if (!doc || !doc.getElementById) return null;

    const formula = doc.getElementById('formulaInput');
    const nameBox = doc.getElementById('nameBox');
    const grid = doc.getElementById('grid');
    const viewport = doc.getElementById('gridViewport');
    const suggestions = doc.getElementById('formulaSuggestions');
    const addRange = doc.getElementById('addFormulaRangeBtn');
    const status = doc.getElementById('formulaReferenceStatus');

    if (!formula || !nameBox || !grid || !viewport) return null;
    if (formula.__inkdeskFormulaReferenceController) {
      return formula.__inkdeskFormulaReferenceController;
    }

    const state = {
      active: false,
      targetReference: '',
      targetCell: null,
      drag: null,
      references: [],
      nextAdditive: false,
      colorIndex: 0,
      pointerFrame: 0,
      pendingPointer: null
    };

    function formulaEditor() {
      return global.InkDeskSpreadsheetFormulaEditor || null;
    }

    function setStatus(message) {
      if (!status) return;

      status.hidden = !message;
      status.textContent = String(message || '');
    }

    function allReferenceCells() {
      return Array.from(
        grid.querySelectorAll(
          '.' + REFERENCE_CLASS + ',.' + TARGET_CLASS
        )
      );
    }

    function clearVisualReferences() {
      allReferenceCells().forEach(function (cell) {
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
      const match = /^\$?([A-Z]{1,3})\$?(\d+)$/i.exec(
        String(reference || '').trim()
      );

      if (!match) return null;

      let column = 0;
      const letters = match[1].toUpperCase();

      for (const character of letters) {
        column = column * 26 + character.charCodeAt(0) - 64;
      }

      const row = Number(match[2]) - 1;
      column -= 1;

      return grid.querySelector(
        `.cell[data-r="${row}"][data-c="${column}"]`
      );
    }

    function markTarget() {
      const target = findCell(state.targetReference);
      state.targetCell = target;

      if (target) target.classList.add(TARGET_CLASS);
    }

    function markRange(range, colorIndex) {
      const colorClass =
        'formula-reference-color-' +
        ((colorIndex % COLOR_COUNT) + 1);

      grid.querySelectorAll('.cell').forEach(function (cell) {
        const point = cellCoordinates(cell);
        if (!point) return;

        if (
          point.r >= range.r1 &&
          point.r <= range.r2 &&
          point.c >= range.c1 &&
          point.c <= range.c2
        ) {
          cell.classList.add(
            REFERENCE_CLASS,
            colorClass
          );
          cell.dataset.formulaReference =
            formatRange(
              { r: range.r1, c: range.c1 },
              { r: range.r2, c: range.c2 }
            );
        }
      });
    }

    function renderReferences(activeRange, activeColor) {
      clearVisualReferences();
      markTarget();

      state.references.forEach(function (entry) {
        markRange(entry.range, entry.colorIndex);
      });

      if (activeRange) {
        markRange(activeRange, activeColor);
      }
    }

    function formulaIsEditing() {
      const editor = formulaEditor();

      return (
        String(formula.value || '').startsWith('=') &&
        (
          state.active ||
          doc.activeElement === formula ||
          Boolean(editor && editor.isActive())
        )
      );
    }

    function beginMode() {
      if (!String(formula.value || '').startsWith('=')) {
        return false;
      }

      if (!state.active) {
        state.active = true;
        state.targetReference =
          String(nameBox.value || 'A1').toUpperCase();
        state.references = [];
        state.nextAdditive = false;
        doc.body.dataset.formulaReferenceMode = 'active';
        if (addRange) addRange.hidden = false;
        markTarget();
      }

      setStatus(
        'Select a cell or drag a range. Hold Ctrl or Command, or use + Range, for another reference.'
      );

      return true;
    }

    function endMode(message) {
      state.active = false;
      state.drag = null;
      state.nextAdditive = false;
      state.references = [];
      clearVisualReferences();
      delete doc.body.dataset.formulaReferenceMode;
      if (addRange) addRange.hidden = true;
      setStatus(message || '');
    }

    function setFormulaResult(result) {
      const editor = formulaEditor();

      if (
        editor &&
        editor.isActive() &&
        typeof editor.setValueFromReference === 'function'
      ) {
        editor.setValueFromReference(result);
        return;
      }

      formula.value = result.value;
      formula.focus({ preventScroll: true });
      formula.setSelectionRange(
        result.caret,
        result.caret
      );

      formula.dispatchEvent(
        new global.Event('input', {
          bubbles: true,
          cancelable: false
        })
      );
    }

    function updateDrag(point) {
      if (!state.drag || !point) return;

      state.drag.current = point;
      const range = normalizeRange(
        state.drag.start,
        point
      );
      const reference = formatRange(
        state.drag.start,
        point
      );

      const result = insertReference(
        state.drag.baseValue,
        state.drag.baseStart,
        state.drag.baseEnd,
        reference,
        {
          additive: state.drag.additive,
          autoClose: false
        }
      );

      state.drag.result = result;
      state.drag.range = range;
      setFormulaResult(result);
      renderReferences(range, state.drag.colorIndex);

      setStatus(
        `Reference ${reference} selected for ${state.targetReference}. Release to keep it.`
      );
    }

    function pointFromEventTarget(target) {
      const cell =
        target &&
        typeof target.closest === 'function' &&
        target.closest('.cell');

      return cellCoordinates(cell);
    }

    function beginReference(event) {
      const cell =
        event.target &&
        typeof event.target.closest === 'function' &&
        event.target.closest('.cell');

      if (!cell || !formulaIsEditing()) return;
      if (!beginMode()) return;

      event.preventDefault();
      event.stopImmediatePropagation();

      if (suggestions) suggestions.hidden = true;

      const point = cellCoordinates(cell);
      if (!point) return;

      const additive =
        event.ctrlKey ||
        event.metaKey ||
        state.nextAdditive;

      state.nextAdditive = false;

      const editor = formulaEditor();
      const editorSelection =
        editor &&
        editor.isActive() &&
        typeof editor.getSelection === 'function'
          ? editor.getSelection()
          : null;

      let start = editorSelection
        ? editorSelection.start
        : formula.selectionStart;

      let end = editorSelection
        ? editorSelection.end
        : formula.selectionEnd;

      if (
        !Number.isFinite(start) ||
        !Number.isFinite(end)
      ) {
        start = end = formula.value.length;
      }

      state.drag = {
        pointerId: event.pointerId,
        start: point,
        current: point,
        baseValue: formula.value,
        baseStart: start,
        baseEnd: end,
        additive,
        colorIndex: state.colorIndex % COLOR_COUNT,
        range: normalizeRange(point, point),
        result: null
      };

      updateDrag(point);

      if (
        typeof cell.setPointerCapture === 'function' &&
        event.pointerId !== undefined
      ) {
        try {
          cell.setPointerCapture(event.pointerId);
        } catch (error) {
          /* Window capture listeners continue the drag. */
        }
      }
    }

    function pointerPoint(event) {
      const direct = pointFromEventTarget(event.target);
      if (direct) return direct;

      if (
        doc.elementFromPoint &&
        Number.isFinite(event.clientX) &&
        Number.isFinite(event.clientY)
      ) {
        return pointFromEventTarget(
          doc.elementFromPoint(
            event.clientX,
            event.clientY
          )
        );
      }

      return null;
    }

    function moveReference(event) {
      if (!state.drag) return;

      if (
        state.drag.pointerId !== undefined &&
        event.pointerId !== undefined &&
        state.drag.pointerId !== event.pointerId
      ) {
        return;
      }

      state.pendingPointer = pointerPoint(event);
      if (!state.pendingPointer) return;

      if (state.pointerFrame) return;

      const render = function () {
        state.pointerFrame = 0;
        const point = state.pendingPointer;
        state.pendingPointer = null;
        updateDrag(point);
      };

      state.pointerFrame = global.requestAnimationFrame
        ? global.requestAnimationFrame(render)
        : global.setTimeout(render, 0);

      event.preventDefault();
      event.stopImmediatePropagation();
    }

    function finishReference(event) {
      if (!state.drag) return;

      if (
        state.drag.pointerId !== undefined &&
        event.pointerId !== undefined &&
        state.drag.pointerId !== event.pointerId
      ) {
        return;
      }

      event.preventDefault();
      event.stopImmediatePropagation();

      const finished = state.drag;
      state.drag = null;

      if (!finished.additive) {
        state.references = [];
      }

      state.references.push({
        range: finished.range,
        colorIndex: finished.colorIndex
      });

      state.colorIndex =
        (finished.colorIndex + 1) % COLOR_COUNT;

      renderReferences();

      const editor = formulaEditor();
      if (editor && editor.isActive()) {
        editor.focus();
      } else {
        formula.focus({ preventScroll: true });
      }

      const reference = formatRange(
        { r: finished.range.r1, c: finished.range.c1 },
        { r: finished.range.r2, c: finished.range.c2 }
      );

      setStatus(
        `${reference} added. Press Enter to confirm, Escape to cancel, or add another range.`
      );
    }

    function syncFormulaMode() {
      if (String(formula.value || '').startsWith('=')) {
        beginMode();
      } else if (state.active) {
        endMode('');
      }
    }

    formula.addEventListener('focus', syncFormulaMode);
    formula.addEventListener('input', syncFormulaMode);

    formula.addEventListener(
      'keydown',
      function (event) {
        if (event.key === 'Escape') {
          global.setTimeout(function () {
            endMode('');
          }, 0);
        } else if (event.key === 'Enter') {
          global.setTimeout(function () {
            endMode('Formula confirmed.');
          }, 0);
        }
      },
      true
    );

    grid.addEventListener(
      'pointerdown',
      beginReference,
      true
    );

    global.addEventListener(
      'pointermove',
      moveReference,
      true
    );

    global.addEventListener(
      'pointerup',
      finishReference,
      true
    );

    global.addEventListener(
      'pointercancel',
      finishReference,
      true
    );

    if (addRange) {
      addRange.addEventListener(
        'pointerdown',
        function (event) {
          event.preventDefault();
        }
      );

      addRange.addEventListener(
        'click',
        function () {
          if (!beginMode()) return;
          state.nextAdditive = true;

          const editor = formulaEditor();
          if (editor && editor.isActive()) {
            editor.focus();
          } else {
            formula.focus({ preventScroll: true });
          }

          setStatus(
            'Add-range mode: select another cell or drag another range.'
          );
        }
      );
    }

    viewport.addEventListener(
      'scroll',
      function () {
        if (state.active) renderReferences();
      },
      { passive: true }
    );

    const controller = Object.freeze({
      version: VERSION,
      state,
      begin: beginMode,
      end: endMode,
      insertReference,
      normalizeRange,
      formatRange
    });

    Object.defineProperty(
      formula,
      '__inkdeskFormulaReferenceController',
      {
        value: controller,
        configurable: true
      }
    );

    global.InkDeskSpreadsheetFormulaReferences =
      controller;

    return controller;
  }

  const api = Object.freeze({
    version: VERSION,
    encodeColumn,
    encodeCell,
    normalizeRange,
    formatRange,
    unmatchedParentheses,
    insertReference,
    cellCoordinates,
    createController
  });

  global.InkDeskFormulaReferences = api;

  function autoInitialize() {
    createController(global.document);
  }

  if (global.document) {
    if (global.document.readyState === 'loading') {
      global.document.addEventListener(
        'DOMContentLoaded',
        autoInitialize,
        { once: true }
      );
    } else {
      autoInitialize();
    }
  }
})(typeof window !== 'undefined' ? window : globalThis);

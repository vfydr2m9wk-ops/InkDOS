(function (global) {
  'use strict';

  const VERSION = '0.19.4.9';
  const MAX_SUGGESTIONS = 6;

  const FUNCTIONS = Object.freeze([
    ['SUM', 'SUM(number1, [number2], …)', 'Adds numbers and ranges'],
    ['AVERAGE', 'AVERAGE(number1, …)', 'Returns the arithmetic mean'],
    ['COUNT', 'COUNT(value1, …)', 'Counts numeric values'],
    ['COUNTA', 'COUNTA(value1, …)', 'Counts non-empty values'],
    ['MIN', 'MIN(number1, …)', 'Returns the smallest value'],
    ['MAX', 'MAX(number1, …)', 'Returns the largest value'],
    ['MEDIAN', 'MEDIAN(number1, …)', 'Returns the median'],
    ['PRODUCT', 'PRODUCT(number1, …)', 'Multiplies values'],
    ['ABS', 'ABS(number)', 'Returns absolute value'],
    ['ROUND', 'ROUND(number, digits)', 'Rounds a number'],
    ['ROUNDUP', 'ROUNDUP(number, digits)', 'Rounds away from zero'],
    ['ROUNDDOWN', 'ROUNDDOWN(number, digits)', 'Rounds toward zero'],
    ['MOD', 'MOD(number, divisor)', 'Returns the remainder'],
    ['POWER', 'POWER(number, power)', 'Raises to a power'],
    ['IF', 'IF(test, true, false)', 'Conditional result'],
    ['IFERROR', 'IFERROR(value, fallback)', 'Handles formula errors'],
    ['AND', 'AND(logical1, …)', 'TRUE when all are true'],
    ['OR', 'OR(logical1, …)', 'TRUE when any is true'],
    ['NOT', 'NOT(logical)', 'Reverses a logical value'],
    ['XLOOKUP', 'XLOOKUP(value, lookup, return, [missing])', 'Looks up a value'],
    ['FILTER', 'FILTER(array, include, [empty])', 'Filters a range'],
    ['CONCAT', 'CONCAT(text1, …)', 'Joins text'],
    ['LEFT', 'LEFT(text, [count])', 'Takes left characters'],
    ['RIGHT', 'RIGHT(text, [count])', 'Takes right characters'],
    ['MID', 'MID(text, start, count)', 'Takes middle characters'],
    ['LEN', 'LEN(text)', 'Counts characters'],
    ['TRIM', 'TRIM(text)', 'Normalizes spaces'],
    ['UPPER', 'UPPER(text)', 'Uppercase text'],
    ['LOWER', 'LOWER(text)', 'Lowercase text'],
    ['TODAY', 'TODAY()', 'Current local date'],
    ['NOW', 'NOW()', 'Current date and time'],
    ['DAY', 'DAY(date)', 'Day of month'],
    ['MONTH', 'MONTH(date)', 'Month number'],
    ['YEAR', 'YEAR(date)', 'Year number']
  ]);

  const DEFAULT_FUNCTIONS = Object.freeze([
    'SUM',
    'AVERAGE',
    'COUNT',
    'IF',
    'XLOOKUP',
    'TODAY'
  ]);

  function clamp(value, minimum, maximum) {
    return Math.max(
      Number(minimum) || 0,
      Math.min(Number(maximum) || 0, Number(value) || 0)
    );
  }

  function parenthesisDepth(value) {
    let depth = 0;
    let quoted = false;
    const source = String(value || '');

    for (let index = 0; index < source.length; index += 1) {
      const character = source[index];

      if (character === '"') {
        if (quoted && source[index + 1] === '"') {
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

  function balanceFormula(value) {
    const source = String(value || '');
    if (!source.startsWith('=')) return source;

    const missing = parenthesisDepth(source);
    return missing > 0 ? source + ')'.repeat(missing) : source;
  }

  function suggestionContext(value, cursor) {
    const source = String(value || '');
    if (!source.startsWith('=')) return null;

    const position = clamp(
      Number.isFinite(Number(cursor)) ? Number(cursor) : source.length,
      1,
      source.length
    );

    const before = source.slice(0, position);

    if (before === '=') {
      return Object.freeze({
        query: '',
        start: 1,
        end: 1,
        depth: 0,
        root: true
      });
    }

    const match = before.match(/([A-Z][A-Z0-9.]*)$/i);
    if (!match) return null;

    const query = match[1].toUpperCase();
    const start = position - match[1].length;
    const previous = source[start - 1] || '';
    const depth = parenthesisDepth(source.slice(0, start));
    const validBoundary =
      start === 1 ||
      /[=,+\-*/^&<>]/.test(previous) ||
      previous === '(';

    if (!validBoundary) return null;

    /*
     * Inside a function argument, one letter is overwhelmingly more likely
     * to be the beginning of A1/B2/etc. than a nested function. Requiring
     * two letters here prevents A from immediately becoming AVERAGE.
     */
    if (depth > 0 && query.length < 2) return null;

    return Object.freeze({
      query,
      start,
      end: position,
      depth,
      root: start === 1
    });
  }

  function applyFunctionSuggestion(
    value,
    start,
    end,
    functionName
  ) {
    const source = String(value || '');
    const from = clamp(start, 0, source.length);
    const to = clamp(end, from, source.length);
    const insertion = String(functionName || '').toUpperCase() + '(';
    const result =
      source.slice(0, from) +
      insertion +
      source.slice(to);

    return Object.freeze({
      value: result,
      caret: from + insertion.length
    });
  }

  function matchingFunctions(context) {
    if (!context) return [];

    if (!context.query) {
      return DEFAULT_FUNCTIONS
        .map(function (name) {
          return FUNCTIONS.find(function (item) {
            return item[0] === name;
          });
        })
        .filter(Boolean);
    }

    return FUNCTIONS.filter(function (item) {
      return item[0].startsWith(context.query);
    }).slice(0, MAX_SUGGESTIONS);
  }

  function selectedCell(documentObject, grid, nameBox) {
    const selected = grid.querySelector('.cell.selected');
    if (selected) return selected;

    const match = /^\$?([A-Z]{1,3})\$?(\d+)$/i.exec(
      String(nameBox.value || '').trim()
    );

    if (!match) return null;

    let column = 0;
    for (const character of match[1].toUpperCase()) {
      column = column * 26 + character.charCodeAt(0) - 64;
    }

    return grid.querySelector(
      `.cell[data-r="${Number(match[2]) - 1}"]` +
      `[data-c="${column - 1}"]`
    );
  }

  function createController(documentObject) {
    const doc = documentObject || global.document;
    if (!doc || !doc.getElementById) return null;

    const formula = doc.getElementById('formulaInput');
    const suggestions = doc.getElementById('formulaSuggestions');
    const grid = doc.getElementById('grid');
    const viewport = doc.getElementById('gridViewport');
    const nameBox = doc.getElementById('nameBox');
    const status = doc.getElementById('formulaReferenceStatus');

    if (!formula || !suggestions || !grid || !viewport || !nameBox) {
      return null;
    }

    if (formula.__inkdeskFormulaEditorController) {
      return formula.__inkdeskFormulaEditorController;
    }

    const coreHandlers = {
      focus: formula.onfocus,
      input: formula.oninput,
      keydown: formula.onkeydown
    };

    const overlay = doc.createElement('input');
    overlay.id = 'cellFormulaEditor';
    overlay.className = 'cell-formula-editor';
    overlay.type = 'text';
    overlay.autocomplete = 'off';
    overlay.spellcheck = false;
    overlay.setAttribute('aria-label', 'Edit formula in selected cell');
    overlay.hidden = true;
    doc.body.appendChild(overlay);

    const state = {
      active: false,
      cell: null,
      suggestionIndex: 0,
      suggestionItems: [],
      suggestionContext: null,
      syncing: false,
      positionFrame: 0
    };

    function setStatus(message) {
      if (!status) return;
      status.hidden = !message;
      status.textContent = String(message || '');
    }

    function currentInput() {
      return state.active ? overlay : formula;
    }

    function currentValue() {
      return String(currentInput().value || '');
    }

    function currentSelection() {
      const input = currentInput();
      const fallback = String(input.value || '').length;

      return Object.freeze({
        start: Number.isFinite(input.selectionStart)
          ? input.selectionStart
          : fallback,
        end: Number.isFinite(input.selectionEnd)
          ? input.selectionEnd
          : fallback
      });
    }

    function closeSuggestions() {
      suggestions.hidden = true;
      suggestions.replaceChildren();
      suggestions.classList.remove(
        'formula-suggestions-cell',
        'formula-suggestions-bar'
      );
      state.suggestionItems = [];
      state.suggestionContext = null;
      state.suggestionIndex = 0;
    }

    function positionSuggestions() {
      if (suggestions.hidden) return;

      const input = currentInput();
      const rect = input.getBoundingClientRect();
      const viewportWidth =
        doc.documentElement.clientWidth ||
        global.innerWidth ||
        1024;

      const width = Math.min(
        Math.max(rect.width, 340),
        Math.max(260, viewportWidth - 24)
      );

      const left = clamp(
        rect.left,
        8,
        Math.max(8, viewportWidth - width - 8)
      );

      suggestions.style.left = left + 'px';
      suggestions.style.top = (rect.bottom + 4) + 'px';
      suggestions.style.width = width + 'px';
    }

    function renderSuggestions() {
      const input = currentInput();
      const selection = currentSelection();
      const context = suggestionContext(
        input.value,
        selection.start
      );

      const items = matchingFunctions(context);

      if (!context || !items.length) {
        closeSuggestions();
        return;
      }

      state.suggestionContext = context;
      state.suggestionItems = items;
      state.suggestionIndex = clamp(
        state.suggestionIndex,
        0,
        items.length - 1
      );

      suggestions.replaceChildren();
      suggestions.classList.toggle(
        'formula-suggestions-cell',
        state.active
      );
      suggestions.classList.toggle(
        'formula-suggestions-bar',
        !state.active
      );

      items.forEach(function (item, index) {
        const button = doc.createElement('button');
        button.type = 'button';
        button.className =
          'formula-suggestion' +
          (index === state.suggestionIndex ? ' active' : '');
        button.setAttribute('role', 'option');
        button.setAttribute(
          'aria-selected',
          index === state.suggestionIndex ? 'true' : 'false'
        );

        const name = doc.createElement('strong');
        name.textContent = item[0];

        const details = doc.createElement('span');
        details.textContent = item[1] + ' · ' + item[2];

        button.append(name, details);

        button.addEventListener(
          'pointerdown',
          function (event) {
            event.preventDefault();
          }
        );

        button.addEventListener(
          'click',
          function () {
            acceptSuggestion(index);
          }
        );

        suggestions.appendChild(button);
      });

      suggestions.hidden = false;
      positionSuggestions();
    }

    function dispatchFormulaInput() {
      formula.dispatchEvent(
        new global.Event('input', {
          bubbles: true,
          cancelable: false
        })
      );
    }

    function setValue(value, caret, options) {
      const settings = options || {};
      const source = String(value || '');
      const position = clamp(
        Number.isFinite(Number(caret)) ? Number(caret) : source.length,
        0,
        source.length
      );

      state.syncing = true;
      formula.value = source;
      formula.setSelectionRange(position, position);

      if (state.active) {
        overlay.value = source;
        overlay.setSelectionRange(position, position);
      }

      if (settings.dispatch !== false) {
        dispatchFormulaInput();
      }

      state.syncing = false;
      state.suggestionIndex = 0;

      if (settings.suggestions !== false) {
        renderSuggestions();
      } else {
        closeSuggestions();
      }
    }

    function acceptSuggestion(index) {
      const context = state.suggestionContext;
      const item = state.suggestionItems[index];

      if (!context || !item) return false;

      const result = applyFunctionSuggestion(
        currentValue(),
        context.start,
        context.end,
        item[0]
      );

      setValue(
        result.value,
        result.caret,
        {
          dispatch: true,
          suggestions: true
        }
      );

      currentInput().focus({ preventScroll: true });
      closeSuggestions();

      setStatus(
        item[0] +
        ' inserted. Select cells or type arguments; Enter confirms.'
      );

      return true;
    }

    function positionOverlay() {
      if (!state.active || !state.cell) return;

      const rect = state.cell.getBoundingClientRect();
      const viewportWidth =
        doc.documentElement.clientWidth ||
        global.innerWidth ||
        1024;

      const width = Math.min(
        Math.max(rect.width, 220),
        Math.max(220, viewportWidth - rect.left - 12),
        520
      );

      overlay.style.left = rect.left + 'px';
      overlay.style.top = rect.top + 'px';
      overlay.style.width = width + 'px';
      overlay.style.height = Math.max(rect.height, 28) + 'px';

      positionSuggestions();
    }

    function schedulePosition() {
      if (!state.active || state.positionFrame) return;

      const render = function () {
        state.positionFrame = 0;
        positionOverlay();
      };

      state.positionFrame = global.requestAnimationFrame
        ? global.requestAnimationFrame(render)
        : global.setTimeout(render, 0);
    }

    function openCellEditor(cell, initialValue, caret) {
      if (!cell) return false;

      state.active = true;
      state.cell = cell;
      doc.body.dataset.formulaEditorMode = 'cell';

      overlay.hidden = false;
      overlay.value = String(initialValue || '');
      positionOverlay();

      const position = clamp(
        Number.isFinite(Number(caret))
          ? Number(caret)
          : overlay.value.length,
        0,
        overlay.value.length
      );

      setValue(
        overlay.value,
        position,
        {
          dispatch: true,
          suggestions: false
        }
      );

      overlay.focus({ preventScroll: true });
      overlay.setSelectionRange(position, position);
      renderSuggestions();

      setStatus(
        'Editing ' +
        String(nameBox.value || '') +
        ' in the cell. Tab accepts a function; Enter confirms.'
      );

      return true;
    }

    function closeOverlay() {
      state.active = false;
      state.cell = null;
      overlay.hidden = true;
      delete doc.body.dataset.formulaEditorMode;
      closeSuggestions();
    }

    function callCoreKeydown(key) {
      if (typeof coreHandlers.keydown !== 'function') return false;

      let prevented = false;

      coreHandlers.keydown.call(formula, {
        key,
        shiftKey: false,
        preventDefault: function () {
          prevented = true;
        },
        stopPropagation: function () {},
        stopImmediatePropagation: function () {}
      });

      return prevented;
    }

    function commit() {
      const balanced = balanceFormula(currentValue());

      setValue(
        balanced,
        balanced.length,
        {
          dispatch: true,
          suggestions: false
        }
      );

      closeSuggestions();
      callCoreKeydown('Enter');

      const references =
        global.InkDeskSpreadsheetFormulaReferences;

      if (references && typeof references.end === 'function') {
        references.end('Formula confirmed.');
      }

      closeOverlay();
      setStatus('Formula confirmed.');
      return balanced;
    }

    function cancel() {
      closeSuggestions();
      callCoreKeydown('Escape');

      const references =
        global.InkDeskSpreadsheetFormulaReferences;

      if (references && typeof references.end === 'function') {
        references.end('');
      }

      closeOverlay();
      setStatus('');
    }

    function handleEditingKeydown(event) {
      if (
        !suggestions.hidden &&
        (event.key === 'ArrowDown' || event.key === 'ArrowUp')
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();

        const direction = event.key === 'ArrowDown' ? 1 : -1;
        state.suggestionIndex =
          (
            state.suggestionIndex +
            direction +
            state.suggestionItems.length
          ) % state.suggestionItems.length;

        renderSuggestions();
        return;
      }

      if (
        event.key === 'Tab' &&
        !suggestions.hidden &&
        state.suggestionItems.length
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
        acceptSuggestion(state.suggestionIndex);
        return;
      }

      /*
       * Enter never accepts a suggestion. It always confirms the formula,
       * which prevents A in A1 from turning into AVERAGE on confirmation.
       */
      if (event.key === 'Enter') {
        event.preventDefault();
        event.stopImmediatePropagation();
        commit();
        return;
      }

      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopImmediatePropagation();

        if (!suggestions.hidden) {
          closeSuggestions();
          setStatus(
            'Suggestions closed. Press Escape again to cancel editing.'
          );
        } else {
          cancel();
        }
      }
    }

    overlay.addEventListener('input', function () {
      if (state.syncing) return;

      const caret = Number.isFinite(overlay.selectionStart)
        ? overlay.selectionStart
        : overlay.value.length;

      setValue(
        overlay.value,
        caret,
        {
          dispatch: true,
          suggestions: true
        }
      );
    });

    overlay.addEventListener(
      'keydown',
      handleEditingKeydown,
      true
    );

    formula.onfocus = function (event) {
      if (typeof coreHandlers.focus === 'function') {
        coreHandlers.focus.call(formula, event);
      }

      if (state.active) return;

      closeSuggestions();
      state.suggestionIndex = 0;
      renderSuggestions();

      setStatus(
        'Formula bar ready. Tab accepts a function; Enter confirms the formula.'
      );
    };

    formula.oninput = function () {
      if (state.syncing) return;

      if (state.active) {
        overlay.value = formula.value;
        const caret = Number.isFinite(formula.selectionStart)
          ? formula.selectionStart
          : formula.value.length;
        overlay.setSelectionRange(caret, caret);
      }

      state.suggestionIndex = 0;
      renderSuggestions();
    };

    formula.onkeydown = handleEditingKeydown;

    formula.addEventListener(
      'pointerdown',
      function () {
        if (!state.active) return;

        const value = overlay.value;
        const caret = Number.isFinite(overlay.selectionStart)
          ? overlay.selectionStart
          : value.length;

        closeOverlay();
        formula.value = value;
        formula.setSelectionRange(caret, caret);
      },
      true
    );

    global.addEventListener(
      'keydown',
      function (event) {
        const target = event.target;

        if (
          target === formula ||
          target === overlay ||
          target?.matches?.(
            'input,textarea,select,button,[contenteditable="true"]'
          )
        ) {
          return;
        }

        const cell = selectedCell(doc, grid, nameBox);
        if (!cell) return;

        if (
          event.key === '=' &&
          !event.ctrlKey &&
          !event.metaKey &&
          !event.altKey
        ) {
          event.preventDefault();
          event.stopImmediatePropagation();
          openCellEditor(cell, '=', 1);
          return;
        }

        if (event.key === 'F2') {
          event.preventDefault();
          event.stopImmediatePropagation();

          const value = String(formula.value || cell.textContent || '');
          openCellEditor(cell, value, value.length);
        }
      },
      true
    );

    global.addEventListener(
      'dblclick',
      function (event) {
        const cell =
          event.target &&
          typeof event.target.closest === 'function' &&
          event.target.closest('.cell');

        if (!cell || !grid.contains(cell)) return;

        event.preventDefault();
        event.stopImmediatePropagation();

        const value = String(formula.value || cell.textContent || '');
        openCellEditor(cell, value, value.length);
      },
      true
    );

    viewport.addEventListener(
      'scroll',
      schedulePosition,
      { passive: true }
    );

    global.addEventListener('resize', schedulePosition);

    const controller = Object.freeze({
      version: VERSION,
      isActive: function () {
        return state.active;
      },
      hasSuggestions: function () {
        return !suggestions.hidden;
      },
      getValue: currentValue,
      getSelection: currentSelection,
      open: openCellEditor,
      close: closeOverlay,
      focus: function () {
        currentInput().focus({ preventScroll: true });
      },
      setValueFromReference: function (result) {
        if (!result) return;

        setValue(
          result.value,
          result.caret,
          {
            dispatch: true,
            suggestions: false
          }
        );

        currentInput().focus({ preventScroll: true });
      },
      commit,
      cancel
    });

    Object.defineProperty(
      formula,
      '__inkdeskFormulaEditorController',
      {
        value: controller,
        configurable: true
      }
    );

    global.InkDeskSpreadsheetFormulaEditor = controller;
    return controller;
  }

  const api = Object.freeze({
    version: VERSION,
    functions: FUNCTIONS,
    parenthesisDepth,
    balanceFormula,
    suggestionContext,
    applyFunctionSuggestion,
    matchingFunctions,
    createController
  });

  global.InkDeskFormulaEditor = api;

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

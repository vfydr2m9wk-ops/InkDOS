(function (global) {
  'use strict';
  const VERSION = '0.20.0';
  const DRAFT_CLASS = 'formula-draft-editing';
  const SAVED_DRAFT_CLASS = 'has-formula-draft';
  const FormulaModel = global.InkDeskSpreadsheetFormulaModel || (
    typeof module === 'object' && module.exports && typeof require === 'function'
      ? require('./formula-model.js')
      : null
  );
  const FormulaSession = global.InkDeskSpreadsheetFormulaSession || (
    typeof module === 'object' && module.exports && typeof require === 'function'
      ? require('./formula-session.js')
      : null
  );
  if (!FormulaModel || !FormulaSession) {
    if (global.console && typeof global.console.error === 'function') {
      global.console.error('InkDesk spreadsheet formula model/session is unavailable.');
    }
    return;
  }
  const {
    functions: FUNCTIONS,
    clamp,
    encodeColumn,
    cellReference,
    parenthesisDepth,
    balanceFormula,
    suggestionContext,
    matchingFunctions,
    applyFunctionSuggestion,
    formulaCanSelectReference,
    shouldAppendReference,
    formulaIsComplete
  } = FormulaModel;
  function caretOffset(element) {
    const selection = global.getSelection && global.getSelection();
    if (!selection || !selection.rangeCount || !element.contains(selection.anchorNode)) {
      return String(element.textContent || '').length;
    }
    const range = selection.getRangeAt(0).cloneRange();
    range.selectNodeContents(element);
    range.setEnd(selection.anchorNode, selection.anchorOffset);
    return range.toString().length;
  }
  function setCaret(element, offset) {
    const selection = global.getSelection && global.getSelection();
    if (!selection || !global.document.createRange) return;
    const target = clamp(offset, 0, String(element.textContent || '').length);
    const walker = global.document.createTreeWalker(
      element,
      global.NodeFilter ? global.NodeFilter.SHOW_TEXT : 4
    );
    let remaining = target;
    let node = walker.nextNode();
    while (node) {
      const length = node.nodeValue.length;
      if (remaining <= length) {
        const range = global.document.createRange();
        range.setStart(node, remaining);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
        return;
      }
      remaining -= length;
      node = walker.nextNode();
    }
    const range = global.document.createRange();
    range.selectNodeContents(element);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
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
    const tabs = doc.getElementById('sheetTabs');
    if (!formula || !suggestions || !grid || !viewport || !nameBox) return null;
    if (formula.__inkdeskFormulaEditorController) {
      return formula.__inkdeskFormulaEditorController;
    }
    const coreHandlers = {
      focus: formula.onfocus,
      input: formula.oninput,
      keydown: formula.onkeydown
    };
    const session = FormulaSession.createSession({ clamp });
    const drafts = session.drafts;
    const state = session.state;
    const suggestionState = { items: [], index: 0, context: null };
    let syncing = false;
    let resumeTimer = 0;
    function activeSheetName() {
      return (
        tabs && tabs.querySelector('button.active')?.textContent?.trim()
      ) || 'Sheet';
    }
    function keyFor(reference) {
      return activeSheetName() + '!' + String(reference || '').toUpperCase();
    }
    function selectedCell() {
      return grid.querySelector('.cell.selected');
    }
    function setStatus(message) {
      if (!status) return;
      status.hidden = !message;
      status.textContent = String(message || '');
    }
    function closeSuggestions() {
      suggestions.hidden = true;
      suggestions.replaceChildren();
      suggestionState.items = [];
      suggestionState.index = 0;
      suggestionState.context = null;
    }

    function positionSuggestions() {
      if (suggestions.hidden) return;
      const rect = formula.getBoundingClientRect();
      const viewportWidth = doc.documentElement.clientWidth || global.innerWidth || 1024;
      const width = Math.min(Math.max(rect.width, 320), Math.max(260, viewportWidth - 24), 520);
      suggestions.style.position = 'fixed';
      suggestions.style.left = clamp(rect.left, 8, Math.max(8, viewportWidth - width - 8)) + 'px';
      suggestions.style.top = rect.bottom + 3 + 'px';
      suggestions.style.width = width + 'px';
    }

    function renderSuggestions() {
      const context = suggestionContext(state.value, state.caret);
      const items = matchingFunctions(context);
      if (!context || !items.length) {
        closeSuggestions();
        return;
      }
      suggestionState.context = context;
      suggestionState.items = items;
      suggestionState.index = clamp(suggestionState.index, 0, items.length - 1);
      suggestions.replaceChildren();
      items.forEach(function (item, index) {
        const button = doc.createElement('button');
        button.type = 'button';
        button.className = 'formula-suggestion' + (index === suggestionState.index ? ' active' : '');
        button.setAttribute('role', 'option');
        button.setAttribute('aria-selected', index === suggestionState.index ? 'true' : 'false');
        const name = doc.createElement('strong');
        name.textContent = item[0];
        const detail = doc.createElement('span');
        detail.textContent = item[1] + ' · ' + item[2];
        button.append(name, detail);
        button.addEventListener('pointerdown', function (event) {
          event.preventDefault();
        });
        button.addEventListener('click', function () {
          acceptSuggestion(index);
        });
        suggestions.appendChild(button);
      });
      suggestions.hidden = false;
      positionSuggestions();
    }

    function rememberDraft() {
      session.rememberDraft();
    }

    function updateCellText(value, caret) {
      if (!state.cell) return;
      state.cell.textContent = value;
      state.cell.dataset.formulaDraft = value;
      state.cell.classList.add(SAVED_DRAFT_CLASS);
      if (state.active && doc.activeElement === state.cell) setCaret(state.cell, caret);
    }

    function mirrorFormula(value, caret, dispatch) {
      syncing = true;
      formula.value = value;
      formula.setSelectionRange(caret, caret);
      if (dispatch) {
        formula.dispatchEvent(new global.Event('input', { bubbles: true, cancelable: false }));
      }
      syncing = false;
    }

    function setDraftValue(value, caret, options) {
      const settings = options || {};
      session.update(value, caret);
      updateCellText(state.value, state.caret);
      mirrorFormula(state.value, state.caret, settings.dispatch === true);
      rememberDraft();
      suggestionState.index = 0;
      if (settings.suggestions === false) closeSuggestions();
      else renderSuggestions();
      doc.dispatchEvent(new global.CustomEvent('inkdesk:formula-session-change', {
        detail: {
          value: state.value,
          caret: state.caret,
          targetReference: state.targetReference
        }
      }));
    }

    function referenceController() {
      return global.InkDeskSpreadsheetFormulaReferences || null;
    }

    function beginReferenceMode() {
      const controller = referenceController();
      if (controller && typeof controller.begin === 'function') {
        controller.begin(state.targetReference);
      }
    }

    function start(cell, value, caret) {
      if (!cell) return false;
      if (state.active && state.cell !== cell) suspend();
      const reference = cellReference(cell) || String(nameBox.value || '').toUpperCase();
      const opened = session.start({
        cell,
        reference,
        key: keyFor(reference),
        value,
        caret,
        originalDisplay: cell.textContent,
        originalFormulaValue: formula.value
      });
      if (!opened) return false;
      doc.body.dataset.formulaEditorMode = 'cell-session';
      cell.contentEditable = 'true';
      cell.spellcheck = false;
      cell.classList.add(DRAFT_CLASS, SAVED_DRAFT_CLASS);
      cell.dataset.formulaDraft = opened.value;
      cell.textContent = opened.value;
      mirrorFormula(opened.value, opened.caret, false);
      cell.focus({ preventScroll: true });
      setCaret(cell, opened.caret);
      renderSuggestions();
      beginReferenceMode();
      setStatus('Draft ' + reference + ' is preserved. Type in the cell; Tab accepts a function and Enter confirms.');
      return true;
    }

    function suspend() {
      const suspended = session.suspend();
      if (!suspended) return;
      closeSuggestions();
      if (suspended.cell) {
        suspended.cell.contentEditable = 'false';
        suspended.cell.classList.remove(DRAFT_CLASS);
        suspended.cell.classList.add(SAVED_DRAFT_CLASS);
        suspended.cell.dataset.formulaDraft = suspended.value;
        suspended.cell.textContent = suspended.value;
      }
      delete doc.body.dataset.formulaEditorMode;
      const controller = referenceController();
      if (controller && typeof controller.pause === 'function') controller.pause();
      setStatus('Formula draft preserved. Return to its cell to continue.');
    }

    function clearActiveState() {
      closeSuggestions();
      const cleared = session.clearActive();
      if (cleared.cell) {
        cleared.cell.contentEditable = 'false';
        cleared.cell.classList.remove(DRAFT_CLASS, SAVED_DRAFT_CLASS);
        delete cleared.cell.dataset.formulaDraft;
      }
      delete doc.body.dataset.formulaEditorMode;
    }

    function callCoreKeydown(key) {
      if (typeof coreHandlers.keydown !== 'function') return;
      coreHandlers.keydown.call(formula, {
        key,
        shiftKey: false,
        preventDefault: function () {},
        stopPropagation: function () {},
        stopImmediatePropagation: function () {}
      });
    }

    function commit() {
      const prepared = session.prepareCommit(balanceFormula);
      if (!prepared) return false;
      mirrorFormula(prepared.value, prepared.caret, false);
      if (prepared.cell) {
        prepared.cell.contentEditable = 'false';
        prepared.cell.classList.remove(DRAFT_CLASS);
      }
      callCoreKeydown('Enter');
      const controller = referenceController();
      if (controller && typeof controller.end === 'function') controller.end('Formula confirmed.');
      clearActiveState();
      setStatus('Formula confirmed.');
      return true;
    }

    function cancel() {
      const prepared = session.prepareCancel();
      if (!prepared) return;
      if (prepared.cell) prepared.cell.textContent = prepared.originalDisplay;
      callCoreKeydown('Escape');
      const controller = referenceController();
      if (controller && typeof controller.end === 'function') controller.end('');
      clearActiveState();
      setStatus('');
    }

    function reset() {
      closeSuggestions();
      session.reset();
      delete doc.body.dataset.formulaEditorMode;
      const controller = referenceController();
      if (controller && typeof controller.end === 'function') controller.end('');
      setStatus('');
      return true;
    }

    function acceptSuggestion(index) {
      const context = suggestionState.context;
      const item = suggestionState.items[index];
      if (!context || !item || !state.active) return false;
      const result = applyFunctionSuggestion(
        state.value,
        context.start,
        context.end,
        item[0]
      );
      setDraftValue(result.value, result.caret, { dispatch: false, suggestions: false });
      state.cell.focus({ preventScroll: true });
      setCaret(state.cell, result.caret);
      beginReferenceMode();
      setStatus(item[0] + ' inserted. Click or drag cells, type arguments, or press Enter to confirm.');
      return true;
    }

    function handleEditingKeydown(event) {
      if (!state.active) return;
      if (!suggestions.hidden && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
        event.preventDefault();
        event.stopImmediatePropagation();
        const direction = event.key === 'ArrowDown' ? 1 : -1;
        suggestionState.index = (
          suggestionState.index + direction + suggestionState.items.length
        ) % suggestionState.items.length;
        renderSuggestions();
        return;
      }
      if (event.key === 'Tab' && !suggestions.hidden && suggestionState.items.length) {
        event.preventDefault();
        event.stopImmediatePropagation();
        acceptSuggestion(suggestionState.index);
        return;
      }
      if (event.key === 'Enter' && !event.shiftKey) {
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
          setStatus('Suggestions closed. Press Escape again to cancel the draft.');
        } else {
          cancel();
        }
      }
    }

    function applyReference(result) {
      if (!state.active || !result) return;
      setDraftValue(result.value, result.caret, { dispatch: false, suggestions: false });
      state.cell.focus({ preventScroll: true });
      setCaret(state.cell, result.caret);
    }

    function resumeDraftAfterCoreSelection(cell) {
      clearTimeout(resumeTimer);
      resumeTimer = global.setTimeout(function () {
        const reference = cellReference(cell);
        const saved = session.savedFor(keyFor(reference));
        if (saved) start(cell, saved.value, saved.caret);
      }, 0);
    }

    function reapplyDrafts() {
      grid.querySelectorAll('.cell').forEach(function (cell) {
        if (state.active && cell === state.cell) return;
        const reference = cellReference(cell);
        const saved = session.savedFor(keyFor(reference));
        if (saved) {
          cell.textContent = saved.value;
          cell.dataset.formulaDraft = saved.value;
          cell.classList.add(SAVED_DRAFT_CLASS);
        } else {
          cell.classList.remove(SAVED_DRAFT_CLASS);
          delete cell.dataset.formulaDraft;
        }
      });
    }

    grid.addEventListener('input', function (event) {
      if (!state.active || event.target !== state.cell) return;
      const value = String(state.cell.innerText || '').replace(/[\r\n]+/g, '');
      const caret = caretOffset(state.cell);
      session.update(value, caret);
      mirrorFormula(state.value, state.caret, false);
      suggestionState.index = 0;
      renderSuggestions();
      beginReferenceMode();
    }, true);

    grid.addEventListener('keydown', function (event) {
      if (state.active && event.target === state.cell) handleEditingKeydown(event);
    }, true);

    grid.addEventListener('pointerdown', function (event) {
      const cell = event.target?.closest?.('.cell');
      if (!cell) return;
      const reference = cellReference(cell);
      const saved = session.savedFor(keyFor(reference));
      if (state.active && cell !== state.cell) {
        if (formulaCanSelectReference(state.value, state.caret)) return;
        if (formulaIsComplete(state.value)) commit();
        else suspend();
      }
      if (!state.active && saved) resumeDraftAfterCoreSelection(cell);
    }, true);

    formula.onfocus = function (event) {
      if (!state.active && typeof coreHandlers.focus === 'function') {
        coreHandlers.focus.call(formula, event);
      }
      if (!state.active && String(formula.value || '').startsWith('=')) {
        const cell = selectedCell();
        if (cell) start(cell, formula.value, formula.selectionStart ?? formula.value.length);
      } else if (state.active) {
        mirrorFormula(state.value, state.caret, false);
        renderSuggestions();
      }
    };

    formula.oninput = function () {
      if (syncing) return;
      if (!state.active) {
        if (String(formula.value || '').startsWith('=')) {
          const cell = selectedCell();
          if (cell) start(cell, formula.value, formula.selectionStart ?? formula.value.length);
        } else if (typeof coreHandlers.input === 'function') {
          coreHandlers.input.call(formula);
        }
        return;
      }
      const caret = formula.selectionStart ?? formula.value.length;
      session.update(formula.value, caret);
      updateCellText(state.value, state.caret);
      suggestionState.index = 0;
      renderSuggestions();
      beginReferenceMode();
    };

    formula.onkeydown = function (event) {
      if (state.active) handleEditingKeydown(event);
      else if (typeof coreHandlers.keydown === 'function') coreHandlers.keydown.call(formula, event);
    };

    global.addEventListener('keydown', function (event) {
      const target = event.target;
      if (
        target === formula ||
        target?.matches?.('input,textarea,select,button,[contenteditable="true"]')
      ) return;
      const cell = selectedCell();
      if (!cell) return;
      if (event.key === '=' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        event.stopImmediatePropagation();
        start(cell, '=', 1);
        return;
      }
      if (event.key === 'F2') {
        const reference = cellReference(cell);
        const saved = session.savedFor(keyFor(reference));
        const value = saved?.value || String(formula.value || '');
        if (saved || value.startsWith('=')) {
          event.preventDefault();
          event.stopImmediatePropagation();
          start(cell, value, saved?.caret ?? value.length);
        }
      }
    }, true);

    global.addEventListener('dblclick', function (event) {
      const cell = event.target?.closest?.('.cell');
      if (!cell || !grid.contains(cell)) return;
      const reference = cellReference(cell);
      const saved = session.savedFor(keyFor(reference));
      const value = saved?.value || (cell.classList.contains('selected') ? String(formula.value || '') : '');
      if (!saved && !value.startsWith('=')) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      start(cell, value, saved?.caret ?? value.length);
    }, true);

    global.addEventListener('resize', positionSuggestions);
    viewport.addEventListener('scroll', positionSuggestions, { passive: true });

    if (typeof global.MutationObserver === 'function') {
      new global.MutationObserver(function () {
        global.setTimeout(reapplyDrafts, 0);
      }).observe(grid, { childList: true });
    }

    const controller = Object.freeze({
      version: VERSION,
      drafts,
      session,
      isActive: function () { return state.active; },
      hasPendingDrafts: function () { return session.hasDrafts(); },
      getValue: function () { return state.value; },
      getSelection: function () { return { start: state.caret, end: state.caret }; },
      getTargetReference: function () { return state.targetReference; },
      canSelectReference: function () { return state.active && formulaCanSelectReference(state.value, state.caret); },
      shouldAppendReference: function () { return state.active && shouldAppendReference(state.value, state.caret); },
      applyReference,
      focus: function () {
        if (state.cell) {
          state.cell.focus({ preventScroll: true });
          setCaret(state.cell, state.caret);
        }
      },
      start,
      suspend,
      commit,
      cancel,
      reset,
      formulaIsComplete: function () { return formulaIsComplete(state.value); }
    });

    Object.defineProperty(formula, '__inkdeskFormulaEditorController', {
      value: controller,
      configurable: true
    });
    global.InkDeskSpreadsheetFormulaEditor = controller;
    return controller;
  }

  const api = Object.freeze({
    version: VERSION,
    functions: FUNCTIONS,
    encodeColumn,
    cellReference,
    parenthesisDepth,
    balanceFormula,
    suggestionContext,
    matchingFunctions,
    applyFunctionSuggestion,
    formulaCanSelectReference,
    shouldAppendReference,
    formulaIsComplete,
    createController
  });

  global.InkDeskFormulaEditor = api;

  function initialize() {
    createController(global.document);
  }

  if (global.document) {
    if (global.document.readyState === 'loading') {
      global.document.addEventListener('DOMContentLoaded', initialize, { once: true });
    } else {
      initialize();
    }
  }
})(typeof window !== 'undefined' ? window : globalThis);

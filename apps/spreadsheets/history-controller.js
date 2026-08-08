(function (global, factory) {
  'use strict';

  const api = factory();
  global.InkDeskSpreadsheetHistory = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const VERSION = '0.20.2.24';
  const DEFAULT_LIMIT = 80;

  function clone(value) {
    return value == null ? value : JSON.parse(JSON.stringify(value));
  }

  function normalizeSheetIndex(value) {
    const number = Number(value);
    return Number.isFinite(number) && number >= 0 ? Math.floor(number) : 0;
  }

  function normalizeAction(action, sheetIndex) {
    if (!action || typeof action !== 'object') return null;
    const normalized = clone(action);
    normalized.sheetIndex = normalizeSheetIndex(
      sheetIndex === undefined ? normalized.sheetIndex : sheetIndex
    );
    return normalized;
  }

  function create(options) {
    const settings = options || {};
    const limit = Math.max(1, Number(settings.limit) || DEFAULT_LIMIT);
    let undoStack = [];
    let redoStack = [];

    function trim(stack) {
      if (stack.length > limit) stack.splice(0, stack.length - limit);
      return stack;
    }

    function reset() {
      undoStack = [];
      redoStack = [];
    }

    function push(action, sheetIndex) {
      const normalized = normalizeAction(action, sheetIndex);
      if (!normalized) return null;
      undoStack.push(normalized);
      trim(undoStack);
      redoStack = [];
      return clone(normalized);
    }

    function undo() {
      if (!undoStack.length) return null;
      const action = undoStack.pop();
      redoStack.push(action);
      trim(redoStack);
      return clone(action);
    }

    function redo() {
      if (!redoStack.length) return null;
      const action = redoStack.pop();
      undoStack.push(action);
      trim(undoStack);
      return clone(action);
    }

    function exportState() {
      return Object.freeze({
        schemaVersion: 1,
        undo: clone(undoStack),
        redo: clone(redoStack)
      });
    }

    function importState(value) {
      const snapshot = value && typeof value === 'object' ? value : {};
      const normalizeList = (items) => trim(
        (Array.isArray(items) ? items : [])
          .map((item) => normalizeAction(item))
          .filter(Boolean)
      );
      undoStack = normalizeList(snapshot.undo);
      redoStack = normalizeList(snapshot.redo);
      return exportState();
    }

    return Object.freeze({
      version: VERSION,
      reset,
      push,
      undo,
      redo,
      canUndo: function () { return undoStack.length > 0; },
      canRedo: function () { return redoStack.length > 0; },
      exportState,
      importState
    });
  }

  return Object.freeze({
    version: VERSION,
    create,
    normalizeAction,
    normalizeSheetIndex
  });
});

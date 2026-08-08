(function (global, factory) {
  'use strict';

  const api = factory();
  global.InkDeskSpreadsheetFormulaSafety = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const VERSION = '0.20.2.29';

  function create(options) {
    const settings = options || {};
    const editorProvider = typeof settings.editor === 'function'
      ? settings.editor
      : function () { return null; };

    function editor() {
      return editorProvider() || null;
    }

    function hasDrafts() {
      const current = editor();
      return Boolean(
        current &&
        typeof current.hasPendingDrafts === 'function' &&
        current.hasPendingDrafts()
      );
    }

    function hasUnsaved(committedDirty) {
      return Boolean(committedDirty) || hasDrafts();
    }

    function reset() {
      const current = editor();
      if (current && typeof current.reset === 'function') current.reset();
    }

    function guardSave(notify) {
      if (!hasDrafts()) return false;
      if (typeof notify === 'function') {
        notify('Confirm or cancel formula drafts before saving.');
      }
      return true;
    }

    function guardHistory(notify) {
      if (!hasDrafts()) return false;
      if (typeof notify === 'function') {
        notify('Confirm or cancel formula drafts before using Undo or Redo.');
      }
      return true;
    }

    return Object.freeze({
      version: VERSION,
      hasDrafts,
      hasUnsaved,
      reset,
      guardSave,
      guardHistory
    });
  }

  return Object.freeze({ version: VERSION, create });
});

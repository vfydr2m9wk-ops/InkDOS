(function (global, factory) {
  'use strict';

  const api = factory();
  global.InkDeskSpreadsheetFormulaSession = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const VERSION = '0.20.3.0';

  function fallbackClamp(value, minimum, maximum) {
    return Math.max(
      Number(minimum) || 0,
      Math.min(Number(maximum) || 0, Number(value) || 0)
    );
  }

  function normalizeDraft(value) {
    return String(value ?? '').replace(/[\r\n]+/g, '');
  }

  function createSession(options) {
    const settings = options || {};
    const clamp = typeof settings.clamp === 'function' ? settings.clamp : fallbackClamp;
    const drafts = new Map();
    const state = {
      active: false,
      cell: null,
      targetReference: '',
      targetKey: '',
      value: '',
      caret: 0,
      originalDisplay: '',
      originalFormulaValue: ''
    };

    function snapshot() {
      return Object.freeze({
        active: state.active,
        cell: state.cell,
        targetReference: state.targetReference,
        targetKey: state.targetKey,
        value: state.value,
        caret: state.caret,
        originalDisplay: state.originalDisplay,
        originalFormulaValue: state.originalFormulaValue
      });
    }

    function rememberDraft() {
      if (!state.targetKey) return null;
      const draft = {
        value: state.value,
        caret: state.caret,
        reference: state.targetReference
      };
      drafts.set(state.targetKey, draft);
      return draft;
    }

    function savedFor(key) {
      return drafts.get(String(key || '')) || null;
    }

    function start(input) {
      const value = input || {};
      if (!value.cell) return null;
      const reference = String(value.reference || '').toUpperCase();
      const key = String(value.key || reference);
      const saved = savedFor(key);
      const initial = saved ? saved.value : normalizeDraft(value.value);
      const position = saved
        ? saved.caret
        : clamp(value.caret ?? initial.length, 0, initial.length);

      state.active = true;
      state.cell = value.cell;
      state.targetReference = reference;
      state.targetKey = key;
      state.value = initial;
      state.caret = position;
      state.originalDisplay = String(value.originalDisplay ?? '');
      state.originalFormulaValue = String(value.originalFormulaValue ?? '');
      rememberDraft();

      return Object.freeze({
        reference,
        key,
        value: initial,
        caret: position,
        resumed: Boolean(saved)
      });
    }

    function update(value, caret) {
      state.value = normalizeDraft(value);
      state.caret = clamp(caret, 0, state.value.length);
      rememberDraft();
      return snapshot();
    }

    function clearTarget() {
      state.active = false;
      state.cell = null;
      state.targetReference = '';
      state.targetKey = '';
    }

    function suspend() {
      if (!state.active) return null;
      rememberDraft();
      const current = snapshot();
      clearTarget();
      return current;
    }

    function clearActive() {
      const current = snapshot();
      clearTarget();
      return current;
    }

    function prepareCommit(balanceFormula) {
      if (!state.active) return null;
      const balance = typeof balanceFormula === 'function'
        ? balanceFormula
        : function (value) { return String(value || ''); };
      const balanced = balance(state.value);
      state.value = balanced;
      state.caret = balanced.length;
      drafts.delete(state.targetKey);
      return snapshot();
    }

    function prepareCancel() {
      if (!state.active) return null;
      drafts.delete(state.targetKey);
      return snapshot();
    }

    function removeDraft(key) {
      return drafts.delete(String(key || ''));
    }

    function exportDrafts() {
      return Array.from(drafts.entries()).map(function (entry) {
        const key = String(entry[0] || '');
        const draft = entry[1] || {};
        const value = normalizeDraft(draft.value);
        return Object.freeze({
          key,
          reference: String(draft.reference || ''),
          value,
          caret: clamp(draft.caret, 0, value.length)
        });
      });
    }

    function importDrafts(entries) {
      drafts.clear();
      clearTarget();
      state.value = '';
      state.caret = 0;
      state.originalDisplay = '';
      state.originalFormulaValue = '';
      for (const item of Array.isArray(entries) ? entries : []) {
        if (!item || typeof item !== 'object') continue;
        const key = String(item.key || '');
        const reference = String(item.reference || '').toUpperCase();
        if (!key || !reference) continue;
        const value = normalizeDraft(item.value);
        drafts.set(key, {
          value,
          caret: clamp(item.caret, 0, value.length),
          reference
        });
      }
      return exportDrafts();
    }

    function hasDrafts() {
      return drafts.size > 0;
    }

    function reset() {
      const current = snapshot();
      drafts.clear();
      state.active = false;
      state.cell = null;
      state.targetReference = '';
      state.targetKey = '';
      state.value = '';
      state.caret = 0;
      state.originalDisplay = '';
      state.originalFormulaValue = '';
      return current;
    }

    return Object.freeze({
      version: VERSION,
      drafts,
      state,
      normalizeDraft,
      rememberDraft,
      savedFor,
      start,
      update,
      suspend,
      clearActive,
      prepareCommit,
      prepareCancel,
      removeDraft,
      exportDrafts,
      importDrafts,
      hasDrafts,
      reset,
      snapshot
    });
  }

  return Object.freeze({
    version: VERSION,
    normalizeDraft,
    createSession
  });
});

(function (global) {
  'use strict';

  function createHistoryController(options) {
    const editor = options && options.editor;
    const undoButton = options && options.undoButton;
    const redoButton = options && options.redoButton;
    const onRestore = options && options.onRestore;
    const shouldWarnBeforeUnload = options && options.shouldWarnBeforeUnload;
    const markDirty = options && options.markDirty;

    if (!editor || !undoButton || !redoButton) {
      throw new Error('TXT history controller requires editor and history buttons.');
    }

    let history = [];
    let historyIndex = -1;
    let historyTimer = 0;
    let restoringHistory = false;

    function updateButtons() {
      undoButton.disabled = historyIndex <= 0;
      redoButton.disabled =
        historyIndex < 0 || historyIndex >= history.length - 1;
    }

    function snapshot() {
      return {
        value: editor.value,
        start: editor.selectionStart,
        end: editor.selectionEnd
      };
    }

    function reset() {
      clearTimeout(historyTimer);
      history = [snapshot()];
      historyIndex = 0;
      updateButtons();
    }

    function push() {
      if (restoringHistory) return;

      const next = snapshot();
      const current = history[historyIndex];

      if (
        current &&
        current.value === next.value &&
        current.start === next.start &&
        current.end === next.end
      ) {
        return;
      }

      history = history.slice(0, historyIndex + 1);
      history.push(next);

      if (history.length > 80) {
        history.shift();
      } else {
        historyIndex += 1;
      }

      updateButtons();
    }

    function schedule() {
      clearTimeout(historyTimer);
      historyTimer = setTimeout(push, 180);
    }

    function restore(index) {
      if (index < 0 || index >= history.length) return;

      restoringHistory = true;
      historyIndex = index;

      const item = history[index];
      editor.value = item.value;
      editor.setSelectionRange(item.start, item.end);

      if (typeof onRestore === 'function') onRestore();
      updateButtons();

      if (
        typeof shouldWarnBeforeUnload === 'function' &&
        typeof markDirty === 'function' &&
        !shouldWarnBeforeUnload()
      ) {
        markDirty();
      }

      setTimeout(function () {
        restoringHistory = false;
        editor.focus();
      }, 0);
    }

    function undo() {
      restore(historyIndex - 1);
    }

    function redo() {
      restore(historyIndex + 1);
    }

    updateButtons();

    return Object.freeze({
      reset,
      schedule,
      undo,
      redo,
      getState: function () {
        return {
          historyLength: history.length,
          historyIndex,
          restoringHistory
        };
      }
    });
  }

  global.InkDeskTxtHistoryController = Object.freeze({
    version: '0.20.2.24',
    createHistoryController
  });
})(globalThis);

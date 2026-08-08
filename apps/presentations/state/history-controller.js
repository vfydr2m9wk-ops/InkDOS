(function (global) {
  'use strict';

  class PresentationHistoryController {
    constructor(options) {
      this.getState = options.getState;
      this.applyState = options.applyState;
      this.undoButton = options.undoButton;
      this.redoButton = options.redoButton;
      this.limit = options.limit || 80;
      this.undoStack = [];
      this.redoStack = [];
      this.locked = false;
      this.updateButtons();
    }

    capture() {
      const state = this.getState();
      return state == null ? null : JSON.parse(JSON.stringify(state));
    }

    reset() {
      this.undoStack = [];
      this.redoStack = [];
      this.updateButtons();
    }

    push(before) {
      if (this.locked || !before) {
        return;
      }
      this.undoStack.push(before);
      if (this.undoStack.length > this.limit) {
        this.undoStack.shift();
      }
      this.redoStack = [];
      this.updateButtons();
    }

    action(fn) {
      const before = this.capture();
      fn();
      this.push(before);
    }

    undo() {
      if (!this.undoStack.length) {
        return;
      }
      this.redoStack.push(this.capture());
      this.restore(this.undoStack.pop());
    }

    redo() {
      if (!this.redoStack.length) {
        return;
      }
      this.undoStack.push(this.capture());
      this.restore(this.redoStack.pop());
    }

    restore(state) {
      if (!state) {
        return;
      }
      this.locked = true;
      try {
        this.applyState(state);
      } finally {
        this.locked = false;
      }
      this.updateButtons();
    }

    updateButtons() {
      if (this.undoButton) {
        this.undoButton.disabled = !this.undoStack.length;
      }
      if (this.redoButton) {
        this.redoButton.disabled = !this.redoStack.length;
      }
    }
  }

  global.InkDeskPresentationsHistory = Object.freeze({
    version: '0.20.3.0',
    create(options) {
      return new PresentationHistoryController(options);
    },
  });
})(window);

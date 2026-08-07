(function (global) {
  'use strict';

  class PresentationNotesController {
    constructor(options) {
      this.app = options.app;
      this.textarea = options.textarea;
      this.count = options.count;
      this.button = options.button;
      this.getPresentation = options.getPresentation;
      this.getCurrentSlideData = options.getCurrentSlideData;
      this.markDirty = options.markDirty;
      this.renderThumbnails = options.renderThumbnails;
      this.relayout = options.relayout;
      this.renderTimer = null;
      this.bindInput();
      this.bindToggle();
      this.updateToggleLabel();
    }

    characterLabel(length) {
      return length + ' character' + (length === 1 ? '' : 's');
    }

    updateToggleLabel() {
      if (!this.button || !this.app) {
        return;
      }
      this.button.textContent = this.app.classList.contains('hide-notes')
        ? 'Show presenter notes'
        : 'Hide presenter notes';
    }

    setOpen(open, options = {}) {
      if (!this.app) {
        return;
      }
      this.app.classList.toggle('hide-notes', !open);
      this.updateToggleLabel();
      if (options.relayout !== false) {
        this.relayout();
      }
    }

    resetClosed(options = {}) {
      this.setOpen(false, options);
    }

    bindToggle() {
      if (!this.button) {
        return;
      }
      this.button.onclick = () => {
        const isOpen = !this.app.classList.contains('hide-notes');
        this.setOpen(!isOpen);
      };
    }

    bindInput() {
      if (!this.textarea) {
        return;
      }
      this.textarea.addEventListener('input', () => {
        const presentation = this.getPresentation();
        const slide = this.getCurrentSlideData();
        if (!presentation || !slide) {
          return;
        }

        slide.notes = this.textarea.value;
        if (this.count) {
          this.count.textContent = this.characterLabel(this.textarea.value.length);
        }
        this.markDirty();
        global.clearTimeout(this.renderTimer);
        this.renderTimer = global.setTimeout(() => this.renderThumbnails(), 250);
      });
    }

    render() {
      const presentation = this.getPresentation();
      const slide = this.getCurrentSlideData();
      if (!this.textarea || !presentation || !slide) {
        return;
      }

      const value = slide.notes || '';
      if (global.document.activeElement !== this.textarea) {
        this.textarea.value = value;
      }
      if (this.count) {
        this.count.textContent = this.characterLabel(value.length);
      }
    }

    destroy() {
      global.clearTimeout(this.renderTimer);
    }
  }

  global.InkDeskPresentationsNotes = Object.freeze({
    version: '0.20.2.9',
    create(options) {
      return new PresentationNotesController(options);
    },
  });
})(window);

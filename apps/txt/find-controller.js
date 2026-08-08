(function (global) {
  'use strict';

  function createFindController(options) {
    const editor = options && options.editor;
    const button = options && options.button;
    const bar = options && options.bar;
    const input = options && options.input;
    const previousButton = options && options.previousButton;
    const nextButton = options && options.nextButton;
    const closeButton = options && options.closeButton;
    const status = options && options.status;

    if (
      !editor || !button || !bar || !input || !previousButton ||
      !nextButton || !closeButton || !status
    ) {
      throw new Error('TXT find controller requires the complete find UI.');
    }

    function show() {
      bar.hidden = false;
      button.classList.add('active');
      input.focus();
      input.select();
    }

    function hide() {
      bar.hidden = true;
      button.classList.remove('active');
      status.textContent = '';
      editor.focus();
    }

    function find(direction) {
      const query = input.value;
      if (!query) {
        status.textContent = 'Type a search';
        return;
      }

      const source = editor.value.toLocaleLowerCase();
      const needle = query.toLocaleLowerCase();
      let index;

      if (direction < 0) {
        const before = Math.max(0, editor.selectionStart - 1);
        index = source.lastIndexOf(needle, before);
        if (index < 0) index = source.lastIndexOf(needle);
      } else {
        index = source.indexOf(needle, editor.selectionEnd);
        if (index < 0) index = source.indexOf(needle);
      }

      if (index < 0) {
        status.textContent = 'No results';
        return;
      }

      editor.focus();
      editor.setSelectionRange(index, index + query.length);
      status.textContent = (index + 1) + ' of ' + source.length;
    }

    button.addEventListener('click', function () {
      if (bar.hidden) show();
      else hide();
    });
    previousButton.addEventListener('click', function () {
      find(-1);
    });
    nextButton.addEventListener('click', function () {
      find(1);
    });
    closeButton.addEventListener('click', hide);
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        find(event.shiftKey ? -1 : 1);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        hide();
      }
    });

    return Object.freeze({ show, hide, find });
  }

  global.InkDeskTxtFindController = Object.freeze({
    version: '0.20.2.24',
    createFindController
  });
})(globalThis);

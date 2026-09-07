(function (global) {
  'use strict';

  function createTextBoxController({
    state,
    elements,
    status,
    toast,
    markDirty,
    renderPageReview,
    renderSideLists,
    commitFreeAnnotation
  }) {
    if (
      !state ||
      !elements ||
      typeof status !== 'function' ||
      typeof toast !== 'function' ||
      typeof markDirty !== 'function' ||
      typeof renderPageReview !== 'function' ||
      typeof renderSideLists !== 'function' ||
      typeof commitFreeAnnotation !== 'function'
    ) {
      throw new Error(
        'InkDOS PDF text box controller requires review state and callbacks.'
      );
    }

    const E = elements;
    let pendingText = null;

    function closeTextDialog() {
      pendingText = null;
      if (!E.textDialog) return;
      E.textDialog.classList.add('hidden');
      E.textDialogForm?.reset();
    }

    function openTextDialog(configuration) {
      if (
        !E.textDialog ||
        !E.textDialogForm ||
        !E.textDialogValue
      ) {
        status('The text box editor is unavailable.');
        return false;
      }

      pendingText = configuration;
      const title = document.getElementById('textDialogTitle');
      const submit = E.textDialogForm.querySelector('[type="submit"]');

      if (configuration.kind === 'edit') {
        const annotation = state.annotations.find(
          item => item.id === configuration.id && item.type === 'text'
        );
        if (!annotation) {
          pendingText = null;
          return false;
        }
        E.textDialogValue.value = annotation.text || '';
        if (title) title.textContent = 'Edit text';
        if (submit) submit.textContent = 'Apply';
      } else {
        E.textDialogValue.value = '';
        if (title) title.textContent = 'Insert text';
        if (submit) submit.textContent = 'Insert';
      }

      E.textDialog.classList.remove('hidden');
      global.setTimeout(() => {
        E.textDialogValue.focus();
        if (configuration.kind === 'edit') {
          E.textDialogValue.select();
        }
      }, 0);
      return true;
    }

    function requestTextAnnotation(item) {
      return openTextDialog({
        kind: 'new',
        item: { ...item, type: 'text', source: 'free' }
      });
    }

    function requestTextEdit(id) {
      if (state.tool !== 'text') return false;
      return openTextDialog({ kind: 'edit', id });
    }

    function submitTextDialog(event) {
      event.preventDefault();
      if (!pendingText) return;

      const text = String(E.textDialogValue?.value || '').trim();
      if (!text) {
        E.textDialogValue?.focus();
        return;
      }

      if (pendingText.kind === 'edit') {
        const annotation = state.annotations.find(
          item => item.id === pendingText.id && item.type === 'text'
        );
        if (!annotation) {
          closeTextDialog();
          return;
        }

        state.undo.push({
          kind: 'annotation-update',
          id: annotation.id,
          before: { ...annotation }
        });
        annotation.text = text;
        const pageNumber = annotation.page;
        closeTextDialog();
        markDirty();
        renderPageReview(pageNumber);
        renderSideLists();
        toast('Text box updated.');
        return;
      }

      const item = pendingText.item;
      closeTextDialog();
      commitFreeAnnotation({ ...item, text });
      toast('Text box inserted.');
    }

    function wireControls() {
      E.textDialogForm?.addEventListener('submit', submitTextDialog);
      E.dialogCancel?.addEventListener('click', closeTextDialog);
      E.textDialog?.addEventListener('pointerdown', event => {
        if (event.target === E.textDialog) closeTextDialog();
      });
      document.addEventListener('keydown', event => {
        if (
          event.key === 'Escape' &&
          !E.textDialog?.classList.contains('hidden')
        ) {
          closeTextDialog();
        }
      });
    }

    wireControls();

    return Object.freeze({
      requestTextAnnotation,
      requestTextEdit,
      close: closeTextDialog,
      reset: closeTextDialog
    });
  }

  global.InkDOSPdfTextBoxController = Object.freeze({
    version: '0.20.3.0',
    createTextBoxController
  });
})(globalThis);

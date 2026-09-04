(function (global) {
  'use strict';

  const documentObject = global.document;
  if (!documentObject) return;

  const VERSION = '0.20.3.0';

  /*
   * Document-session controller.
   *
   * Owns the existing shared filename, dirty-state, discard-warning and
   * download-name behavior without replacing any workspace runtime.
   */
  function initializeDocumentSessionAdapter() {
    const body = documentObject.body;
    if (!body || body.dataset.inkdosDocumentSession === 'ready') {
      return null;
    }

    const configurations = [
      {
        bodyClass: 'office-documents',
        selector: '#titleText',
        extension: '.docx',
        fallback: 'Untitled.docx'
      },
      {
        bodyClass: 'office-spreadsheets',
        selector: '#docTitle',
        extension: '.xlsx',
        fallback: 'Untitled.xlsx'
      },
      {
        bodyClass: 'office-presentations',
        selector: '#docTitle',
        extension: '.pptx',
        fallback: 'Untitled presentation.pptx'
      },
      {
        bodyClass: 'office-pdf',
        selector: '#docTitle',
        extension: '.pdf',
        fallback: 'Untitled.pdf'
      },
      {
        bodyClass: 'office-txt',
        selector: '#docTitle',
        extension: '.txt',
        fallback: 'Untitled.txt'
      },
      {
        bodyClass: 'office-epub',
        selector: '#docTitle',
        extension: '.epub',
        fallback: 'Untitled.epub'
      }
    ];

    const configuration = configurations.find(function (candidate) {
      return body.classList.contains(candidate.bodyClass);
    });

    if (!configuration) return null;

    const title = documentObject.querySelector(configuration.selector);
    if (!title) return null;

    body.dataset.inkdosDocumentSession = 'ready';

    let titleDirty = false;
    let contentDirty = false;
    let suppressTitleObserver = false;
    let lastApplicationTitle = readTitle();
    let lifecycle = null;

    if (
      global.InkDOSFileLifecycle &&
      typeof global.InkDOSFileLifecycle.create === 'function'
    ) {
      lifecycle = global.InkDOSFileLifecycle.create();
    }

    function readTitle() {
      if (
        title instanceof global.HTMLInputElement ||
        title instanceof global.HTMLTextAreaElement
      ) {
        return title.value;
      }
      return title.textContent;
    }

    function writeTitle(value) {
      suppressTitleObserver = true;
      if (
        title instanceof global.HTMLInputElement ||
        title instanceof global.HTMLTextAreaElement
      ) {
        title.value = value;
      } else {
        title.textContent = value;
      }
      title.dataset.inkdosFileName = value;
      suppressTitleObserver = false;
    }

    function normalizeName(value) {
      let name = String(value || '').trim() || configuration.fallback;
      name = name.replace(/[\\/:*?"<>|]+/g, '-');

      const extensionExpression = new RegExp(
        configuration.extension.replace('.', '\\.') + '$',
        'i'
      );

      if (!extensionExpression.test(name)) {
        name += configuration.extension;
      }

      return name;
    }

    function currentName() {
      return normalizeName(readTitle());
    }

    function syncLifecycle() {
      if (!lifecycle) return;

      const shouldWarn = titleDirty || contentDirty;
      if (shouldWarn && !lifecycle.shouldWarnBeforeUnload()) {
        lifecycle.markDirty();
      } else if (!shouldWarn && lifecycle.shouldWarnBeforeUnload()) {
        lifecycle.resetClean();
      }
    }

    function commitTitle() {
      const next = normalizeName(readTitle());
      const previous = normalizeName(lastApplicationTitle);

      writeTitle(next);
      lastApplicationTitle = next;

      if (next !== previous) {
        titleDirty = true;
        syncLifecycle();
      }

      documentObject.title =
        next +
        ((titleDirty || contentDirty) ? ' •' : '') +
        ' — InkDOS';
    }

    function restoreTitle() {
      writeTitle(normalizeName(lastApplicationTitle));
    }

    title.classList.add('file-title-editable');
    title.setAttribute('aria-label', 'File name');
    title.setAttribute('title', 'Click to rename');
    title.setAttribute('spellcheck', 'false');

    if (
      !(title instanceof global.HTMLInputElement) &&
      !(title instanceof global.HTMLTextAreaElement)
    ) {
      title.contentEditable = 'plaintext-only';
      if (title.contentEditable !== 'plaintext-only') {
        title.contentEditable = 'true';
      }
      title.setAttribute('role', 'textbox');
      title.setAttribute('tabindex', '0');
    }

    title.addEventListener('focus', function () {
      lastApplicationTitle = currentName();

      if (
        title instanceof global.HTMLInputElement ||
        title instanceof global.HTMLTextAreaElement
      ) {
        title.select();
        return;
      }

      const selection = global.getSelection();
      const range = documentObject.createRange();
      range.selectNodeContents(title);
      selection.removeAllRanges();
      selection.addRange(range);
    });

    title.addEventListener('blur', commitTitle);

    title.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        title.blur();
      } else if (event.key === 'Escape') {
        event.preventDefault();
        restoreTitle();
        title.blur();
      }
    });

    if (
      !(title instanceof global.HTMLInputElement) &&
      !(title instanceof global.HTMLTextAreaElement)
    ) {
      const titleObserver = new MutationObserver(function () {
        if (suppressTitleObserver) return;
        if (documentObject.activeElement === title) return;

        const applicationValue = String(readTitle() || '').trim();
        if (!applicationValue) return;

        lastApplicationTitle = normalizeName(applicationValue);
        title.dataset.inkdosFileName = lastApplicationTitle;
        titleDirty = false;
        syncLifecycle();
      });

      titleObserver.observe(title, {
        childList: true,
        characterData: true,
        subtree: true
      });
    }

    const dirtyMark = documentObject.querySelector('#dirtyMark');
    if (configuration.bodyClass === 'office-pdf' && dirtyMark) {
      let lastPdfDirty = false;

      function synchronizePdfDirty() {
        const nowDirty =
          !dirtyMark.hidden &&
          dirtyMark.style.display !== 'none';

        if (nowDirty === lastPdfDirty) return;
        lastPdfDirty = nowDirty;
        contentDirty = nowDirty;
        syncLifecycle();
      }

      new MutationObserver(synchronizePdfDirty).observe(dirtyMark, {
        attributes: true,
        attributeFilter: ['hidden', 'style', 'class']
      });

      synchronizePdfDirty();
    }

    function rewriteDownloadName(originalName) {
      const desired = currentName();
      const extension = configuration.extension;
      const desiredBase = desired.slice(0, -extension.length);
      const original = String(originalName || '');
      const originalBase = original.replace(
        new RegExp(extension.replace('.', '\\.') + '$', 'i'),
        ''
      );

      const suffixMatch = originalBase.match(
        /((?: copy .+)|(?:-modified)|(?:-copy(?: .*)?))$/i
      );

      return desiredBase +
        (suffixMatch ? suffixMatch[1] : '') +
        extension;
    }

    if (
      global.InkDOSRuntime &&
      typeof global.InkDOSRuntime.requestDownload === 'function' &&
      !global.InkDOSRuntime.requestDownload
        .__inkdosDocumentSessionWrapped
    ) {
      const originalRequestDownload =
        global.InkDOSRuntime.requestDownload.bind(
          global.InkDOSRuntime
        );

      function requestDownload(blob, fileName) {
        const args = Array.prototype.slice.call(arguments);
        args[1] = rewriteDownloadName(fileName);

        const receipt = originalRequestDownload.apply(null, args);
        titleDirty = false;
        contentDirty = false;
        lastApplicationTitle = currentName();
        syncLifecycle();
        return receipt;
      }

      requestDownload.__inkdosDocumentSessionWrapped = true;
      requestDownload.__inkdosOriginal = originalRequestDownload;
      global.InkDOSRuntime = Object.freeze(Object.assign(
        {},
        global.InkDOSRuntime,
        { requestDownload }
      ));
    }

    const replacementActionIds = new Set([
      'newBtn',
      'newSmall',
      'newEmptyBtn',
      'openBtn',
      'openSmall',
      'openEmptyBtn'
    ]);

    documentObject.addEventListener(
      'click',
      function (event) {
        const action = event.target.closest('[id]');
        if (!action || !replacementActionIds.has(action.id)) return;
        if (!(titleDirty || contentDirty)) return;

        const accepted = global.confirm(
          'You have unsaved changes. Continue and discard them?'
        );

        if (!accepted) {
          event.preventDefault();
          event.stopImmediatePropagation();
          return;
        }

        titleDirty = false;
        contentDirty = false;
        syncLifecycle();
      },
      true
    );

    const fileInput = documentObject.querySelector(
      'input[type="file"]'
    );

    if (fileInput) {
      fileInput.addEventListener(
        'change',
        function (event) {
          if (!(titleDirty || contentDirty)) return;

          const accepted = global.confirm(
            'You have unsaved changes. Continue and discard them?'
          );

          if (!accepted) {
            event.preventDefault();
            event.stopImmediatePropagation();
            fileInput.value = '';
            return;
          }

          titleDirty = false;
          contentDirty = false;
          syncLifecycle();
        },
        true
      );
    }

    writeTitle(normalizeName(readTitle()));
    lastApplicationTitle = currentName();

    return Object.freeze({
      version: '0.20.0',
      currentName,
      commitTitle
    });
  }

  global.InkDOSDocumentSessionController = Object.freeze({
    version: VERSION,
    initialize: initializeDocumentSessionAdapter
  });
})(typeof window !== 'undefined' ? window : globalThis);

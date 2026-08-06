(function (global) {
  'use strict';

  const documentObject = global.document;
  if (!documentObject) return;

  documentObject.documentElement.classList.add('inkdesk');

  const current = documentObject.currentScript;
  const source = current && current.src
    ? current.src
    : new URL('office-shell.js', documentObject.baseURI).href;
  const uiBase = new URL('./ui/', source);

  function addStylesheet(name) {
    const key = 'inkdesk-ui-' +
      name.replace(/[^a-z0-9]+/gi, '-').toLowerCase();

    if (
      documentObject.querySelector(
        'link[data-inkdesk-ui="' + key + '"]'
      )
    ) {
      return;
    }

    const link = documentObject.createElement('link');
    link.rel = 'stylesheet';
    link.href = new URL(name, uiBase).href;
    link.dataset.inkdeskUi = key;
    documentObject.head.appendChild(link);
  }

  function loadApplicationShell() {
    if (
      global.InkDeskUI &&
      global.InkDeskUI.version === '0.19.4.3'
    ) {
      return Promise.resolve(global.InkDeskUI);
    }

    return new Promise(function (resolve, reject) {
      const existing = documentObject.querySelector(
        'script[data-inkdesk-ui="application-shell"]'
      );

      if (existing) {
        existing.addEventListener(
          'load',
          function () { resolve(global.InkDeskUI); },
          { once: true }
        );
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = documentObject.createElement('script');
      script.src = new URL('application-shell.js', uiBase).href;
      script.async = false;
      script.dataset.inkdeskUi = 'application-shell';

      script.addEventListener(
        'load',
        function () {
          if (!global.InkDeskUI) {
            reject(new Error('InkDeskUI did not initialize.'));
            return;
          }
          resolve(global.InkDeskUI);
        },
        { once: true }
      );

      script.addEventListener(
        'error',
        function () {
          reject(
            new Error(
              'The shared InkDesk application shell could not be loaded.'
            )
          );
        },
        { once: true }
      );

      documentObject.head.appendChild(script);
    });
  }

  function loadWorkspaceLayout() {
    if (
      global.InkDeskWorkspaceLayout &&
      global.InkDeskWorkspaceLayout.version === '0.19.4.7'
    ) {
      return Promise.resolve(global.InkDeskWorkspaceLayout);
    }

    return new Promise(function (resolve, reject) {
      const existing = documentObject.querySelector(
        'script[data-inkdesk-ui="workspace-layout"]'
      );

      if (existing) {
        existing.addEventListener(
          'load',
          function () { resolve(global.InkDeskWorkspaceLayout); },
          { once: true }
        );
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = documentObject.createElement('script');
      script.src = new URL('workspace-layout.js', uiBase).href;
      script.async = false;
      script.dataset.inkdeskUi = 'workspace-layout';

      script.addEventListener(
        'load',
        function () {
          resolve(global.InkDeskWorkspaceLayout || null);
        },
        { once: true }
      );

      script.addEventListener(
        'error',
        function () {
          reject(
            new Error(
              'The shared InkDesk workspace layout could not be loaded.'
            )
          );
        },
        { once: true }
      );

      documentObject.head.appendChild(script);
    });
  }

  addStylesheet('design-tokens.css');
  addStylesheet('components.css');
  addStylesheet('workspace-layout.css');

  global.InkDeskUIReady = loadApplicationShell()
    .then(function (ui) {
      return loadWorkspaceLayout().then(function () {
        return ui;
      });
    })
    .catch(function (error) {
    if (documentObject.body) {
      documentObject.body.dataset.inkdeskShellError = 'true';
    }
    if (
      global.console &&
      typeof global.console.error === 'function'
    ) {
      global.console.error(error);
    }
    return null;
  });

  global.addEventListener(
    'pageshow',
    function () {
      if (documentObject.body) {
        documentObject.body.classList.add('office-product-ready');
      }
    },
    { once: true }
  );
})(typeof window !== 'undefined' ? window : globalThis);

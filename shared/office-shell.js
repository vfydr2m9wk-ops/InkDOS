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
      global.InkDeskUI.version === '0.20.0'
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

  function loadWorkspacePanelController() {
    if (
      global.InkDeskWorkspacePanelController &&
      global.InkDeskWorkspacePanelController.version === '0.20.2.25'
    ) {
      return Promise.resolve(global.InkDeskWorkspacePanelController);
    }

    return new Promise(function (resolve, reject) {
      const existing = documentObject.querySelector(
        'script[data-inkdesk-ui="workspace-panel-controller"]'
      );

      if (existing) {
        existing.addEventListener(
          'load',
          function () { resolve(global.InkDeskWorkspacePanelController); },
          { once: true }
        );
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = documentObject.createElement('script');
      script.src = new URL('workspace-panel-controller.js', uiBase).href;
      script.async = false;
      script.dataset.inkdeskUi = 'workspace-panel-controller';

      script.addEventListener(
        'load',
        function () {
          if (!global.InkDeskWorkspacePanelController) {
            reject(new Error(
              'InkDesk workspace panel controller did not initialize.'
            ));
            return;
          }
          resolve(global.InkDeskWorkspacePanelController);
        },
        { once: true }
      );

      script.addEventListener(
        'error',
        function () {
          reject(new Error(
            'The shared InkDesk workspace panel controller could not be loaded.'
          ));
        },
        { once: true }
      );

      documentObject.head.appendChild(script);
    });
  }

  function loadDocumentRulerModel() {
    if (
      global.InkDeskDocumentRulerModel &&
      global.InkDeskDocumentRulerModel.version === '0.20.2.25'
    ) {
      return Promise.resolve(global.InkDeskDocumentRulerModel);
    }

    return new Promise(function (resolve, reject) {
      const existing = documentObject.querySelector(
        'script[data-inkdesk-ui="document-ruler-model"]'
      );

      if (existing) {
        existing.addEventListener(
          'load',
          function () { resolve(global.InkDeskDocumentRulerModel); },
          { once: true }
        );
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = documentObject.createElement('script');
      script.src = new URL('document-ruler-model.js', uiBase).href;
      script.async = false;
      script.dataset.inkdeskUi = 'document-ruler-model';

      script.addEventListener(
        'load',
        function () {
          if (!global.InkDeskDocumentRulerModel) {
            reject(new Error(
              'InkDesk document ruler model did not initialize.'
            ));
            return;
          }
          resolve(global.InkDeskDocumentRulerModel);
        },
        { once: true }
      );

      script.addEventListener(
        'error',
        function () {
          reject(new Error(
            'The shared InkDesk document ruler model could not be loaded.'
          ));
        },
        { once: true }
      );

      documentObject.head.appendChild(script);
    });
  }

  function loadDocumentRulerDragController() {
    if (
      global.InkDeskDocumentRulerDragController &&
      global.InkDeskDocumentRulerDragController.version === '0.20.2.25'
    ) {
      return Promise.resolve(global.InkDeskDocumentRulerDragController);
    }

    return new Promise(function (resolve, reject) {
      const existing = documentObject.querySelector(
        'script[data-inkdesk-ui="document-ruler-drag-controller"]'
      );

      if (existing) {
        existing.addEventListener(
          'load',
          function () { resolve(global.InkDeskDocumentRulerDragController); },
          { once: true }
        );
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = documentObject.createElement('script');
      script.src = new URL('document-ruler-drag-controller.js', uiBase).href;
      script.async = false;
      script.dataset.inkdeskUi = 'document-ruler-drag-controller';

      script.addEventListener(
        'load',
        function () {
          if (!global.InkDeskDocumentRulerDragController) {
            reject(new Error(
              'InkDesk document ruler drag controller did not initialize.'
            ));
            return;
          }
          resolve(global.InkDeskDocumentRulerDragController);
        },
        { once: true }
      );

      script.addEventListener(
        'error',
        function () {
          reject(new Error(
            'The shared InkDesk document ruler drag controller could not be loaded.'
          ));
        },
        { once: true }
      );

      documentObject.head.appendChild(script);
    });
  }

  function loadWorkspaceLayoutRuntime() {
    if (
      global.InkDeskWorkspaceLayout &&
      global.InkDeskWorkspaceLayout.version === '0.20.0'
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

  function loadWorkspaceLayout() {
    return loadWorkspacePanelController().then(function () {
      return loadDocumentRulerModel();
    }).then(function () {
      return loadDocumentRulerDragController();
    }).then(function () {
      return loadWorkspaceLayoutRuntime();
    });
  }

  addStylesheet('design-tokens.css');
  addStylesheet('components.css');
  addStylesheet('workspace-layout.css');
  addStylesheet('visual-foundation.css');

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


  /*
   * Document-session title adapter — 0.20.0.
   *
   * This shared layer deliberately avoids replacing complete application
   * files. It upgrades the title already rendered by each installed
   * workspace and rewrites only the requested download name.
   */
  function loadFileLifecycle() {
    if (global.InkDeskFileLifecycle) {
      return Promise.resolve(global.InkDeskFileLifecycle);
    }

    return new Promise(function (resolve, reject) {
      const existing = documentObject.querySelector(
        'script[data-inkdesk-session="file-lifecycle"]'
      );

      if (existing) {
        existing.addEventListener(
          'load',
          function () {
            resolve(global.InkDeskFileLifecycle || null);
          },
          { once: true }
        );
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = documentObject.createElement('script');
      script.src = new URL('file-lifecycle.js', source).href;
      script.async = false;
      script.dataset.inkdeskSession = 'file-lifecycle';
      script.addEventListener(
        'load',
        function () {
          resolve(global.InkDeskFileLifecycle || null);
        },
        { once: true }
      );
      script.addEventListener('error', reject, { once: true });
      documentObject.head.appendChild(script);
    });
  }

  function whenDocumentReady() {
    if (documentObject.readyState !== 'loading') {
      return Promise.resolve();
    }

    return new Promise(function (resolve) {
      documentObject.addEventListener(
        'DOMContentLoaded',
        resolve,
        { once: true }
      );
    });
  }

  function loadDocumentSessionController() {
    if (
      global.InkDeskDocumentSessionController &&
      global.InkDeskDocumentSessionController.version === '0.20.2.25'
    ) {
      return Promise.resolve(global.InkDeskDocumentSessionController);
    }

    return new Promise(function (resolve, reject) {
      const existing = documentObject.querySelector(
        'script[data-inkdesk-ui="document-session-controller"]'
      );

      if (existing) {
        existing.addEventListener(
          'load',
          function () {
            resolve(global.InkDeskDocumentSessionController || null);
          },
          { once: true }
        );
        existing.addEventListener('error', reject, { once: true });
        return;
      }

      const script = documentObject.createElement('script');
      script.src = new URL('document-session-controller.js', uiBase).href;
      script.async = false;
      script.dataset.inkdeskUi = 'document-session-controller';
      script.addEventListener(
        'load',
        function () {
          if (!global.InkDeskDocumentSessionController) {
            reject(new Error(
              'InkDesk document-session controller did not initialize.'
            ));
            return;
          }
          resolve(global.InkDeskDocumentSessionController);
        },
        { once: true }
      );
      script.addEventListener(
        'error',
        function () {
          reject(new Error(
            'The shared InkDesk document-session controller could not be loaded.'
          ));
        },
        { once: true }
      );
      documentObject.head.appendChild(script);
    });
  }

  global.InkDeskDocumentSessionReady = Promise.all([
    loadFileLifecycle(),
    loadDocumentSessionController(),
    whenDocumentReady()
  ])
    .then(function (values) {
      const controller = values[1];
      if (!controller || typeof controller.initialize !== 'function') {
        return null;
      }
      return controller.initialize();
    })
    .catch(function (error) {
      if (
        global.console &&
        typeof global.console.error === 'function'
      ) {
        global.console.error(
          'InkDesk document-session adapter failed.',
          error
        );
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

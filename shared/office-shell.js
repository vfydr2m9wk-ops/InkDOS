(function (global) {
  'use strict';

  const doc = global.document;
  if (!doc) return;

  doc.documentElement.classList.add('inkdos');

  const current = doc.currentScript;
  const source = current && current.src
    ? current.src
    : new URL('office-shell.js', doc.baseURI).href;
  const sharedBase = new URL('./', source);
  const uiBase = new URL('./ui/', source);

  function dataKey(name) {
    return 'inkdos-' + name.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
  }

  function addStylesheet(name) {
    const key = dataKey('ui-' + name);
    if (doc.querySelector('link[data-inkdos-ui="' + key + '"]')) return;
    const link = doc.createElement('link');
    link.rel = 'stylesheet';
    link.href = new URL(name, uiBase).href;
    link.dataset.inkdosUi = key;
    doc.head.appendChild(link);
  }

  function loadScript(name, globalName, base, key) {
    if (global[globalName]) return Promise.resolve(global[globalName]);
    const marker = key || name.replace(/\.js$/i, '');
    const selector = 'script[data-inkdos-ui="' + marker + '"]';
    return new Promise(function (resolve, reject) {
      const existing = doc.querySelector(selector);
      const finish = function () { resolve(global[globalName] || null); };
      if (existing) {
        existing.addEventListener('load', finish, { once: true });
        existing.addEventListener('error', reject, { once: true });
        return;
      }
      const script = doc.createElement('script');
      script.src = new URL(name, base || uiBase).href;
      script.async = false;
      script.dataset.inkdosUi = marker;
      script.addEventListener('load', function () {
        if (!global[globalName]) {
          reject(new Error(globalName + ' did not initialize.'));
          return;
        }
        finish();
      }, { once: true });
      script.addEventListener('error', reject, { once: true });
      doc.head.appendChild(script);
    });
  }

  function loadApplicationShell() {
    return loadScript('application-shell.js', 'InkDOSUI', uiBase, 'application-shell');
  }

  function loadWorkspacePanelController() {
    return loadScript('workspace-panel-controller.js', 'InkDOSWorkspacePanelController', uiBase, 'workspace-panel-controller');
  }

  function loadDocumentRulerModel() {
    return loadScript('document-ruler-model.js', 'InkDOSDocumentRulerModel', uiBase, 'document-ruler-model');
  }

  function loadDocumentRulerDragController() {
    return loadScript('document-ruler-drag-controller.js', 'InkDOSDocumentRulerDragController', uiBase, 'document-ruler-drag-controller');
  }

  function loadWorkspaceLayoutRuntime() {
    return loadScript('workspace-layout.js', 'InkDOSWorkspaceLayout', uiBase, 'workspace-layout');
  }

  function loadWorkspaceLayout() {
    return loadWorkspacePanelController()
      .then(loadDocumentRulerModel)
      .then(loadDocumentRulerDragController)
      .then(loadWorkspaceLayoutRuntime);
  }

  function loadFileLifecycle() {
    return loadScript('file-lifecycle.js', 'InkDOSFileLifecycle', sharedBase, 'file-lifecycle');
  }

  function loadDocumentSessionController() {
    return loadScript('document-session-controller.js', 'InkDOSDocumentSessionController', uiBase, 'document-session-controller');
  }

  function whenDocumentReady() {
    if (doc.readyState !== 'loading') return Promise.resolve();
    return new Promise(function (resolve) {
      doc.addEventListener('DOMContentLoaded', resolve, { once: true });
    });
  }

  [
    'design-tokens.css',
    'components.css',
    'workspace-layout.css',
    'visual-foundation.css',
    'visual.css',
    'content.css',
    'workspace.css',
    'polish.css'
  ].forEach(addStylesheet);

  global.InkDOSUIReady = loadApplicationShell()
    .then(function (ui) {
      return loadWorkspaceLayout().then(function () { return ui; });
    })
    .catch(function (error) {
      if (doc.body) doc.body.dataset.inkdosShellError = 'true';
      if (global.console && typeof global.console.error === 'function') {
        global.console.error(error);
      }
      return null;
    });

  global.InkDOSDocumentSessionReady = Promise.all([
    loadFileLifecycle(),
    loadDocumentSessionController(),
    whenDocumentReady()
  ])
    .then(function (values) {
      const controller = values[1];
      if (!controller || typeof controller.initialize !== 'function') return null;
      return controller.initialize();
    })
    .catch(function (error) {
      if (global.console && typeof global.console.error === 'function') {
        global.console.error('InkDOS document-session initialization failed.', error);
      }
      return null;
    });

  global.addEventListener('pageshow', function () {
    if (doc.body) doc.body.classList.add('office-product-ready');
  }, { once: true });
})(typeof window !== 'undefined' ? window : globalThis);

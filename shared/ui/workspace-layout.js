(function (global) {
  'use strict';

  const VERSION = '0.20.0';
  const MODULE_DEFAULTS = Object.freeze({
    documents: Object.freeze({
      sidebar: false
    }),
    presentations: Object.freeze({
      thumbnails: true,
      inspector: false,
      notes: false
    }),
    pdf: Object.freeze({
      sidebar: false
    })
  });


  function documentRulerModel() {
    return global.InkDeskDocumentRulerModel || null;
  }

function installDocumentsRuler(documentObject) {
  const model = documentRulerModel();
  if (!model) return null;

  const ruler = documentObject.getElementById('ruler');
  const track =
    ruler &&
    ruler.querySelector('.ruler-track');
  const ticks =
    track &&
    track.querySelector('.ticks');
  const viewport =
    documentObject.getElementById('viewport');
  const pagesHost =
    documentObject.getElementById('pagesHost');

  if (!ruler || !track || !ticks || !viewport || !pagesHost) {
    return null;
  }

  if (ruler.__inkdeskPageRuler) {
    return ruler.__inkdeskPageRuler;
  }

  ruler.dataset.inkdeskRuler = 'page-linked';
  track.dataset.inkdeskRulerTrack = 'active-page';

  let activePage = null;
  let metrics = null;
  let frame = 0;
  let lastTickKey = '';

  function scheduleSync() {
    if (frame) return;

    frame = global.requestAnimationFrame
      ? global.requestAnimationFrame(sync)
      : global.setTimeout(sync, 0);
  }

  function renderTicks(nextMetrics) {
    const key = [
      Math.round(nextMetrics.pageWidth * 100) / 100,
      Math.round(nextMetrics.zoom * 1000) / 1000
    ].join(':');

    if (key === lastTickKey) return;
    lastTickKey = key;

    ticks.replaceChildren();

    const fragment =
      documentObject.createDocumentFragment &&
      documentObject.createDocumentFragment();

    const target = fragment || ticks;

    model.rulerTickModel(nextMetrics.pageWidth, 96).forEach(
      function (tick) {
        const mark = documentObject.createElement('span');
        mark.className =
          'inkdesk-ruler-tick ' +
          'inkdesk-ruler-tick-' +
          tick.kind;
        mark.style.left = (tick.ratio * 100) + '%';
        mark.dataset.kind = tick.kind;

        if (tick.label) {
          const label = documentObject.createElement('span');
          label.className = 'inkdesk-ruler-number';
          label.textContent = tick.label;
          mark.appendChild(label);
        }

        target.appendChild(mark);
      }
    );

    if (fragment) ticks.appendChild(fragment);
  }

  function ensureMarginZones() {
    let left = track.querySelector(
      '.inkdesk-ruler-margin-left'
    );
    let right = track.querySelector(
      '.inkdesk-ruler-margin-right'
    );

    if (!left) {
      left = documentObject.createElement('span');
      left.className =
        'inkdesk-ruler-margin inkdesk-ruler-margin-left';
      track.prepend(left);
    }

    if (!right) {
      right = documentObject.createElement('span');
      right.className =
        'inkdesk-ruler-margin inkdesk-ruler-margin-right';
      track.prepend(right);
    }

    return { left, right };
  }

  function handleElements() {
    return {
      first: documentObject.getElementById('firstIndent'),
      hanging: documentObject.getElementById('hangingIndent'),
      left: documentObject.getElementById('leftIndent'),
      right: documentObject.getElementById('rightIndent')
    };
  }

  function updateHandles(nextState) {
    if (!metrics) return;

    const handles = handleElements();
    const state = model.clampIndentState(nextState, metrics);
    const contentStart = metrics.contentStartDisplay;
    const contentEnd = metrics.contentEndDisplay;

    const leftPosition =
      contentStart + state.left * metrics.zoom;

    const firstPosition =
      contentStart + state.first * metrics.zoom;

    const rightDistance =
      metrics.displayWidth -
      contentEnd +
      state.right * metrics.zoom;

    if (handles.first) {
      handles.first.style.left = firstPosition + 'px';
    }

    if (handles.hanging) {
      handles.hanging.style.left = leftPosition + 'px';
    }

    if (handles.left) {
      handles.left.style.left = leftPosition + 'px';
    }

    if (handles.right) {
      handles.right.style.right = rightDistance + 'px';
    }
  }

  function currentBlockState() {
    const block = model.selectedDocumentBlock(
      documentObject,
      pagesHost
    );

    return {
      block,
      state: model.clampIndentState(
        model.documentIndentState(block, global),
        metrics
      )
    };
  }

  function sync() {
    frame = 0;

    const page = model.visibleDocumentPage(
      documentObject,
      viewport
    );

    if (!page) {
      activePage = null;
      metrics = null;
      track.hidden = true;
      ruler.dataset.activePage = '';
      return;
    }

    activePage = page;
    metrics = model.rulerMetrics(page, global);

    if (!metrics) {
      track.hidden = true;
      return;
    }

    const rulerRect = ruler.getBoundingClientRect();
    const offset = metrics.rect.left - rulerRect.left;

    track.hidden = false;
    track.style.width = metrics.displayWidth + 'px';
    track.style.transform =
      'translate3d(' + offset + 'px,0,0)';

    track.style.setProperty(
      '--inkdesk-ruler-page-width',
      metrics.displayWidth + 'px'
    );

    track.style.setProperty(
      '--inkdesk-ruler-left-margin',
      metrics.contentStartDisplay + 'px'
    );

    track.style.setProperty(
      '--inkdesk-ruler-right-margin',
      (
        metrics.displayWidth -
        metrics.contentEndDisplay
      ) + 'px'
    );

    ruler.dataset.activePage =
      String(page.dataset.page || '');

    ruler.dataset.pageWidth =
      String(Math.round(metrics.pageWidth));

    ruler.dataset.pageZoom =
      String(Math.round(metrics.zoom * 1000) / 1000);

    const zones = ensureMarginZones();
    zones.left.style.width =
      metrics.contentStartDisplay + 'px';
    zones.right.style.width =
      (
        metrics.displayWidth -
        metrics.contentEndDisplay
      ) + 'px';

    renderTicks(metrics);
    updateHandles(currentBlockState().state);
  }

  const dragControllerFactory =
    global.InkDeskDocumentRulerDragController;

  const dragController =
    dragControllerFactory &&
    typeof dragControllerFactory.create === 'function'
      ? dragControllerFactory.create({
        documentObject,
        ruler,
        track,
        pagesHost,
        model,
        scheduleSync,
        sync,
        currentBlockState,
        updateHandles,
        getMetrics: function () { return metrics; },
        setMetrics: function (value) { metrics = value; },
        getActivePage: function () { return activePage; }
      })
      : null;

  viewport.addEventListener(
    'scroll',
    scheduleSync,
    { passive: true }
  );

  documentObject.addEventListener(
    'selectionchange',
    scheduleSync
  );

  global.addEventListener(
    'resize',
    scheduleSync
  );

  [
    'zoomIn',
    'zoomOut',
    'zoomLabel',
    'fitWidth',
    'sidebarBtn'
  ].forEach(function (id) {
    const control = documentObject.getElementById(id);
    if (!control) return;

    control.addEventListener(
      'click',
      function () {
        global.setTimeout(scheduleSync, 0);
      }
    );
  });

  let mutationObserver = null;

  if (typeof global.MutationObserver === 'function') {
    mutationObserver = new global.MutationObserver(
      scheduleSync
    );

    mutationObserver.observe(pagesHost, {
      childList: true,
      subtree: false,
      attributes: true,
      attributeFilter: ['style', 'class']
    });
  }

  let resizeObserver = null;

  if (typeof global.ResizeObserver === 'function') {
    resizeObserver = new global.ResizeObserver(
      scheduleSync
    );

    resizeObserver.observe(viewport);
    resizeObserver.observe(pagesHost);
    resizeObserver.observe(ruler);
  }

  const controller = Object.freeze({
    version: VERSION,
    sync: scheduleSync,
    metrics: function () { return metrics; },
    activePage: function () { return activePage; },
    destroy: function () {
      mutationObserver && mutationObserver.disconnect();
      resizeObserver && resizeObserver.disconnect();
      viewport.removeEventListener('scroll', scheduleSync);
      documentObject.removeEventListener(
        'selectionchange',
        scheduleSync
      );
      global.removeEventListener(
        'resize',
        scheduleSync
      );
      if (dragController && typeof dragController.destroy === 'function') {
        dragController.destroy();
      }
    }
  });

  Object.defineProperty(
    ruler,
    '__inkdeskPageRuler',
    {
      value: controller,
      configurable: true
    }
  );

  scheduleSync();
  return controller;
}
  function applyDocumentRuler(documentObject) {
    return Boolean(installDocumentsRuler(documentObject));
  }

  function apply(documentObject) {
    const doc = documentObject || global.document;
    if (!doc || !doc.body || !doc.querySelector) return false;
    if (doc.body.dataset.inkdeskWorkspaceLayout === VERSION) return true;

    const panelController = global.InkDeskWorkspacePanelController;
    const currentModule = panelController && typeof panelController.moduleId === 'function'
      ? panelController.moduleId(doc)
      : '';
    let applied = false;

    if (panelController && typeof panelController.apply === 'function') {
      applied = Boolean(panelController.apply(doc, currentModule));
    }

    if (currentModule === 'documents') {
      applied = applyDocumentRuler(doc) || applied;
    }

    doc.body.dataset.inkdeskWorkspaceLayout = VERSION;
    if (panelController && typeof panelController.notifyLayoutReady === 'function') {
      panelController.notifyLayoutReady(doc, currentModule);
    }

    global.setTimeout(function () {
      try {
        global.dispatchEvent(new Event('resize'));
      } catch (error) {
        /* Resize dispatch is only a layout hint. */
      }
    }, 0);

    return applied;
  }

  function autoInitialize() {
    if (!global.document) return false;

    if (global.InkDeskUIReady && typeof global.InkDeskUIReady.then === 'function') {
      global.InkDeskUIReady.then(function () {
        apply(global.document);
      });
      return true;
    }

    return apply(global.document);
  }

  const api = Object.freeze({
    version: VERSION,
    defaults: MODULE_DEFAULTS,
    apply,
    moduleId: function (documentObject) {
      const controller = global.InkDeskWorkspacePanelController;
      return controller && typeof controller.moduleId === 'function'
        ? controller.moduleId(documentObject)
        : '';
    },
    resolvedPreference: function (key, defaultValue) {
      const controller = global.InkDeskWorkspacePanelController;
      return controller && typeof controller.resolvedPreference === 'function'
        ? controller.resolvedPreference(key, defaultValue)
        : Boolean(defaultValue);
    },
    rulerTickModel: function () {
      const model = documentRulerModel();
      return model && model.rulerTickModel.apply(model, arguments);
    },
    rulerMetrics: function () {
      const model = documentRulerModel();
      return model && model.rulerMetrics.apply(model, arguments);
    },
    visibleDocumentPage: function () {
      const model = documentRulerModel();
      return model && model.visibleDocumentPage.apply(model, arguments);
    },
    documentIndentState: function () {
      const model = documentRulerModel();
      return model && model.documentIndentState.apply(model, arguments);
    },
    clampIndentState: function () {
      const model = documentRulerModel();
      return model && model.clampIndentState.apply(model, arguments);
    },
    pointerToDocumentIndent: function () {
      const model = documentRulerModel();
      return model && model.pointerToDocumentIndent.apply(model, arguments);
    },
    applyDocumentIndent: function () {
      const model = documentRulerModel();
      return model && model.applyDocumentIndent.apply(model, arguments);
    },
    installDocumentsRuler
  });

  global.InkDeskWorkspaceLayout = api;

  if (global.document) {
    if (global.document.readyState === 'loading') {
      global.document.addEventListener(
        'DOMContentLoaded',
        autoInitialize,
        { once: true }
      );
    } else {
      autoInitialize();
    }
  }
})(typeof window !== 'undefined' ? window : globalThis);

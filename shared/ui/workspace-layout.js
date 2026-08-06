(function (global) {
  'use strict';

  const VERSION = '0.19.4.7';
  const STORAGE_PREFIX = 'inkdesk.ui.session.';

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

  function safeSessionGet(key) {
    try {
      const value = global.sessionStorage.getItem(STORAGE_PREFIX + key);
      if (value === 'true') return true;
      if (value === 'false') return false;
    } catch (error) {
      return null;
    }
    return null;
  }

  function safeSessionSet(key, value) {
    try {
      global.sessionStorage.setItem(
        STORAGE_PREFIX + key,
        value ? 'true' : 'false'
      );
    } catch (error) {
      /* Direct-file and privacy modes may reject session storage. */
    }
  }

  function resolvedPreference(key, defaultValue) {
    const stored = safeSessionGet(key);
    return stored === null ? Boolean(defaultValue) : stored;
  }

  function setExpanded(control, expanded) {
    if (!control) return;
    control.setAttribute('aria-expanded', expanded ? 'true' : 'false');
  }

  function notify(documentObject, moduleId) {
    if (!documentObject || typeof documentObject.dispatchEvent !== 'function') {
      return;
    }

    let event = null;
    if (typeof global.CustomEvent === 'function') {
      event = new global.CustomEvent('inkdesk:workspace-layout-ready', {
        detail: { version: VERSION, moduleId }
      });
    } else if (typeof documentObject.createEvent === 'function') {
      event = documentObject.createEvent('CustomEvent');
      event.initCustomEvent(
        'inkdesk:workspace-layout-ready',
        false,
        false,
        { version: VERSION, moduleId }
      );
    }

    if (event) documentObject.dispatchEvent(event);
  }

  function moduleId(documentObject) {
    if (!documentObject || !documentObject.body) return '';

    const declared = String(
      documentObject.body.dataset &&
      documentObject.body.dataset.inkdeskModule ||
      ''
    );

    if (declared) return declared;

    const classes = documentObject.body.classList;
    if (!classes) return '';
    if (classes.contains('office-documents')) return 'documents';
    if (classes.contains('office-spreadsheets')) return 'spreadsheets';
    if (classes.contains('office-presentations')) return 'presentations';
    if (classes.contains('office-pdf')) return 'pdf';
    return '';
  }


function finiteNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number(fallback || 0);
}

function clampNumber(value, minimum, maximum) {
  return Math.max(
    finiteNumber(minimum, 0),
    Math.min(
      finiteNumber(maximum, 0),
      finiteNumber(value, 0)
    )
  );
}

function rulerTickModel(pageWidthPx, dpi) {
  const width = Math.max(1, finiteNumber(pageWidthPx, 816));
  const pixelsPerInch = Math.max(48, finiteNumber(dpi, 96));
  const eighth = pixelsPerInch / 8;
  const count = Math.floor(width / eighth);
  const ticks = [];

  for (let index = 0; index <= count; index += 1) {
    const position = index * eighth;
    const remainder = index % 8;
    const kind =
      remainder === 0
        ? 'major'
        : remainder === 4
          ? 'half'
          : remainder % 2 === 0
            ? 'quarter'
            : 'minor';

    ticks.push(Object.freeze({
      position,
      ratio: clampNumber(position / width, 0, 1),
      kind,
      label: kind === 'major'
        ? String(Math.round(position / pixelsPerInch))
        : ''
    }));
  }

  if (
    ticks.length &&
    width - ticks[ticks.length - 1].position > eighth * 0.45
  ) {
    ticks.push(Object.freeze({
      position: width,
      ratio: 1,
      kind: 'edge',
      label: ''
    }));
  }

  return Object.freeze(ticks);
}

function rulerMetrics(page, globalObject) {
  if (!page || typeof page.getBoundingClientRect !== 'function') {
    return null;
  }

  const rect = page.getBoundingClientRect();
  const style =
    globalObject &&
    typeof globalObject.getComputedStyle === 'function'
      ? globalObject.getComputedStyle(page)
      : page.__computedStyle || {};

  const unscaledWidth = Math.max(
    1,
    finiteNumber(
      page.offsetWidth,
      finiteNumber(style.width, finiteNumber(rect.width, 816))
    )
  );

  const displayWidth = Math.max(
    1,
    finiteNumber(rect.width, unscaledWidth)
  );

  const zoom = displayWidth / unscaledWidth;

  const paddingLeft = clampNumber(
    parseFloat(style.paddingLeft) || 0,
    0,
    unscaledWidth
  );

  const paddingRight = clampNumber(
    parseFloat(style.paddingRight) || 0,
    0,
    unscaledWidth
  );

  const contentWidth = Math.max(
    1,
    unscaledWidth - paddingLeft - paddingRight
  );

  return Object.freeze({
    page,
    rect: Object.freeze({
      left: finiteNumber(rect.left, 0),
      top: finiteNumber(rect.top, 0),
      right: finiteNumber(rect.right, finiteNumber(rect.left, 0) + displayWidth),
      bottom: finiteNumber(rect.bottom, finiteNumber(rect.top, 0)),
      width: displayWidth,
      height: Math.max(1, finiteNumber(rect.height, 1))
    }),
    pageWidth: unscaledWidth,
    displayWidth,
    zoom,
    paddingLeft,
    paddingRight,
    contentWidth,
    contentStartDisplay: paddingLeft * zoom,
    contentEndDisplay: (unscaledWidth - paddingRight) * zoom
  });
}

function visibleDocumentPage(documentObject, viewport) {
  if (!documentObject || !viewport) return null;

  const selection =
    documentObject.getSelection &&
    documentObject.getSelection();

  if (selection && selection.rangeCount) {
    let node = selection.anchorNode;
    if (node && node.nodeType === 3) node = node.parentElement;
    const selectedPage =
      node &&
      typeof node.closest === 'function' &&
      node.closest('.page');

    if (selectedPage) return selectedPage;
  }

  const pages = Array.from(
    documentObject.querySelectorAll('.pages-host > .page')
  );

  if (!pages.length) return null;

  const viewportRect = viewport.getBoundingClientRect();
  let best = null;
  let bestArea = -1;

  pages.forEach(function (page) {
    const rect = page.getBoundingClientRect();
    const visibleWidth = Math.max(
      0,
      Math.min(rect.right, viewportRect.right) -
        Math.max(rect.left, viewportRect.left)
    );
    const visibleHeight = Math.max(
      0,
      Math.min(rect.bottom, viewportRect.bottom) -
        Math.max(rect.top, viewportRect.top)
    );
    const area = visibleWidth * visibleHeight;

    if (area > bestArea) {
      bestArea = area;
      best = page;
    }
  });

  return best || pages[0];
}

function selectedDocumentBlock(documentObject, pagesHost) {
  if (!documentObject || !pagesHost) return null;

  const selection =
    documentObject.getSelection &&
    documentObject.getSelection();

  if (!selection || !selection.rangeCount) return null;

  let node = selection.anchorNode;
  if (node && node.nodeType === 3) node = node.parentElement;

  if (!node || !pagesHost.contains(node)) return null;

  return (
    typeof node.closest === 'function' &&
    node.closest(
      '.page-content p,' +
      '.page-content h1,' +
      '.page-content h2,' +
      '.page-content h3,' +
      '.page-content li,' +
      '.page-content td'
    )
  );
}

function documentIndentState(block, globalObject) {
  if (!block) {
    return Object.freeze({
      left: 0,
      first: 0,
      right: 0
    });
  }

  const style =
    globalObject &&
    typeof globalObject.getComputedStyle === 'function'
      ? globalObject.getComputedStyle(block)
      : block.__computedStyle || {};

  const left = Math.max(
    0,
    parseFloat(style.marginLeft) || 0
  );

  const textIndent =
    parseFloat(style.textIndent) || 0;

  const right = Math.max(
    0,
    parseFloat(style.marginRight) || 0
  );

  return Object.freeze({
    left,
    first: Math.max(0, left + textIndent),
    right
  });
}

function clampIndentState(state, metrics) {
  const contentWidth = Math.max(
    1,
    finiteNumber(metrics && metrics.contentWidth, 644)
  );

  let left = clampNumber(
    state && state.left,
    0,
    contentWidth
  );

  let first = clampNumber(
    state && state.first,
    0,
    contentWidth
  );

  let right = clampNumber(
    state && state.right,
    0,
    contentWidth
  );

  const occupiedLeft = Math.max(left, first);
  const maximumRight = Math.max(
    0,
    contentWidth - occupiedLeft - 4
  );

  right = Math.min(right, maximumRight);

  const maximumLeft = Math.max(
    0,
    contentWidth - right - 4
  );

  left = Math.min(left, maximumLeft);
  first = Math.min(first, maximumLeft);

  return Object.freeze({ left, first, right });
}

function pointerToDocumentIndent(clientX, metrics) {
  if (!metrics) return 0;

  const localPage = (
    finiteNumber(clientX, metrics.rect.left) -
    metrics.rect.left
  ) / Math.max(metrics.zoom, 0.001);

  return clampNumber(
    localPage - metrics.paddingLeft,
    0,
    metrics.contentWidth
  );
}

function applyDocumentIndent(block, state, pagesHost) {
  if (!block) return false;

  block.style.marginLeft = state.left + 'px';
  block.style.textIndent = (state.first - state.left) + 'px';
  block.style.marginRight = state.right + 'px';

  if (
    pagesHost &&
    typeof pagesHost.dispatchEvent === 'function'
  ) {
    let event = null;

    if (typeof global.Event === 'function') {
      event = new global.Event('input', {
        bubbles: true,
        cancelable: false
      });
    } else if (
      pagesHost.ownerDocument &&
      typeof pagesHost.ownerDocument.createEvent === 'function'
    ) {
      event = pagesHost.ownerDocument.createEvent('Event');
      event.initEvent('input', true, false);
    }

    if (event) pagesHost.dispatchEvent(event);
  }

  return true;
}

function installDocumentsRuler(documentObject) {
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
  let drag = null;
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

    rulerTickModel(nextMetrics.pageWidth, 96).forEach(
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
    const state = clampIndentState(nextState, metrics);
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
    const block = selectedDocumentBlock(
      documentObject,
      pagesHost
    );

    return {
      block,
      state: clampIndentState(
        documentIndentState(block, global),
        metrics
      )
    };
  }

  function sync() {
    frame = 0;

    const page = visibleDocumentPage(
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
    metrics = rulerMetrics(page, global);

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

  function startDrag(event) {
    const target =
      event.target &&
      typeof event.target.closest === 'function' &&
      event.target.closest('.ruler-handle');

    if (!target || !track.contains(target)) return;

    scheduleSync();
    sync();

    if (!metrics) return;

    const selected = currentBlockState();

    if (!selected.block) {
      const status =
        documentObject.getElementById('statusText');
      if (status) {
        status.textContent =
          'Place the cursor in a paragraph before changing indentation.';
      }
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }

    const kind =
      target.id === 'firstIndent'
        ? 'first'
        : target.id === 'hangingIndent'
          ? 'hanging'
          : target.id === 'leftIndent'
            ? 'left'
            : target.id === 'rightIndent'
              ? 'right'
              : '';

    if (!kind) return;

    drag = {
      kind,
      pointerId: event.pointerId,
      startClientX: event.clientX,
      block: selected.block,
      initial: selected.state,
      state: selected.state,
      metrics
    };

    if (
      typeof target.setPointerCapture === 'function'
    ) {
      try {
        target.setPointerCapture(event.pointerId);
      } catch (error) {
        /* Window listeners still preserve dragging. */
      }
    }

    event.preventDefault();
    event.stopImmediatePropagation();
  }

  function moveDrag(event) {
    if (
      !drag ||
      (
        drag.pointerId !== undefined &&
        event.pointerId !== undefined &&
        drag.pointerId !== event.pointerId
      )
    ) {
      return;
    }

    const nextMetrics =
      rulerMetrics(activePage, global) ||
      drag.metrics;

    const state = {
      left: drag.state.left,
      first: drag.state.first,
      right: drag.state.right
    };

    const local = pointerToDocumentIndent(
      event.clientX,
      nextMetrics
    );

    if (drag.kind === 'first') {
      state.first = local;
    } else if (drag.kind === 'hanging') {
      state.left = local;
    } else if (drag.kind === 'left') {
      const delta =
        (
          event.clientX -
          drag.startClientX
        ) / Math.max(nextMetrics.zoom, 0.001);

      state.left =
        drag.initial.left + delta;
      state.first =
        drag.initial.first + delta;
    } else if (drag.kind === 'right') {
      state.right =
        nextMetrics.contentWidth - local;
    }

    drag.state = clampIndentState(
      state,
      nextMetrics
    );

    metrics = nextMetrics;
    updateHandles(drag.state);
    applyDocumentIndent(
      drag.block,
      drag.state,
      pagesHost
    );

    const status =
      documentObject.getElementById('statusText');

    if (status) {
      status.textContent =
        'Paragraph indentation updated';
    }

    event.preventDefault();
    event.stopImmediatePropagation();
  }

  function endDrag(event) {
    if (!drag) return;

    if (
      drag.pointerId !== undefined &&
      event.pointerId !== undefined &&
      drag.pointerId !== event.pointerId
    ) {
      return;
    }

    drag = null;
    scheduleSync();

    event.preventDefault();
    event.stopImmediatePropagation();
  }

  ruler.addEventListener(
    'pointerdown',
    startDrag,
    true
  );

  global.addEventListener(
    'pointermove',
    moveDrag,
    true
  );

  global.addEventListener(
    'pointerup',
    endDrag,
    true
  );

  global.addEventListener(
    'pointercancel',
    endDrag,
    true
  );

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
      global.removeEventListener(
        'pointermove',
        moveDrag,
        true
      );
      global.removeEventListener(
        'pointerup',
        endDrag,
        true
      );
      global.removeEventListener(
        'pointercancel',
        endDrag,
        true
      );
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
  function applyDocuments(documentObject) {
    const workspace = documentObject.querySelector('.workspace');
    const button = documentObject.getElementById('sidebarBtn');
    if (!workspace) return false;

    const open = resolvedPreference(
      'documents.sidebar',
      MODULE_DEFAULTS.documents.sidebar
    );

    workspace.classList.toggle('sidebar-hidden', !open);
    setExpanded(button, open);

    if (button) {
      button.title = open ? 'Hide navigation panel' : 'Show navigation panel';
      button.setAttribute(
        'aria-label',
        open ? 'Hide navigation panel' : 'Show navigation panel'
      );

      button.addEventListener('click', function () {
        global.setTimeout(function () {
          const currentlyOpen = !workspace.classList.contains('sidebar-hidden');
          safeSessionSet('documents.sidebar', currentlyOpen);
          setExpanded(button, currentlyOpen);
          button.title = currentlyOpen
            ? 'Hide navigation panel'
            : 'Show navigation panel';
          button.setAttribute(
            'aria-label',
            currentlyOpen
              ? 'Hide navigation panel'
              : 'Show navigation panel'
          );
        }, 0);
      });
    }

    installDocumentsRuler(documentObject);
    return true;
  }

  function applyPresentations(documentObject) {
    const app = documentObject.getElementById('app');
    const workspace = documentObject.querySelector('.workspace');
    if (!app || !workspace) return false;

    const thumbnailsOpen = resolvedPreference(
      'presentations.thumbnails',
      MODULE_DEFAULTS.presentations.thumbnails
    );
    const inspectorOpen = resolvedPreference(
      'presentations.inspector',
      MODULE_DEFAULTS.presentations.inspector
    );
    const notesOpen = resolvedPreference(
      'presentations.notes',
      MODULE_DEFAULTS.presentations.notes
    );

    workspace.classList.toggle('hide-slides', !thumbnailsOpen);
    workspace.classList.toggle('hide-inspector', !inspectorOpen);
    app.classList.toggle('hide-notes', !notesOpen);

    const thumbnailsButton =
      documentObject.getElementById('togglePresentationsBtn');
    const inspectorButton =
      documentObject.getElementById('toggleInspectorBtn');
    const notesButton =
      documentObject.getElementById('toggleNotesBtn');

    function syncButtons() {
      const currentThumbnails =
        !workspace.classList.contains('hide-slides');
      const currentInspector =
        !workspace.classList.contains('hide-inspector');
      const currentNotes =
        !app.classList.contains('hide-notes');

      if (thumbnailsButton) {
        thumbnailsButton.textContent = currentThumbnails
          ? 'Hide thumbnails'
          : 'Show thumbnails';
        setExpanded(thumbnailsButton, currentThumbnails);
      }

      if (inspectorButton) {
        inspectorButton.textContent = currentInspector
          ? 'Hide format panel'
          : 'Show format panel';
        setExpanded(inspectorButton, currentInspector);
      }

      if (notesButton) {
        notesButton.textContent = currentNotes
          ? 'Hide presenter notes'
          : 'Show presenter notes';
        setExpanded(notesButton, currentNotes);
      }
    }

    syncButtons();

    if (thumbnailsButton) {
      thumbnailsButton.addEventListener('click', function () {
        global.setTimeout(function () {
          const current =
            !workspace.classList.contains('hide-slides');
          safeSessionSet('presentations.thumbnails', current);
          syncButtons();
        }, 0);
      });
    }

    if (inspectorButton) {
      inspectorButton.addEventListener('click', function () {
        global.setTimeout(function () {
          const current =
            !workspace.classList.contains('hide-inspector');
          safeSessionSet('presentations.inspector', current);
          syncButtons();
        }, 0);
      });
    }

    if (notesButton) {
      notesButton.addEventListener('click', function () {
        global.setTimeout(function () {
          const current =
            !app.classList.contains('hide-notes');
          safeSessionSet('presentations.notes', current);
          syncButtons();
        }, 0);
      });
    }

    return true;
  }

  function applyPdf(documentObject) {
    const startScreen = documentObject.getElementById('startScreen');
    const openButton = documentObject.getElementById('openBtn');
    const workspace = documentObject.getElementById('workspaceBody');
    const sidebar = documentObject.getElementById('sidebar');
    const toggle = documentObject.getElementById('sidebarToggle');

    if (startScreen) {
      startScreen.dataset.inkdeskEmptyState = 'centered';
    }

    if (openButton) {
      openButton.dataset.inkdeskPrimaryAction = 'open-document';
    }

    function setSidebarOpen(open, persist) {
      if (!workspace) return false;

      const shouldOpen = Boolean(open);
      workspace.classList.toggle('sidebar-collapsed', !shouldOpen);
      workspace.dataset.inkdeskPdfSidebar = shouldOpen ? 'open' : 'closed';

      if (sidebar) {
        sidebar.setAttribute(
          'aria-hidden',
          shouldOpen ? 'false' : 'true'
        );
        if ('inert' in sidebar) sidebar.inert = !shouldOpen;
      }

      if (toggle) {
        toggle.classList.toggle('active', shouldOpen);
        setExpanded(toggle, shouldOpen);
        toggle.title = shouldOpen
          ? 'Hide navigation panel'
          : 'Show navigation panel';
        toggle.setAttribute(
          'aria-label',
          shouldOpen
            ? 'Hide navigation panel'
            : 'Show navigation panel'
        );
      }

      if (persist) {
        safeSessionSet('pdf.sidebar', shouldOpen);
      }

      global.setTimeout(function () {
        try {
          global.dispatchEvent(new Event('resize'));
        } catch (error) {
          /* Resize dispatch is only a layout hint. */
        }
      }, 0);

      return shouldOpen;
    }

    const initialOpen = resolvedPreference(
      'pdf.sidebar',
      MODULE_DEFAULTS.pdf.sidebar
    );
    setSidebarOpen(initialOpen, false);

    if (
      toggle &&
      toggle.dataset.inkdeskPdfSidebarController !== VERSION
    ) {
      toggle.dataset.inkdeskPdfSidebarController = VERSION;

      toggle.addEventListener(
        'click',
        function (event) {
          event.preventDefault();
          event.stopImmediatePropagation();

          const currentlyOpen = workspace
            ? !workspace.classList.contains('sidebar-collapsed')
            : false;

          setSidebarOpen(!currentlyOpen, true);
        },
        true
      );
    }

    return Boolean(
      startScreen ||
      openButton ||
      workspace ||
      sidebar ||
      toggle
    );
  }

  function applySpreadsheet(documentObject) {
    const formulaRow = documentObject.querySelector('.formula-row');
    const footer = documentObject.querySelector('body > footer');

    if (formulaRow) {
      formulaRow.dataset.inkdeskFormulaBar = 'primary';
    }

    if (footer) {
      footer.dataset.inkdeskStatusLayout = 'sheets-left-zoom-right';
    }

    return Boolean(formulaRow || footer);
  }

  function apply(documentObject) {
    const doc = documentObject || global.document;
    if (!doc || !doc.body || !doc.querySelector) return false;
    if (doc.body.dataset.inkdeskWorkspaceLayout === VERSION) return true;

    const currentModule = moduleId(doc);
    let applied = false;

    if (currentModule === 'documents') {
      applied = applyDocuments(doc);
    } else if (currentModule === 'presentations') {
      applied = applyPresentations(doc);
    } else if (currentModule === 'spreadsheets') {
      applied = applySpreadsheet(doc);
    } else if (currentModule === 'pdf') {
      applied = applyPdf(doc);
    }

    doc.body.dataset.inkdeskWorkspaceLayout = VERSION;
    notify(doc, currentModule);

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
    moduleId,
    resolvedPreference,
    rulerTickModel,
    rulerMetrics,
    visibleDocumentPage,
    documentIndentState,
    clampIndentState,
    pointerToDocumentIndent,
    applyDocumentIndent,
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

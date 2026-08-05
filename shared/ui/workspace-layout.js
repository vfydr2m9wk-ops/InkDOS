(function (global) {
  'use strict';

  const VERSION = '0.19.4.5';
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
    resolvedPreference
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

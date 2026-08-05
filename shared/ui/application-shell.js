(function (global) {
  'use strict';

  const VERSION = '0.19.4.3';

  const MODULE_CLASSES = Object.freeze({
    'office-documents': 'documents',
    'office-spreadsheets': 'spreadsheets',
    'office-presentations': 'presentations',
    'office-pdf': 'pdf',
    'office-epub': 'epub',
    'office-text': 'text'
  });

  const REGION_SELECTORS = Object.freeze({
    titlebar: 'header.topbar, header.titlebar, .titlebar',
    commandTabs: 'nav.toolbar',
    commandbar: '.formatbar, section.toolbar, section.tools, .formula-row',
    workspace: '.workspace, #workspace, .stage-wrap, .viewer-workspace, .pdf-workspace',
    statusbar: '.statusbar, main.app > footer, body > footer'
  });

  const PANEL_SELECTORS = Object.freeze([
    ['sidebar', '.sidebar', 'left'],
    ['slides', '.slide-list', 'left'],
    ['inspector', '.inspector', 'right'],
    ['notes', '.notes-panel', 'bottom'],
    ['pdf-navigation', '.viewer-sidebar, .pdf-sidebar, #sidebar', 'left']
  ]);

  function asArray(value) {
    return Array.prototype.slice.call(value || []);
  }

  function moduleIdFromBody(body) {
    if (!body || !body.classList) return '';
    for (const className of Object.keys(MODULE_CLASSES)) {
      if (body.classList.contains(className)) return MODULE_CLASSES[className];
    }
    return String(body.dataset && body.dataset.inkdeskModule || '');
  }

  function dispatch(target, name, detail) {
    if (!target || typeof target.dispatchEvent !== 'function') return;
    let event = null;
    if (typeof global.CustomEvent === 'function') {
      event = new global.CustomEvent(name, { detail });
    } else if (target.ownerDocument && typeof target.ownerDocument.createEvent === 'function') {
      event = target.ownerDocument.createEvent('CustomEvent');
      event.initCustomEvent(name, false, false, detail);
    }
    if (event) target.dispatchEvent(event);
  }

  function setAttributeIfMissing(element, name, value) {
    if (!element || typeof element.hasAttribute !== 'function') return;
    if (!element.hasAttribute(name)) element.setAttribute(name, value);
  }

  function visibleByMarkup(element) {
    if (!element || element.hidden) return false;
    if (element.classList && element.classList.contains('hidden')) return false;
    if (element.classList && element.classList.contains('inkdesk-panel-collapsed')) return false;
    return true;
  }

  function createCommandRegistry(eventTarget) {
    const commands = new Map();

    function register(id, handler, options) {
      const commandId = String(id || '').trim();
      if (!/^[a-z][a-z0-9.-]*$/.test(commandId)) {
        throw new Error('Invalid InkDesk command ID.');
      }
      if (typeof handler !== 'function') {
        throw new TypeError('Command handlers must be functions.');
      }
      if (commands.has(commandId)) {
        throw new Error('Command is already registered: ' + commandId);
      }

      const definition = Object.freeze({
        id: commandId,
        handler,
        enabled: !options || options.enabled !== false,
        label: String(options && options.label || commandId)
      });

      commands.set(commandId, definition);
      dispatch(eventTarget, 'inkdesk:command-registered', { command: definition });

      return function unregister() {
        commands.delete(commandId);
      };
    }

    function execute(id, context) {
      const command = commands.get(String(id || ''));
      if (!command) throw new Error('Unknown InkDesk command: ' + id);
      if (!command.enabled) return false;
      const result = command.handler(context || {});
      dispatch(eventTarget, 'inkdesk:command-executed', { id: command.id });
      return result;
    }

    return Object.freeze({
      register,
      execute,
      has: function (id) { return commands.has(String(id || '')); },
      list: function () { return Array.from(commands.values()); }
    });
  }

  function createPanelController(eventTarget) {
    const panels = new Map();

    function register(id, element, options) {
      const panelId = String(id || '').trim();
      if (!/^[a-z][a-z0-9-]*$/.test(panelId)) {
        throw new Error('Invalid InkDesk panel ID.');
      }
      if (!element || !element.classList) {
        throw new TypeError('A panel requires a DOM element.');
      }
      if (panels.has(panelId)) return panels.get(panelId);

      const side = String(options && options.side || 'left');
      element.dataset.inkdeskPanel = panelId;
      element.dataset.inkdeskPanelSide = side;
      setAttributeIfMissing(
        element,
        'aria-label',
        String(options && options.label || panelId)
      );

      const record = { id: panelId, element, side };
      panels.set(panelId, record);
      return record;
    }

    function isOpen(id) {
      const panel = panels.get(String(id || ''));
      return Boolean(panel && visibleByMarkup(panel.element));
    }

    function setOpen(id, open, options) {
      const panel = panels.get(String(id || ''));
      if (!panel) return false;

      const shouldOpen = Boolean(open);
      panel.element.classList.toggle('inkdesk-panel-collapsed', !shouldOpen);
      panel.element.setAttribute('aria-hidden', shouldOpen ? 'false' : 'true');

      const controls = eventTarget && eventTarget.querySelectorAll
        ? asArray(
            eventTarget.querySelectorAll(
              '[aria-controls="' + panel.element.id + '"]'
            )
          )
        : [];

      controls.forEach(function (control) {
        control.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
      });

      if (shouldOpen && options && options.focus) {
        const focusTarget = panel.element.querySelector &&
          panel.element.querySelector(
            'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
        if (focusTarget && typeof focusTarget.focus === 'function') {
          focusTarget.focus();
        }
      }

      dispatch(eventTarget, 'inkdesk:panel-change', {
        id: panel.id,
        open: shouldOpen,
        side: panel.side
      });
      return true;
    }

    return Object.freeze({
      register,
      isOpen,
      setOpen,
      toggle: function (id, options) {
        return setOpen(id, !isOpen(id), options);
      },
      list: function () {
        return Array.from(panels.values()).map(function (panel) {
          return Object.freeze({
            id: panel.id,
            side: panel.side,
            open: isOpen(panel.id),
            element: panel.element
          });
        });
      }
    });
  }

  function annotateRegions(root) {
    const regions = {};

    function first(selector) {
      return root.querySelector ? root.querySelector(selector) : null;
    }

    const titlebar = first(REGION_SELECTORS.titlebar);
    if (titlebar) {
      titlebar.dataset.inkdeskShellRegion = 'titlebar';
      setAttributeIfMissing(titlebar, 'aria-label', 'Application title bar');
      regions.titlebar = titlebar;
    }

    const commandTabs = first(REGION_SELECTORS.commandTabs);
    if (commandTabs) {
      commandTabs.dataset.inkdeskShellRegion = 'command-tabs';
      setAttributeIfMissing(commandTabs, 'aria-label', 'Command categories');
      regions.commandTabs = commandTabs;
    }

    const commandBars = root.querySelectorAll
      ? asArray(root.querySelectorAll(REGION_SELECTORS.commandbar))
      : [];

    commandBars.forEach(function (element) {
      if (element === commandTabs) return;
      element.dataset.inkdeskShellRegion = 'commandbar';
      setAttributeIfMissing(element, 'aria-label', 'Workspace commands');
    });
    regions.commandBars = commandBars;

    const workspaces = root.querySelectorAll
      ? asArray(root.querySelectorAll(REGION_SELECTORS.workspace))
      : [];

    workspaces.forEach(function (element) {
      element.dataset.inkdeskShellRegion = 'workspace';
    });
    regions.workspaces = workspaces;

    const statusbar = first(REGION_SELECTORS.statusbar);
    if (statusbar) {
      statusbar.dataset.inkdeskShellRegion = 'statusbar';
      setAttributeIfMissing(statusbar, 'aria-label', 'Workspace status');
      regions.statusbar = statusbar;
    }

    return Object.freeze(regions);
  }

  function inferPanels(root, controller) {
    const registeredElements = new Set();

    PANEL_SELECTORS.forEach(function (definition) {
      const baseId = definition[0];
      const selector = definition[1];
      const side = definition[2];
      const matches = root.querySelectorAll
        ? asArray(root.querySelectorAll(selector))
        : [];

      matches.forEach(function (element, index) {
        if (registeredElements.has(element)) return;
        registeredElements.add(element);
        const id = matches.length > 1 ? baseId + '-' + (index + 1) : baseId;
        controller.register(id, element, {
          side,
          label: baseId.replace(/-/g, ' ')
        });
      });
    });
  }

  function ensureAnnouncer(documentObject) {
    if (!documentObject || !documentObject.body) return null;

    let announcer = documentObject.querySelector('.inkdesk-shell-announcer');
    if (announcer) return announcer;

    announcer = documentObject.createElement('div');
    announcer.className = 'inkdesk-shell-announcer';
    announcer.setAttribute('role', 'status');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    documentObject.body.appendChild(announcer);
    return announcer;
  }

  function createApplicationShell(documentObject, options) {
    const doc = documentObject || global.document;
    if (!doc || !doc.body || !doc.querySelector) return null;
    if (doc.body.__inkdeskApplicationShell) {
      return doc.body.__inkdeskApplicationShell;
    }

    const moduleId = String(
      options && options.moduleId ||
      moduleIdFromBody(doc.body) ||
      'unknown'
    );

    const regions = annotateRegions(doc);
    const panels = createPanelController(doc);
    inferPanels(doc, panels);
    const commands = createCommandRegistry(doc);
    const announcer = ensureAnnouncer(doc);

    doc.documentElement.classList.add('inkdesk');
    doc.body.dataset.inkdeskModule = moduleId;
    doc.body.dataset.inkdeskShell = 'ready';

    function announce(message) {
      if (!announcer) return;
      announcer.textContent = '';
      global.setTimeout(function () {
        announcer.textContent = String(message || '');
      }, 0);
    }

    function setStatus(message) {
      const text = String(message || '');
      const candidates = [
        doc.getElementById && doc.getElementById('statusText'),
        doc.getElementById && doc.getElementById('selectionStats'),
        doc.getElementById && doc.getElementById('stateBadge')
      ].filter(Boolean);

      if (candidates[0]) candidates[0].textContent = text;
      announce(text);
      dispatch(doc, 'inkdesk:status-change', { message: text });
    }

    function setFileState(state) {
      const value = state || {};

      if (Object.prototype.hasOwnProperty.call(value, 'dirty')) {
        doc.body.dataset.inkdeskDirty = value.dirty ? 'true' : 'false';
      }

      if (Object.prototype.hasOwnProperty.call(value, 'canSave')) {
        doc.body.dataset.inkdeskCanSave = value.canSave ? 'true' : 'false';
      }

      dispatch(doc, 'inkdesk:file-state-change', {
        name: String(value.name || ''),
        dirty: value.dirty === true,
        canSave: value.canSave === true
      });
    }

    const shell = Object.freeze({
      version: VERSION,
      moduleId,
      regions,
      panels,
      commands,
      announce,
      setStatus,
      setFileState
    });

    Object.defineProperty(doc.body, '__inkdeskApplicationShell', {
      value: shell,
      configurable: true
    });

    global.InkDeskShell = shell;
    dispatch(doc, 'inkdesk:shell-ready', {
      shell,
      moduleId,
      version: VERSION
    });

    return shell;
  }

  function autoInitialize() {
    try {
      if (!global.document || !global.document.body) return null;
      if (!global.document.body.classList.contains('office-product')) return null;
      return createApplicationShell(global.document);
    } catch (error) {
      if (global.document && global.document.body) {
        global.document.body.dataset.inkdeskShellError = 'true';
      }
      if (global.console && typeof global.console.error === 'function') {
        global.console.error(
          'InkDesk application shell initialization failed.',
          error
        );
      }
      return null;
    }
  }

  const api = Object.freeze({
    version: VERSION,
    selectors: REGION_SELECTORS,
    createCommandRegistry,
    createPanelController,
    createApplicationShell,
    moduleIdFromBody,
    autoInitialize
  });

  global.InkDeskUI = api;
  global.InkDeskCreateApplicationShell = createApplicationShell;

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

(function (global) {
  'use strict';

  const VERSION = '1.0.0-beta.9';

  function documentKey(file) {
    return [
      'txt',
      String(file && file.name || 'Untitled.txt'),
      Number(file && file.size || 0),
      Number(file && file.lastModified || 0)
    ].join(':');
  }

  function create(options) {
    const editor = options.editor;
    const state = options.state;
    const lifecycle = options.lifecycle;
    const history = options.history;
    const setTitle = options.setTitle;
    const showEditor = options.showEditor;
    const updateCounts = options.updateCounts;
    const setWorkspaceZoom = options.setWorkspaceZoom;
    const setStatus = options.setStatus;
    const normalizeText = options.normalizeText;

    function capture() {
      return {
        text: editor.value,
        fileName: state.fileName,
        lineEnding: state.lineEnding,
        encoding: state.encoding,
        workspaceZoom: state.workspaceZoom
      };
    }

    async function restore(context) {
      const snapshot = context && context.snapshot;
      const payload = snapshot && snapshot.payload;
      if (!payload || typeof payload.text !== 'string') {
        throw new Error('The TXT recovery snapshot is invalid.');
      }
      editor.value = normalizeText(payload.text);
      state.lineEnding = ['\n', '\r\n', '\r'].includes(payload.lineEnding)
        ? payload.lineEnding
        : '\n';
      state.encoding = String(payload.encoding || 'UTF-8');
      setTitle(payload.fileName || snapshot.fileName || 'Recovered.txt');
      options.encodingLabel.textContent = state.encoding;
      showEditor();
      lifecycle.sourceOpened();
      lifecycle.markDirty();
      history.reset();
      updateCounts();
      setWorkspaceZoom(payload.workspaceZoom || 100);
      setStatus('Recovered unsaved TXT work from this browser');
      editor.focus();
    }

    const manager = global.InkDOSLocalRecovery
      ? global.InkDOSLocalRecovery.create({
          module: 'txt',
          appVersion: VERSION,
          defaultFileName: 'Untitled.txt',
          serialize: capture,
          restore,
          status(message) {
            if (message && /restored|failed/i.test(message)) setStatus(message);
          }
        })
      : null;

    async function beforeReplace() {
      if (!manager) return;
      manager.cancelPrompt();
      await manager.discardCurrent();
    }

    async function startNew(fileName) {
      if (!manager) return;
      await manager.startDocument({fileName, resetSnapshots: true});
    }

    async function startFile(file, fileName) {
      if (!manager) return;
      await manager.startDocument({
        documentKey: documentKey(file),
        fileName,
        resetSnapshots: true
      });
    }

    const api = Object.freeze({
      beforeReplace,
      startNew,
      startFile,
      markDirty() { if (manager) manager.markDirty(); },
      rename(fileName) {
        if (!manager) return;
        manager.updateFileName(fileName);
        manager.markDirty();
      },
      async flush() { if (manager) await manager.flush(); },
      capture,
      restore,
      manager
    });

    if (manager) manager.promptLatest();
    global.__InkDOSTxtRecovery = api;
    return api;
  }

  global.InkDOSTxtRecoveryController = Object.freeze({VERSION, create});
})(window);

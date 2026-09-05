(function (global) {
  'use strict';
  document.body.dataset.inkdosDocumentSession = 'ready';
  const MAX_FILE_BYTES = 20 * 1024 * 1024;
  const E = {
    newBtn: document.getElementById('newBtn'),
    openBtn: document.getElementById('openBtn'),
    undoBtn: document.getElementById('undoBtn'),
    redoBtn: document.getElementById('redoBtn'),
    saveBtn: document.getElementById('saveBtn'),
    docTitle: document.getElementById('docTitle'),
    dirtyMark: document.getElementById('dirtyMark'),
    wrapBtn: document.getElementById('wrapBtn'),
    fontSize: document.getElementById('fontSize'),
    findBtn: document.getElementById('findBtn'),
    findBar: document.getElementById('findBar'),
    findInput: document.getElementById('findInput'),
    findPrevious: document.getElementById('findPrevious'),
    findNext: document.getElementById('findNext'),
    findClose: document.getElementById('findClose'),
    findStatus: document.getElementById('findStatus'),
    startScreen: document.getElementById('startScreen'),
    newStartBtn: document.getElementById('newStartBtn'),
    openStartBtn: document.getElementById('openStartBtn'),
    editorShell: document.getElementById('editorShell'),
    editor: document.getElementById('editor'),
    statusText: document.getElementById('statusText'),
    lineCount: document.getElementById('lineCount'),
    wordCount: document.getElementById('wordCount'),
    characterCount: document.getElementById('characterCount'),
    encodingLabel: document.getElementById('encodingLabel'),
    txtZoomOut: document.getElementById('txtZoomOut'),
    txtZoomSlider: document.getElementById('txtZoomSlider'),
    txtZoomIn: document.getElementById('txtZoomIn'),
    txtFit: document.getElementById('txtFit'),
    txtZoomLabel: document.getElementById('txtZoomLabel'),
    fileInput: document.getElementById('fileInput')
  };
  const state = {
    loaded: false,
    fileName: 'Untitled.txt',
    lineEnding: '\n',
    encoding: 'UTF-8',
    workspaceZoom: 100
  };
  const lifecycle = global.InkDOSFileLifecycle.create({
    onChange(value) {
      const dirty = value.shouldWarnBeforeUnload;
      E.dirtyMark.hidden = !dirty;
      E.saveBtn.disabled = !state.loaded;
      document.title =
        state.fileName +
        (dirty ? ' •' : '') +
        ' — Plain Text';
    }
  });
  function setStatus(message) {
    E.statusText.textContent = String(message || 'Ready');
  }
  function normalizeName(value) {
    let name = String(value || '').trim() || 'Untitled.txt';
    name = name.replace(/[\\/:*?"<>|]+/g, '-');
    if (!/\.txt$/i.test(name)) name += '.txt';
    return name;
  }
  function setTitle(value) {
    state.fileName = normalizeName(value);
    E.docTitle.value = state.fileName;
    document.title =
      state.fileName +
      (lifecycle.shouldWarnBeforeUnload() ? ' •' : '') +
      ' — Plain Text';
    return state.fileName;
  }
  function commitTitle() {
    const previous = state.fileName;
    const next = setTitle(E.docTitle.value);
    if (state.loaded && next !== previous) {
      if (!lifecycle.shouldWarnBeforeUnload()) lifecycle.markDirty();
      recovery.rename(next);
      setStatus('File renamed to ' + next);
    }
  }
  function confirmDiscard() {
    return lifecycle.confirmDiscard(
      'This text file has unsaved changes. Continue and discard them?'
    );
  }
  function showEditor() {
    E.startScreen.hidden = true;
    E.editorShell.hidden = false;
    E.saveBtn.disabled = false;
    state.loaded = true;
  }
  function showStart() {
    E.startScreen.hidden = false;
    E.editorShell.hidden = true;
    E.saveBtn.disabled = true;
    state.loaded = false;
  }

  function updateCounts() {
    const text = E.editor.value;
    const lines = text.length ? text.split('\n').length : 1;
    const words = text.trim()
      ? text.trim().split(/\s+/u).filter(Boolean).length
      : 0;

    E.lineCount.textContent =
      lines + (lines === 1 ? ' line' : ' lines');
    E.wordCount.textContent =
      words + (words === 1 ? ' word' : ' words');
    E.characterCount.textContent =
      text.length +
      (text.length === 1 ? ' character' : ' characters');
  }

  const historyController = global.InkDOSTxtHistoryController.createHistoryController({
    editor: E.editor,
    undoButton: E.undoBtn,
    redoButton: E.redoBtn,
    onRestore: updateCounts,
    shouldWarnBeforeUnload: function () {
      return lifecycle.shouldWarnBeforeUnload();
    },
    markDirty: function () {
      lifecycle.markDirty();
    }
  });

  function detectLineEnding(text) {
    if (text.includes('\r\n')) return '\r\n';
    if (text.includes('\r')) return '\r';
    return '\n';
  }

  function decodeText(buffer) {
    const bytes = new Uint8Array(buffer);

    if (
      bytes.length >= 2 &&
      bytes[0] === 0xff &&
      bytes[1] === 0xfe
    ) {
      return {
        text: new TextDecoder('utf-16le').decode(bytes.subarray(2)),
        encoding: 'UTF-16 LE'
      };
    }

    if (
      bytes.length >= 2 &&
      bytes[0] === 0xfe &&
      bytes[1] === 0xff
    ) {
      const swapped = new Uint8Array(bytes.length - 2);
      for (let index = 2; index + 1 < bytes.length; index += 2) {
        swapped[index - 2] = bytes[index + 1];
        swapped[index - 1] = bytes[index];
      }
      return {
        text: new TextDecoder('utf-16le').decode(swapped),
        encoding: 'UTF-16 BE'
      };
    }

    let start = 0;
    if (
      bytes.length >= 3 &&
      bytes[0] === 0xef &&
      bytes[1] === 0xbb &&
      bytes[2] === 0xbf
    ) {
      start = 3;
    }

    return {
      text: new TextDecoder('utf-8').decode(bytes.subarray(start)),
      encoding: 'UTF-8'
    };
  }

  function normalizeEditorText(text) {
    return String(text || '')
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n');
  }



  async function newDocument() {
    if (!confirmDiscard()) return;
    await recovery.beforeReplace();

    setTitle('Untitled.txt');
    state.lineEnding = '\n';
    state.encoding = 'UTF-8';
    E.encodingLabel.textContent = state.encoding;
    E.editor.value = '';

    showEditor();
    lifecycle.sourceOpened();
    historyController.reset();
    await recovery.startNew(state.fileName);
    updateCounts();
    setStatus('New text file');
    E.editor.focus();
  }

  async function openFile(file) {
    if (!(file instanceof Blob)) {
      throw new TypeError('A TXT file is required.');
    }

    const name = String(file.name || 'Untitled.txt');
    if (!/\.txt$/i.test(name)) {
      throw new Error('Choose a TXT file.');
    }

    if (!file.size) {
      throw new Error('The selected text file is empty or unavailable.');
    }

    if (file.size > MAX_FILE_BYTES) {
      throw new Error(
        'The selected text file is larger than the 20 MB local editor limit.'
      );
    }

    if (!confirmDiscard()) return;

    setStatus('Opening ' + name + '…');

    const buffer = await file.arrayBuffer();
    const decoded = decodeText(buffer);

    await recovery.beforeReplace();

    state.lineEnding = detectLineEnding(decoded.text);
    state.encoding = decoded.encoding;

    E.editor.value = normalizeEditorText(decoded.text);
    setTitle(name);
    E.encodingLabel.textContent = state.encoding;

    showEditor();
    lifecycle.sourceOpened();
    historyController.reset();
    await recovery.startFile(file, state.fileName);
    updateCounts();

    setStatus(
      'Opened ' +
      state.fileName +
      ' · ' +
      state.encoding
    );

    E.editor.focus();
  }

  function encodeForSave() {
    const text = E.editor.value.replace(/\n/g, state.lineEnding);
    return new Blob([text], {
      type: 'text/plain;charset=utf-8'
    });
  }

  function fallbackDownload(blob, fileName) {
    const anchor = document.createElement('a');
    const url = URL.createObjectURL(blob);

    anchor.href = url;
    anchor.download = fileName;
    anchor.rel = 'noopener';
    anchor.hidden = true;
    document.body.appendChild(anchor);

    try {
      anchor.click();
    } finally {
      anchor.remove();
      setTimeout(function () {
        URL.revokeObjectURL(url);
      }, 15000);
    }

    return {
      fileName,
      bytes: blob.size
    };
  }

  async function saveDocument() {
    if (!state.loaded) return;

    commitTitle();
    setStatus('Saving text copy…');
    lifecycle.beginExport();

    try {
      if (lifecycle.shouldWarnBeforeUnload()) await recovery.flush();
      const blob = encodeForSave();
      const receipt =
        global.InkDOSRuntime &&
        typeof global.InkDOSRuntime.requestDownload === 'function'
          ? global.InkDOSRuntime.requestDownload(
              blob,
              state.fileName
            )
          : fallbackDownload(blob, state.fileName);

      lifecycle.downloadRequested(receipt);
      setStatus(
        lifecycle.shouldWarnBeforeUnload()
          ? 'Download requested — changes remain protected until you verify the TXT copy'
          : 'Download requested · ' + receipt.fileName
      );
    } catch (error) {
      lifecycle.exportFailed(error);
      console.error(error);
      setStatus('Save failed');
      global.alert(
        'InkDOS could not save the TXT copy.\n\n' +
        (error && error.message ? error.message : error)
      );
    }
  }

  function openPicker() {
    E.fileInput.value = '';
    E.fileInput.click();
  }

  function setWrap(enabled) {
    E.editor.classList.toggle('no-wrap', !enabled);
    E.wrapBtn.classList.toggle('active', enabled);
    E.wrapBtn.setAttribute('aria-pressed', String(enabled));
    setStatus(enabled ? 'Word wrap enabled' : 'Word wrap disabled');
  }

  function setFontSize(value) {
    const size = Math.max(12, Math.min(32, Number(value) || 16));
    E.editor.style.setProperty('--txt-font-size', size + 'px');
    setStatus('Text size ' + size);
  }

  function setWorkspaceZoom(value) {
    const zoom = Math.max(50, Math.min(160, Math.round((Number(value) || 100) / 5) * 5));
    state.workspaceZoom = zoom;
    E.editorShell.style.zoom = String(zoom / 100);
    E.txtZoomSlider.value = String(zoom);
    E.txtZoomLabel.textContent = zoom + '%';
  }


  const findController = global.InkDOSTxtFindController.createFindController({
    editor: E.editor,
    button: E.findBtn,
    bar: E.findBar,
    input: E.findInput,
    previousButton: E.findPrevious,
    nextButton: E.findNext,
    closeButton: E.findClose,
    status: E.findStatus
  });


  const recovery = global.InkDOSTxtRecoveryController.create({
    editor: E.editor,
    encodingLabel: E.encodingLabel,
    state,
    lifecycle,
    history: historyController,
    setTitle,
    showEditor,
    updateCounts,
    setWorkspaceZoom,
    setStatus,
    normalizeText: normalizeEditorText
  });

  E.newBtn.addEventListener('click', newDocument);
  E.newStartBtn.addEventListener('click', newDocument);
  E.openBtn.addEventListener('click', openPicker);
  E.openStartBtn.addEventListener('click', openPicker);
  E.saveBtn.addEventListener('click', saveDocument);
  E.undoBtn.addEventListener('click', historyController.undo);
  E.redoBtn.addEventListener('click', historyController.redo);

  E.fileInput.addEventListener('change', function () {
    const file = E.fileInput.files && E.fileInput.files[0];
    if (!file) return;

    openFile(file).catch(function (error) {
      console.error(error);
      setStatus('Open failed');
      global.alert(
        'InkDOS could not open this TXT file.\n\n' +
        (error && error.message ? error.message : error)
      );
    });
  });

  E.editor.addEventListener('input', function () {
    if (!lifecycle.shouldWarnBeforeUnload()) {
      lifecycle.markDirty();
    }
    recovery.markDirty();
    historyController.schedule();
    updateCounts();
  });

  E.docTitle.addEventListener('focus', function () {
    E.docTitle.select();
  });
  E.docTitle.addEventListener('blur', commitTitle);
  E.docTitle.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      E.docTitle.blur();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      E.docTitle.value = state.fileName;
      E.docTitle.blur();
    }
  });

  E.wrapBtn.addEventListener('click', function () {
    setWrap(
      E.wrapBtn.getAttribute('aria-pressed') !== 'true'
    );
  });

  E.fontSize.addEventListener('change', function () {
    setFontSize(E.fontSize.value);
  });

  E.txtZoomOut.addEventListener('click', function () { setWorkspaceZoom(state.workspaceZoom - 10); });
  E.txtZoomSlider.addEventListener('input', function () { setWorkspaceZoom(E.txtZoomSlider.value); });
  E.txtZoomIn.addEventListener('click', function () { setWorkspaceZoom(state.workspaceZoom + 10); });
  E.txtFit.addEventListener('click', function () { setWorkspaceZoom(100); });

  global.addEventListener('keydown', function (event) {
    const modifier = event.ctrlKey || event.metaKey;

    if (modifier && event.key.toLocaleLowerCase() === 's') {
      event.preventDefault();
      saveDocument();
    } else if (
      modifier &&
      event.key.toLocaleLowerCase() === 'f'
    ) {
      event.preventDefault();
      findController.show();
    }
  });

  global.InkDOSWorkspaceOpenFile = openFile;

  if (global.InkDOSFileRouter) {
    global.InkDOSFileRouter.attachWorkspace({
      appId: 'txt',
      openFile
    });
  }

  setTitle('Untitled.txt');
  setWrap(true);
  setFontSize(16);
  setWorkspaceZoom(100);
  showStart();
  updateCounts();


  global.InkDOSTxtDebug = Object.freeze({
    version: '1.0.0-beta.6',
    openFile,
    newDocument,
    saveDocument,
    getState: function () {
      return {
        loaded: state.loaded,
        fileName: state.fileName,
        encoding: state.encoding,
        lineEnding: state.lineEnding,
        dirty: lifecycle.shouldWarnBeforeUnload(),
        characters: E.editor.value.length
      };
    }
  });
})(window);

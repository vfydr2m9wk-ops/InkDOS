(function (global) {
  'use strict';

  document.body.dataset.inkdeskDocumentSession = 'ready';

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
    fileInput: document.getElementById('fileInput')
  };

  const state = {
    loaded: false,
    fileName: 'Untitled.txt',
    lineEnding: '\n',
    encoding: 'UTF-8',
    history: [],
    historyIndex: -1,
    historyTimer: 0,
    restoringHistory: false
  };

  const lifecycle = global.InkDeskFileLifecycle.create({
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

  function updateHistoryButtons() {
    E.undoBtn.disabled = state.historyIndex <= 0;
    E.redoBtn.disabled =
      state.historyIndex < 0 ||
      state.historyIndex >= state.history.length - 1;
  }

  function snapshot() {
    return {
      value: E.editor.value,
      start: E.editor.selectionStart,
      end: E.editor.selectionEnd
    };
  }

  function resetHistory() {
    clearTimeout(state.historyTimer);
    state.history = [snapshot()];
    state.historyIndex = 0;
    updateHistoryButtons();
  }

  function pushHistory() {
    if (state.restoringHistory) return;

    const next = snapshot();
    const current = state.history[state.historyIndex];

    if (
      current &&
      current.value === next.value &&
      current.start === next.start &&
      current.end === next.end
    ) {
      return;
    }

    state.history = state.history.slice(
      0,
      state.historyIndex + 1
    );
    state.history.push(next);

    if (state.history.length > 80) {
      state.history.shift();
    } else {
      state.historyIndex += 1;
    }

    updateHistoryButtons();
  }

  function scheduleHistory() {
    clearTimeout(state.historyTimer);
    state.historyTimer = setTimeout(pushHistory, 180);
  }

  function restoreHistory(index) {
    if (index < 0 || index >= state.history.length) return;

    state.restoringHistory = true;
    state.historyIndex = index;

    const item = state.history[index];
    E.editor.value = item.value;
    E.editor.setSelectionRange(item.start, item.end);

    updateCounts();
    updateHistoryButtons();

    if (!lifecycle.shouldWarnBeforeUnload()) {
      lifecycle.markDirty();
    }

    setTimeout(function () {
      state.restoringHistory = false;
      E.editor.focus();
    }, 0);
  }

  function undo() {
    restoreHistory(state.historyIndex - 1);
  }

  function redo() {
    restoreHistory(state.historyIndex + 1);
  }

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

  function newDocument() {
    if (!confirmDiscard()) return;

    setTitle('Untitled.txt');
    state.lineEnding = '\n';
    state.encoding = 'UTF-8';
    E.encodingLabel.textContent = state.encoding;
    E.editor.value = '';

    showEditor();
    lifecycle.sourceOpened();
    resetHistory();
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

    state.lineEnding = detectLineEnding(decoded.text);
    state.encoding = decoded.encoding;

    E.editor.value = normalizeEditorText(decoded.text);
    setTitle(name);
    E.encodingLabel.textContent = state.encoding;

    showEditor();
    lifecycle.sourceOpened();
    resetHistory();
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

  function saveDocument() {
    if (!state.loaded) return;

    commitTitle();
    setStatus('Saving text copy…');

    try {
      const blob = encodeForSave();
      const receipt =
        global.InkDeskRuntime &&
        typeof global.InkDeskRuntime.requestDownload === 'function'
          ? global.InkDeskRuntime.requestDownload(
              blob,
              state.fileName
            )
          : fallbackDownload(blob, state.fileName);

      lifecycle.resetClean();
      setStatus(
        'Download requested · ' +
        receipt.fileName
      );
    } catch (error) {
      lifecycle.exportFailed(error);
      console.error(error);
      setStatus('Save failed');
      global.alert(
        'InkDesk could not save the TXT copy.\n\n' +
        (error && error.message ? error.message : error)
      );
    }
  }

  function openPicker() {
    if (!confirmDiscard()) return;
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

  function showFind() {
    E.findBar.hidden = false;
    E.findBtn.classList.add('active');
    E.findInput.focus();
    E.findInput.select();
  }

  function hideFind() {
    E.findBar.hidden = true;
    E.findBtn.classList.remove('active');
    E.findStatus.textContent = '';
    E.editor.focus();
  }

  function findText(direction) {
    const query = E.findInput.value;
    if (!query) {
      E.findStatus.textContent = 'Type a search';
      return;
    }

    const source = E.editor.value.toLocaleLowerCase();
    const needle = query.toLocaleLowerCase();
    let index;

    if (direction < 0) {
      const before = Math.max(0, E.editor.selectionStart - 1);
      index = source.lastIndexOf(needle, before);
      if (index < 0) index = source.lastIndexOf(needle);
    } else {
      index = source.indexOf(needle, E.editor.selectionEnd);
      if (index < 0) index = source.indexOf(needle);
    }

    if (index < 0) {
      E.findStatus.textContent = 'No results';
      return;
    }

    E.editor.focus();
    E.editor.setSelectionRange(index, index + query.length);
    E.findStatus.textContent =
      (index + 1) + ' of ' + source.length;
  }

  E.newBtn.addEventListener('click', newDocument);
  E.newStartBtn.addEventListener('click', newDocument);
  E.openBtn.addEventListener('click', openPicker);
  E.openStartBtn.addEventListener('click', openPicker);
  E.saveBtn.addEventListener('click', saveDocument);
  E.undoBtn.addEventListener('click', undo);
  E.redoBtn.addEventListener('click', redo);

  E.fileInput.addEventListener('change', function () {
    const file = E.fileInput.files && E.fileInput.files[0];
    if (!file) return;

    openFile(file).catch(function (error) {
      console.error(error);
      setStatus('Open failed');
      global.alert(
        'InkDesk could not open this TXT file.\n\n' +
        (error && error.message ? error.message : error)
      );
    });
  });

  E.editor.addEventListener('input', function () {
    if (!lifecycle.shouldWarnBeforeUnload()) {
      lifecycle.markDirty();
    }
    scheduleHistory();
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

  E.findBtn.addEventListener('click', function () {
    if (E.findBar.hidden) showFind();
    else hideFind();
  });
  E.findPrevious.addEventListener('click', function () {
    findText(-1);
  });
  E.findNext.addEventListener('click', function () {
    findText(1);
  });
  E.findClose.addEventListener('click', hideFind);
  E.findInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      findText(event.shiftKey ? -1 : 1);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      hideFind();
    }
  });

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
      showFind();
    }
  });

  global.InkDeskWorkspaceOpenFile = openFile;

  if (global.InkDeskFileRouter) {
    global.InkDeskFileRouter.attachWorkspace({
      extensions: ['txt'],
      openFile
    });
  }

  setTitle('Untitled.txt');
  setWrap(true);
  setFontSize(16);
  showStart();
  updateCounts();
  updateHistoryButtons();

  global.InkDeskTxtDebug = Object.freeze({
    version: '0.19.4.14',
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

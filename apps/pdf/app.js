pdfjsLib.GlobalWorkerOptions.workerSrc = '../../shared/vendor/pdfjs/pdf.worker.min.js';

const $ = id => document.getElementById(id);

const E = Object.fromEntries(
  [
    'fileInput',
    'openBtn',
    'openSmall',
    'startScreen',
    'viewerApp',
    'docTitle',
    'dirtyMark',
    'sidebarToggle',
    'workspaceBody',
    'viewerStage',
    'pdfStatus',
    'pdfPages',
    'systemOpenBtn',
    'fullscreenBtn',
    'immersiveExit',
    'prevPage',
    'nextPage',
    'pageNumber',
    'pageCount',
    'zoomOut',
    'zoomIn',
    'zoomSelect',
    'verticalScroll',
    'horizontalScroll',
    'pageList',
    'outlineList',
    'bookmarkList',
    'commentList',
    'bookmarkBtn',
    'saveModifiedPdfBtn',
    'undoReview',
    'statusText',
    'textDialog',
    'textDialogForm',
    'textDialogValue',
    'dialogCancel'
  ].map(id => [id, $(id)])
);

const TEXT_SELECTION_TOOLS = new Set([
  'highlight',
  'underline',
  'comment'
]);

const FREE_ANNOTATION_TOOLS = new Set([
  'marker',
  'text'
]);

const state = {
  file: null,
  url: '',
  doc: null,
  task: null,
  page: 1,
  zoom: 'page-width',
  scale: 1,
  direction: 'vertical',
  tool: 'select',
  pages: new Map(),
  rendered: new Map(),
  thumbs: new Map(),
  wanted: new Set(),
  annotations: [],
  bookmarks: [],
  undo: [],
  fingerprint: '',
  storageKey: '',
  dirty: false,
  observer: null,
  renderEpoch: 0,
  navLockUntil: 0,
  textSelection: null,
  selectionTimer: 0
};

let pageRenderer = null;

const navigationController =
  window.InkDeskPdfNavigationController.createNavigationController({
    state,
    elements: E,
    clamp,
    ensureWindow: pageNumber =>
      pageRenderer.ensureWindow(pageNumber)
  });

const {
  syncNavigation,
  navigateToPage,
  goToDestination,
  renderPageList,
  renderOutline,
  renderBookmarks
} = navigationController;

pageRenderer = window.InkDeskPdfPageRenderer.createPageRenderer({
  state,
  elements: E,
  pdfjs: pdfjsLib,
  clamp,
  isFreeAnnotationTool: tool => FREE_ANNOTATION_TOOLS.has(tool),
  renderPageReview: pageNumber => renderPageReview(pageNumber),
  wireReviewLayer: (layer, pageNumber) =>
    wireReviewLayer(layer, pageNumber),
  goToDestination: destination => goToDestination(destination),
  syncNavigation: () => syncNavigation()
});

const {
  buildPlaceholders,
  destroyRendered,
  rerender
} = pageRenderer;

function status(message) {
  E.statusText.textContent = message;
  E.pdfStatus.textContent = message;
}

function toast(message) {
  status(message);
  E.pdfStatus.classList.remove('ready');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(
    () => E.pdfStatus.classList.add('ready'),
    1400
  );
}

function clamp(number, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, number));
}

function makeId() {
  return (
    crypto.randomUUID?.() ||
    String(Date.now()) + '-' + Math.random().toString(36).slice(2)
  );
}

function cleanName(name) {
  return (
    String(name || 'document.pdf')
      .replace(/[\\/:*?"<>|\u0000-\u001f]/g, '_')
      .slice(0, 180) ||
    'document.pdf'
  );
}

function download(bytes, name, type) {
  const blob =
    bytes instanceof Blob
      ? bytes
      : new Blob([bytes], { type });

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = name;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

async function fingerprint(file) {
  const first = new Uint8Array(
    await file
      .slice(0, Math.min(file.size, 65536))
      .arrayBuffer()
  );

  let hash = 2166136261;

  for (const byte of first) {
    hash ^= byte;
    hash = Math.imul(hash, 16777619);
  }

  return `${file.size.toString(36)}-${(hash >>> 0).toString(36)}`;
}

function saveReview() {
  if (!state.storageKey) return;

  localStorage.setItem(
    state.storageKey,
    JSON.stringify({
      schema:'inkdesk-pdf-review/2',
      fingerprint: state.fingerprint,
      annotations: state.annotations,
      bookmarks: state.bookmarks
    })
  );
}

function loadReview() {
  try {
    const data = JSON.parse(
      localStorage.getItem(state.storageKey) || 'null'
    );

    if (data?.schema === 'inkdesk-pdf-review/2') {
      state.annotations = Array.isArray(data.annotations)
        ? data.annotations
        : [];

      state.bookmarks = Array.isArray(data.bookmarks)
        ? data.bookmarks
        : [];
    }
  } catch (error) {
    console.warn('InkDesk could not load the local PDF review.', error);
  }

  renderSideLists();
}

function markDirty() {
  state.dirty = true;
  E.dirtyMark.hidden = false;
  saveReview();
}

function annotationRects(annotation) {
  if (
    Array.isArray(annotation.rects) &&
    annotation.rects.length
  ) {
    return annotation.rects;
  }

  if (
    Number.isFinite(Number(annotation.x)) &&
    Number.isFinite(Number(annotation.y)) &&
    Number.isFinite(Number(annotation.w)) &&
    Number.isFinite(Number(annotation.h))
  ) {
    return [
      {
        x: Number(annotation.x),
        y: Number(annotation.y),
        w: Number(annotation.w),
        h: Number(annotation.h)
      }
    ];
  }

  return [];
}

function renderPageReview(pageNumber) {
  const shell = state.pages.get(pageNumber);
  const layer = shell?.querySelector('.page-review-layer');
  if (!layer) return;

  layer.replaceChildren();

  for (
    const annotation of state.annotations.filter(
      item => item.page === pageNumber
    )
  ) {
    const rects = annotationRects(annotation);

    rects.forEach((rect, rectIndex) => {
      const element = document.createElement('div');

      element.className =
        `review-annotation ${annotation.type}` +
        (annotation.source === 'text-selection'
          ? ' text-selection-segment'
          : '') +
        (rectIndex === rects.length - 1
          ? ' selection-segment-last'
          : '');

      element.style.cssText = [
        `left:${clamp(rect.x, 0, 1) * 100}%`,
        `top:${clamp(rect.y, 0, 1) * 100}%`,
        `width:${clamp(rect.w, 0, 1) * 100}%`,
        `height:${clamp(rect.h, 0, 1) * 100}%`
      ].join(';');

      if (
        annotation.text &&
        annotation.source !== 'text-selection'
      ) {
        element.textContent = annotation.text;
      }

      const titleParts = [];

      if (annotation.comment) {
        titleParts.push(annotation.comment);
      }

      if (annotation.selectedText) {
        titleParts.push(`Selected text: ${annotation.selectedText}`);
      }

      element.title = titleParts.join('\n');
      layer.append(element);
    });
  }
}

function wireReviewLayer(layer, pageNumber) {
  let start = null;

  layer.onpointerdown = event => {
    if (!FREE_ANNOTATION_TOOLS.has(state.tool)) return;

    const bounds = layer.getBoundingClientRect();

    start = {
      x: clamp(
        (event.clientX - bounds.left) / bounds.width,
        0,
        1
      ),
      y: clamp(
        (event.clientY - bounds.top) / bounds.height,
        0,
        1
      ),
      id: event.pointerId
    };

    layer.setPointerCapture?.(event.pointerId);
  };

  layer.onpointerup = event => {
    if (!start) return;

    const bounds = layer.getBoundingClientRect();

    const endX = clamp(
      (event.clientX - bounds.left) / bounds.width,
      0,
      1
    );

    const endY = clamp(
      (event.clientY - bounds.top) / bounds.height,
      0,
      1
    );

    const item = {
      id: makeId(),
      page: pageNumber,
      type: state.tool,
      source: 'free',
      x: Math.min(start.x, endX),
      y: Math.min(start.y, endY),
      w: Math.max(0.012, Math.abs(endX - start.x)),
      h: Math.max(0.012, Math.abs(endY - start.y))
    };

    if (state.tool === 'text') {
      const insertedText = prompt('Text:', '');
      if (insertedText === null) {
        start = null;
        return;
      }
      item.text = insertedText;
    }

    state.undo.push({
      kind: 'annotation',
      id: item.id
    });

    state.annotations.push(item);
    start = null;

    markDirty();
    renderPageReview(pageNumber);
    renderSideLists();
  };
}

function selectionApi() {
  return window.InkDeskPdfTextSelection;
}

function captureCurrentTextSelection() {
  const api = selectionApi();

  if (
    !api ||
    typeof api.captureSelection !== 'function'
  ) {
    state.textSelection = null;
    return null;
  }

  state.textSelection = api.captureSelection(
    window.getSelection(),
    document
  );

  return state.textSelection;
}

function clearBrowserSelection() {
  const selection = window.getSelection();

  if (
    selection &&
    typeof selection.removeAllRanges === 'function'
  ) {
    selection.removeAllRanges();
  }

  state.textSelection = null;
}

function renderAnnotationPages(annotations) {
  const pageNumbers = new Set(
    annotations.map(annotation => annotation.page)
  );

  pageNumbers.forEach(pageNumber => {
    renderPageReview(pageNumber);
  });
}

function applyTextSelection(tool, captured) {
  const api = selectionApi();
  const selection =
    captured ||
    state.textSelection ||
    captureCurrentTextSelection();

  if (
    !api ||
    !selection ||
    !selection.pages?.length
  ) {
    status(
      tool === 'comment'
        ? 'Select PDF text, then choose Comment.'
        : `Select PDF text to ${tool} it.`
    );
    return false;
  }

  let comment = '';

  if (tool === 'comment') {
    const entered = prompt(
      `Comment on “${selection.text.slice(0, 120)}”`,
      ''
    );

    if (entered === null) {
      status('Comment cancelled.');
      return false;
    }

    comment = entered.trim() || 'Comment';
  }

  const groupId = makeId();

  const annotations = api.buildAnnotations(
    selection,
    tool,
    {
      groupId,
      comment,
      makeId
    }
  );

  if (!annotations.length) {
    status('The selected PDF text could not be mapped.');
    return false;
  }

  state.annotations.push(...annotations);

  state.undo.push({
    kind: 'annotation-group',
    groupId
  });

  markDirty();
  renderAnnotationPages(annotations);
  renderSideLists();
  clearBrowserSelection();

  const label = {
    highlight: 'Highlight',
    underline: 'Underline',
    comment: 'Comment'
  }[tool];

  toast(
    `${label} applied to selected text. Select another passage to continue.`
  );

  return true;
}

function scheduleSelectionCapture(applyActiveTool) {
  clearTimeout(state.selectionTimer);

  state.selectionTimer = setTimeout(() => {
    const captured = captureCurrentTextSelection();

    if (
      applyActiveTool &&
      captured &&
      TEXT_SELECTION_TOOLS.has(state.tool)
    ) {
      applyTextSelection(state.tool, captured);
    }
  }, 80);
}

function renderSideLists() {
  renderBookmarks();
  E.commentList.replaceChildren();

  const representedGroups = new Set();

  for (
    const annotation of state.annotations.filter(
      item => item.comment || item.text
    )
  ) {
    const identity =
      annotation.groupId || annotation.id;

    if (representedGroups.has(identity)) continue;
    representedGroups.add(identity);

    const button = document.createElement('button');
    button.className = 'comment-item';

    const primary =
      annotation.comment ||
      annotation.text ||
      'Comment';

    const selected =
      annotation.selectedText
        ? ` — “${annotation.selectedText.slice(0, 100)}”`
        : '';

    button.textContent =
      `Page ${annotation.page}: ${primary}${selected}`;

    button.onclick = () =>
      navigateToPage(annotation.page);

    E.commentList.append(button);
  }

  if (!E.commentList.children.length) {
    E.commentList.textContent = 'No comments.';
  }
}

async function openFile(file) {
  if (
    !(file instanceof Blob) ||
    !(
      /\.pdf$/i.test(file.name || '') ||
      file.type === 'application/pdf'
    )
  ) {
    throw new Error('Choose a PDF file.');
  }

  await closeDocument();

  state.file = file;
  state.fingerprint = await fingerprint(file);
  state.storageKey =
    'inkdesk.pdf.review.' + state.fingerprint;
  state.url = URL.createObjectURL(file);

  E.systemOpenBtn.href = state.url;
  E.docTitle.textContent = cleanName(file.name);
  E.startScreen.classList.add('hidden');
  E.viewerApp.classList.remove('hidden');

  status('Loading PDF with local PDF.js…');

  state.task = pdfjsLib.getDocument({
    url: state.url,
    rangeChunkSize: 262144,
    cMapPacked: true,
    enableXfa: true,
    stopAtErrors: false,
    isEvalSupported: false
  });

  state.doc = await state.task.promise;

  E.pageCount.textContent = state.doc.numPages;
  E.pageNumber.max = state.doc.numPages;

  buildPlaceholders();
  renderPageList();
  loadReview();
  renderOutline();

  await navigateToPage(1);

  E.saveModifiedPdfBtn.disabled = false;

  toast(
    `${state.doc.numPages} pages · PDF.js local`
  );
}

async function closeDocument() {
  state.observer?.disconnect();
  clearTimeout(window.__pdfResize);
  window.__pdfResize = null;

  for (const [pageNumber, record] of [...state.rendered]) {
    destroyRendered(pageNumber, record);
  }

  state.thumbs.clear();

  try {
    await state.task?.destroy();
  } catch (error) {
    console.warn(error);
  }

  if (state.url) URL.revokeObjectURL(state.url);

  Object.assign(state, {
    file: null,
    url: '',
    doc: null,
    task: null,
    page: 1,
    annotations: [],
    bookmarks: [],
    undo: [],
    textSelection: null,
    dirty: false,
    renderEpoch: state.renderEpoch + 1
  });

  E.dirtyMark.hidden = true;
  E.saveModifiedPdfBtn.disabled = true;
  E.saveModifiedPdfBtn.classList.remove('is-saving');
  E.saveModifiedPdfBtn.removeAttribute('aria-busy');
}

function setTool(tool) {
  state.tool = tool;

  document
    .querySelectorAll('.annotation-tool')
    .forEach(button => {
      button.classList.toggle(
        'active',
        button.dataset.tool === tool
      );
    });

  const freeTool = FREE_ANNOTATION_TOOLS.has(tool);

  document
    .querySelectorAll('.page-review-layer')
    .forEach(layer => {
      layer.classList.toggle('inactive', !freeTool);
    });

  document.body.dataset.pdfReviewMode =
    TEXT_SELECTION_TOOLS.has(tool)
      ? 'text-selection'
      : freeTool
        ? 'free-annotation'
        : 'select';

  if (TEXT_SELECTION_TOOLS.has(tool)) {
    const captured =
      state.textSelection ||
      captureCurrentTextSelection();

    if (captured) {
      applyTextSelection(tool, captured);
    } else {
      status(
        tool === 'comment'
          ? 'Select PDF text to attach a comment.'
          : `Select PDF text to ${tool} it.`
      );
    }
  } else if (tool === 'marker') {
    status('Drag freely over the page to add a marker area.');
  } else if (tool === 'text') {
    status('Drag over the page to place free text.');
  } else {
    status('Select PDF text or fill supported form fields.');
  }
}

function setZoom(value) {
  if (!state.doc) return;

  state.zoom = /^\d+$/.test(String(value))
    ? clamp(Number(value) / 100, 0.5, 4)
    : value;

  E.zoomSelect.value =
    typeof state.zoom === 'number'
      ? String(Math.round(state.zoom * 100))
      : state.zoom;

  rerender();
}

function zoomStep(delta) {
  const current =
    typeof state.zoom === 'number'
      ? state.zoom
      : 1;

  setZoom(
    Math.round(
      clamp(current + delta, 0.5, 4) * 100
    )
  );
}

function setDirection(direction) {
  state.direction = direction;

  E.viewerStage.classList.toggle(
    'horizontal-mode',
    direction === 'horizontal'
  );

  E.viewerStage.classList.toggle(
    'vertical-mode',
    direction === 'vertical'
  );

  E.pdfPages.classList.toggle(
    'horizontal-pages',
    direction === 'horizontal'
  );

  E.verticalScroll.classList.toggle(
    'active',
    direction === 'vertical'
  );

  E.horizontalScroll.classList.toggle(
    'active',
    direction === 'horizontal'
  );

  navigateToPage(state.page);
}

async function saveModifiedPdf() {
  if (!state.doc || !state.file || E.saveModifiedPdfBtn.disabled) return;

  const exporter = window.InkDeskPdfFlattenExport;
  const hasInkDeskAnnotations = state.annotations.length > 0;

  E.saveModifiedPdfBtn.disabled = true;
  E.saveModifiedPdfBtn.classList.add('is-saving');
  E.saveModifiedPdfBtn.setAttribute('aria-busy', 'true');

  try {
    /*
     * With no InkDesk review marks, PDF.js can preserve supported form state
     * and the original selectable PDF structure.
     */
    if (!hasInkDeskAnnotations) {
      status('Saving PDF…');
      const bytes = await state.doc.saveDocument();

      download(
        bytes,
        cleanName(state.file.name).replace(
          /\.pdf$/i,
          ''
        ) + '-modified.pdf',
        'application/pdf'
      );

      state.dirty = false;
      E.dirtyMark.hidden = true;
      toast('PDF saved');
      return;
    }

    if (
      !exporter ||
      typeof exporter.exportDocument !== 'function'
    ) {
      throw new Error(
        'The local annotated-PDF exporter is unavailable.'
      );
    }

    const result = await exporter.exportDocument({
      pdfDocument: state.doc,
      pdfjsLib,
      documentObject: document,
      annotations: state.annotations,
      fileName: cleanName(state.file.name),
      dpi: 144,
      jpegQuality: 0.91,
      maxPagePixels: 8000000,
      onProgress(progress) {
        const phase =
          progress.phase === 'encode'
            ? 'Encoding'
            : 'Rendering';

        status(
          `${phase} annotated PDF · page ` +
          `${progress.page} of ${progress.total}`
        );
      }
    });

    download(
      result.bytes,
      result.fileName,
      'application/pdf'
    );

    state.dirty = false;
    E.dirtyMark.hidden = true;
    saveReview();

    toast(
      `Annotated PDF saved · ${result.pageCount} pages`
    );
  } catch (error) {
    alert(
      'InkDesk could not create the PDF copy. ' +
      'The original file and the local review were not changed.'
    );
    console.error(error);
    status('PDF save failed.');
  } finally {
    E.saveModifiedPdfBtn.classList.remove('is-saving');
    E.saveModifiedPdfBtn.removeAttribute('aria-busy');
    E.saveModifiedPdfBtn.disabled = !state.doc;
  }
}

function undoLastReviewAction() {
  const action = state.undo.pop();
  if (!action) return;

  if (action.kind === 'annotation-group') {
    state.annotations = state.annotations.filter(
      annotation =>
        annotation.groupId !== action.groupId
    );
  } else if (action.kind === 'annotation') {
    state.annotations = state.annotations.filter(
      annotation => annotation.id !== action.id
    );
  }

  markDirty();
  rerender();
  renderSideLists();
}

E.openBtn.onclick =
  E.openSmall.onclick =
    () => E.fileInput.click();

E.fileInput.onchange = () => {
  const file = E.fileInput.files[0];

  if (file) {
    openFile(file).catch(error =>
      alert(error.message)
    );
  }
};

E.zoomSelect.onchange = () =>
  setZoom(E.zoomSelect.value);

E.zoomOut.onclick = () => zoomStep(-0.1);
E.zoomIn.onclick = () => zoomStep(0.1);

E.verticalScroll.onclick = () =>
  setDirection('vertical');

E.horizontalScroll.onclick = () =>
  setDirection('horizontal');

document
  .querySelectorAll('.annotation-tool')
  .forEach(button => {
    button.addEventListener(
      'pointerdown',
      () => captureCurrentTextSelection(),
      true
    );

    button.onclick = () =>
      setTool(button.dataset.tool);
  });

document.addEventListener(
  'selectionchange',
  () => scheduleSelectionCapture(false)
);

E.pdfPages.addEventListener(
  'pointerdown',
  event => {
    if (event.target.closest('.textLayer')) {
      state.textSelection = null;
    }
  }
);

E.pdfPages.addEventListener(
  'pointerup',
  event => {
    if (event.target.closest('.textLayer')) {
      scheduleSelectionCapture(true);
    }
  }
);

E.pdfPages.addEventListener(
  'touchend',
  event => {
    if (event.target.closest('.textLayer')) {
      scheduleSelectionCapture(true);
    }
  },
  { passive: true }
);

/*
 * The shared 0.19.4.5 shell owns the PDF sidebar toggle in the
 * capture phase. Do not install another legacy toggle here.
 */

E.bookmarkBtn.onclick = () => {
  const index = state.bookmarks.indexOf(state.page);

  if (index >= 0) {
    state.bookmarks.splice(index, 1);
  } else {
    state.bookmarks.push(state.page);
  }

  markDirty();
  renderSideLists();
};

E.saveModifiedPdfBtn.onclick = saveModifiedPdf;
E.undoReview.onclick = undoLastReviewAction;

function exitImmersive() {
  document.body.classList.remove('immersive');

  if (document.fullscreenElement) {
    document.exitFullscreen().catch(() => {});
  }
}

E.fullscreenBtn.onclick = async () => {
  if (
    document.fullscreenElement ||
    document.body.classList.contains('immersive')
  ) {
    exitImmersive();
    return;
  }

  try {
    await E.viewerApp.requestFullscreen();
  } catch (error) {
    document.body.classList.add('immersive');
  }
};

E.immersiveExit.onclick = exitImmersive;

document.addEventListener(
  'fullscreenchange',
  () => {
    if (!document.fullscreenElement) {
      document.body.classList.remove('immersive');
    }
  }
);

window.addEventListener('resize', () => {
  clearTimeout(window.__pdfResize);
  window.__pdfResize = setTimeout(
    rerender,
    180
  );
});

window.addEventListener(
  'pagehide',
  closeDocument,
  { once: true }
);

window.InkDeskWorkspaceOpenFile = openFile;

if (window.InkDeskFileRouter) {
  InkDeskFileRouter.attachWorkspace({
    extensions: ['pdf'],
    openFile
  });
}

window.InkDeskPdfDebug = {
  getState: () => ({
    page: state.page,
    pageCount: state.doc?.numPages || 0,
    zoom:
      typeof state.zoom === 'number'
        ? String(Math.round(state.zoom * 100))
        : state.zoom,
    renderedCanvases: state.rendered.size,
    pagePlaceholders: state.pages.size,
    annotations: state.annotations.length,
    selectedTextAnnotations:
      state.annotations.filter(
        item => item.source === 'text-selection'
      ).length,
    bookmarks: state.bookmarks.length,
    pdfjsVersion: pdfjsLib.version,
    direction: state.direction,
    tool: state.tool
  }),
  goToPage: pageNumber =>
    navigateToPage(pageNumber),
  setZoom,
  applyCapturedSelection: tool =>
    applyTextSelection(
      tool,
      captureCurrentTextSelection()
    ),
  addSyntheticAnnotation: (
    type = 'highlight'
  ) => {
    const annotation = {
      id: makeId(),
      page: state.page,
      type,
      source: 'free',
      x: 0.1,
      y: 0.1,
      w: 0.2,
      h: 0.04
    };

    state.annotations.push(annotation);
    renderPageReview(state.page);
  },
  toggleFullscreen: () =>
    E.fullscreenBtn.click(),
  exitFullscreen: exitImmersive
};

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

const reviewController =
  window.InkDeskPdfReviewController.createReviewController({
    state,
    elements: E,
    clamp,
    makeId,
    status,
    toast,
    renderBookmarks: () => renderBookmarks(),
    navigateToPage: pageNumber =>
      navigateToPage(pageNumber),
    rerender: () => pageRenderer?.rerender()
  });

const {
  saveReview,
  loadReview,
  markDirty,
  renderPageReview,
  wireReviewLayer,
  renderSideLists
} = reviewController;

pageRenderer = window.InkDeskPdfPageRenderer.createPageRenderer({
  state,
  elements: E,
  pdfjs: pdfjsLib,
  clamp,
  isFreeAnnotationTool: tool =>
    reviewController.isFreeAnnotationTool(tool),
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
    reviewController.applyTextSelection(
      tool,
      reviewController.captureCurrentTextSelection()
    ),
  addSyntheticAnnotation: type =>
    reviewController.addSyntheticAnnotation(type),
  toggleFullscreen: () =>
    E.fullscreenBtn.click(),
  exitFullscreen: exitImmersive
};

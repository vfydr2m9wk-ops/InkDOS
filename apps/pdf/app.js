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
    'zoomSelect', 'pdfZoomSlider', 'pdfFitWidth', 'pdfZoomLabel',
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
  window.InkDOSPdfNavigationController.createNavigationController({
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
  window.InkDOSPdfReviewController.createReviewController({
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

const saveController =
  window.InkDOSPdfSaveController.createSaveController({
    state,
    elements: E,
    pdfjs: pdfjsLib,
    cleanName,
    status,
    toast,
    saveReview
  });

pageRenderer = window.InkDOSPdfPageRenderer.createPageRenderer({
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
    'inkdos.pdf.review.' + state.fingerprint;
  const previousReviewKey = 'ink' + 'desk.pdf.review.' + state.fingerprint;
  try {
    if (localStorage.getItem(state.storageKey) == null) {
      const previousReview = localStorage.getItem(previousReviewKey);
      if (previousReview != null) {
        const migratedReview = JSON.parse(previousReview);
        if (migratedReview && migratedReview.schema === ('ink' + 'desk-pdf-review/2')) {
          migratedReview.schema = 'inkdos-pdf-review/2';
        }
        localStorage.setItem(state.storageKey, JSON.stringify(migratedReview));
        localStorage.removeItem(previousReviewKey);
      }
    }
  } catch (error) {
    console.warn('InkDOS could not migrate previous PDF review data.', error);
  }
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
  syncZoomUi();

  saveController.setAvailable(true);

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
  saveController.setAvailable(false);
}
function syncZoomUi() {
  const current = typeof state.zoom === 'number' ? state.zoom : state.scale || 1;
  const percent = Math.round(current * 100);
  if (E.pdfZoomSlider) E.pdfZoomSlider.value = String(clamp(percent, 50, 200));
  if (E.pdfZoomLabel) E.pdfZoomLabel.textContent = percent + '%';
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

  syncZoomUi();
  rerender();
}
async function fitWidth(gutter = 48, minimumScale = 0.5) {
  if (!state.doc) return;
  const page = await state.doc.getPage(state.page), base = page.getViewport({ scale: 1 });
  const available = Math.max(80, E.viewerStage.clientWidth - gutter);
  const fitted = clamp(available / base.width, minimumScale, 4);
  state.zoom = fitted;
  E.zoomSelect.value = fitted >= 0.5 ? String(Math.round(fitted * 100)) : 'page-width';
  syncZoomUi();
  rerender();
  page.cleanup();
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
E.pdfZoomSlider.oninput = () => setZoom(E.pdfZoomSlider.value);
E.pdfFitWidth.onclick = () => fitWidth().catch(console.error);

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


const fullscreenController = window.InkDOSPdfFullscreen.create({
  state, elements:E, fitWidth, rerender
});
E.fullscreenBtn.onclick = () => fullscreenController.toggle();
E.immersiveExit.onclick = () => fullscreenController.exit();

window.addEventListener(
  'pagehide',
  closeDocument,
  { once: true }
);

window.InkDOSWorkspaceOpenFile = openFile;

if (window.InkDOSFileRouter) {
  InkDOSFileRouter.attachWorkspace({
    appId: 'pdf',
    openFile
  });
}

window.InkDOSPdfDebug = {
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
  exitFullscreen: () => fullscreenController.exit()
};

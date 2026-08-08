(function (global) {
  'use strict';

  const TEXT_SELECTION_TOOLS = new Set([
    'highlight',
    'underline',
    'comment'
  ]);

  const FREE_ANNOTATION_TOOLS = new Set([
    'marker',
    'text'
  ]);

  function createReviewController({
    state,
    elements,
    clamp,
    makeId,
    status,
    toast,
    renderBookmarks,
    navigateToPage,
    rerender
  }) {
    if (
      !state || !elements || !clamp || !makeId ||
      !status || !toast || !renderBookmarks ||
      !navigateToPage || !rerender
    ) {
      throw new Error(
        'InkDesk PDF review controller requires state, elements and review callbacks.'
      );
    }

    const E = elements;

    function saveReview() {
      if (!state.storageKey) return;

      localStorage.setItem(
        state.storageKey,
        JSON.stringify({
          schema: 'inkdesk-pdf-review/2',
          fingerprint: state.fingerprint,
          annotations: state.annotations,
          bookmarks: state.bookmarks
        })
      );
    }

    function renderComments() {
      E.commentList.replaceChildren();
      const representedGroups = new Set();

      for (
        const annotation of state.annotations.filter(
          item => item.comment || item.text
        )
      ) {
        const identity = annotation.groupId || annotation.id;
        if (representedGroups.has(identity)) continue;
        representedGroups.add(identity);

        const button = document.createElement('button');
        button.className = 'comment-item';
        const primary = annotation.comment || annotation.text || 'Comment';
        const selected = annotation.selectedText
          ? ` — “${annotation.selectedText.slice(0, 100)}”`
          : '';

        button.textContent =
          `Page ${annotation.page}: ${primary}${selected}`;
        button.onclick = () => navigateToPage(annotation.page);
        E.commentList.append(button);
      }

      if (!E.commentList.children.length) {
        E.commentList.textContent = 'No comments.';
      }
    }

    function renderSideLists() {
      renderBookmarks();
      renderComments();
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
        console.warn(
          'InkDesk could not load the local PDF review.',
          error
        );
      }

      renderSideLists();
    }

    function markDirty() {
      state.dirty = true;
      E.dirtyMark.hidden = false;
      saveReview();
    }

    let annotationLayer = null;

    const isFreeAnnotationTool = tool =>
      FREE_ANNOTATION_TOOLS.has(tool);

    function ensureAnnotationLayer() {
      if (annotationLayer) return annotationLayer;

      annotationLayer =
        global.InkDeskPdfAnnotationLayer.createAnnotationLayer({
          state,
          clamp,
          makeId,
          isFreeAnnotationTool,
          markDirty,
          renderSideLists
        });

      return annotationLayer;
    }

    function renderPageReview(pageNumber) {
      ensureAnnotationLayer().renderPageReview(pageNumber);
    }

    function wireReviewLayer(layer, pageNumber) {
      ensureAnnotationLayer().wireReviewLayer(layer, pageNumber);
    }

    function selectionApi() {
      return global.InkDeskPdfTextSelection;
    }

    function captureCurrentTextSelection() {
      const api = selectionApi();
      if (!api || typeof api.captureSelection !== 'function') {
        state.textSelection = null;
        return null;
      }

      state.textSelection = api.captureSelection(
        global.getSelection(),
        document
      );
      return state.textSelection;
    }

    function clearBrowserSelection() {
      const selection = global.getSelection();
      if (selection?.removeAllRanges) {
        selection.removeAllRanges();
      }
      state.textSelection = null;
    }

    function renderAnnotationPages(annotations) {
      const pageNumbers = new Set(
        annotations.map(annotation => annotation.page)
      );
      pageNumbers.forEach(renderPageReview);
    }

    function applyTextSelection(tool, captured) {
      const api = selectionApi();
      const selection =
        captured ||
        state.textSelection ||
        captureCurrentTextSelection();

      if (!api || !selection || !selection.pages?.length) {
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
        { groupId, comment, makeId }
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

      const freeTool = isFreeAnnotationTool(tool);
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

    function undoLastReviewAction() {
      const action = state.undo.pop();
      if (!action) return;

      if (action.kind === 'annotation-group') {
        state.annotations = state.annotations.filter(
          annotation => annotation.groupId !== action.groupId
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

    function addSyntheticAnnotation(type = 'highlight') {
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
    }

    function reset() {
      clearTimeout(state.selectionTimer);
      state.selectionTimer = 0;
      state.annotations = [];
      state.undo = [];
      state.textSelection = null;
    }

    function wireControls() {
      document
        .querySelectorAll('.annotation-tool')
        .forEach(button => {
          button.addEventListener(
            'pointerdown',
            captureCurrentTextSelection,
            true
          );
          button.onclick = () => setTool(button.dataset.tool);
        });

      document.addEventListener(
        'selectionchange',
        () => scheduleSelectionCapture(false)
      );

      E.pdfPages.addEventListener('pointerdown', event => {
        if (event.target.closest('.textLayer')) {
          state.textSelection = null;
        }
      });

      E.pdfPages.addEventListener('pointerup', event => {
        if (event.target.closest('.textLayer')) {
          scheduleSelectionCapture(true);
        }
      });

      E.pdfPages.addEventListener(
        'touchend',
        event => {
          if (event.target.closest('.textLayer')) {
            scheduleSelectionCapture(true);
          }
        },
        { passive: true }
      );

      E.undoReview.onclick = undoLastReviewAction;
    }

    wireControls();

    return Object.freeze({
      saveReview,
      loadReview,
      markDirty,
      renderPageReview,
      wireReviewLayer,
      renderComments,
      renderSideLists,
      setTool,
      captureCurrentTextSelection,
      applyTextSelection,
      undoLastReviewAction,
      addSyntheticAnnotation,
      reset,
      isFreeAnnotationTool,
      isTextSelectionTool: tool =>
        TEXT_SELECTION_TOOLS.has(tool)
    });
  }

  global.InkDeskPdfReviewController = Object.freeze({
    version: '0.20.2.25',
    createReviewController
  });
})(globalThis);

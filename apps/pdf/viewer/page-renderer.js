(function (global) {
  'use strict';

  const CACHE_RADIUS = 2;
  const MAX_CANVAS_PIXELS = 16777216;

  function createPageRenderer({
    state,
    elements,
    pdfjs,
    clamp,
    isFreeAnnotationTool,
    renderPageReview,
    wireReviewLayer,
    goToDestination,
    syncNavigation
  }) {
    if (!state || !elements || !pdfjs) {
      throw new Error('InkDesk PDF page renderer requires state, elements and PDF.js.');
    }

    const E = elements;

    function pageScale(base) {
      if (typeof state.zoom === 'number') return state.zoom;

      const availableWidth = Math.max(
        260,
        E.viewerStage.clientWidth -
          (state.direction === 'vertical' ? 48 : 24)
      );

      const availableHeight = Math.max(
        260,
        E.viewerStage.clientHeight - 36
      );

      return state.zoom === 'page-fit'
        ? Math.min(
            availableWidth / base.width,
            availableHeight / base.height
          )
        : availableWidth / base.width;
    }

    function placeholder(pageNumber) {
      const shell = document.createElement('section');
      shell.className = 'pdf-page-shell';
      shell.dataset.page = pageNumber;
      shell.setAttribute('aria-label', `Page ${pageNumber}`);
      shell.style.setProperty('--ratio', '1.294');

      const inner = document.createElement('div');
      inner.className = 'pdf-page';

      const loading = document.createElement('div');
      loading.className = 'page-loading';
      loading.textContent = `Page ${pageNumber}`;

      inner.append(loading);
      shell.append(inner);
      return shell;
    }

    function buildPlaceholders() {
      E.pdfPages.replaceChildren();
      state.pages.clear();

      for (
        let pageNumber = 1;
        pageNumber <= state.doc.numPages;
        pageNumber += 1
      ) {
        const shell = placeholder(pageNumber);
        state.pages.set(pageNumber, shell);
        E.pdfPages.append(shell);
      }

      observePages();
    }

    function observePages() {
      state.observer?.disconnect();

      state.observer = new IntersectionObserver(
        entries => {
          if (performance.now() < state.navLockUntil) return;

          let best = null;

          for (const entry of entries) {
            if (!entry.isIntersecting) continue;

            const pageNumber = Number(entry.target.dataset.page);
            ensureWindow(pageNumber);

            if (
              !best ||
              entry.intersectionRatio > best.intersectionRatio
            ) {
              best = entry;
            }
          }

          if (!best) return;

          const pageNumber = Number(best.target.dataset.page);

          if (pageNumber !== state.page) {
            state.page = pageNumber;
            syncNavigation();
          }
        },
        {
          root: E.viewerStage,
          rootMargin: '120% 120%',
          threshold: [0, 0.05, 0.25, 0.5, 0.75]
        }
      );

      state.pages.forEach(shell => state.observer.observe(shell));
    }

    function viewportRelevant(pageNumber) {
      const shell = state.pages.get(pageNumber);
      if (!shell || !E.viewerStage) return false;
      const pageRect = shell.getBoundingClientRect();
      const stageRect = E.viewerStage.getBoundingClientRect();
      const margin = Math.max(stageRect.height, 300);
      return (
        pageRect.bottom >= stageRect.top - margin &&
        pageRect.top <= stageRect.bottom + margin
      );
    }

    async function ensureWindow(center) {
      const wanted = new Set();

      for (
        let pageNumber = Math.max(1, center - CACHE_RADIUS);
        pageNumber <= Math.min(
          state.doc.numPages,
          center + CACHE_RADIUS
        );
        pageNumber += 1
      ) {
        wanted.add(pageNumber);
      }

      state.wanted = wanted;

      // Keep the previous visible window alive until the incoming window has
      // rendered. This prevents gray placeholders during fast WebKit scrolls
      // while preserving the bounded CACHE_RADIUS memory policy.
      await Promise.all(
        [...wanted].map(pageNumber => renderPage(pageNumber))
      );

      for (const [pageNumber, record] of [...state.rendered]) {
        if (
          !state.wanted.has(pageNumber) &&
          !viewportRelevant(pageNumber)
        ) {
          destroyRendered(pageNumber, record);
        }
      }
    }

    function destroyRendered(pageNumber, record) {
      record.task?.cancel?.();
      record.page?.cleanup?.();
      record.canvas.width = 0;
      record.canvas.height = 0;

      const shell = state.pages.get(pageNumber);

      if (shell) {
        const inner = shell.querySelector('.pdf-page');
        const loading = document.createElement('div');
        loading.className = 'page-loading';
        loading.textContent = `Page ${pageNumber}`;
        inner.replaceChildren(loading);
      }

      state.rendered.delete(pageNumber);
    }

    async function renderPage(pageNumber) {
      if (state.rendered.has(pageNumber)) return;

      const epoch = state.renderEpoch;
      const shell = state.pages.get(pageNumber);
      if (!shell) return;

      const page = await state.doc.getPage(pageNumber);

      if (
        epoch !== state.renderEpoch ||
        (!state.wanted.has(pageNumber) &&
          !viewportRelevant(pageNumber))
      ) {
        page.cleanup();
        return;
      }

      const base = page.getViewport({ scale: 1 });
      const scale = clamp(pageScale(base), state.fullscreenFit ? 0.10 : 0.5, 4);
      state.scale = scale;

      const viewport = page.getViewport({ scale });

      shell.style.width = `${viewport.width}px`;
      shell.style.height = `${viewport.height}px`;

      const holder = shell.querySelector('.pdf-page');
      holder.replaceChildren();
      holder.style.width = `${viewport.width}px`;
      holder.style.height = `${viewport.height}px`;
      holder.style.setProperty(
        '--scale-factor',
        String(viewport.scale)
      );

      const canvas = document.createElement('canvas');
      canvas.className = 'canvas-layer';

      const outputScale = Math.min(
        devicePixelRatio || 1,
        Math.sqrt(
          MAX_CANVAS_PIXELS /
            (viewport.width * viewport.height)
        )
      );

      canvas.width = Math.floor(viewport.width * outputScale);
      canvas.height = Math.floor(viewport.height * outputScale);
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      holder.append(canvas);

      const task = page.render({
        canvasContext: canvas.getContext('2d'),
        viewport,
        transform:
          outputScale === 1
            ? null
            : [outputScale, 0, 0, outputScale, 0, 0],
        annotationMode:
          pdfjs.AnnotationMode.ENABLE_STORAGE,
        annotationStorage: state.doc.annotationStorage
      });

      state.rendered.set(pageNumber, {
        page,
        canvas,
        task
      });

      await task.promise.catch(error => {
        if (error?.name !== 'RenderingCancelledException') {
          throw error;
        }
      });

      if (
        epoch !== state.renderEpoch ||
        (!state.wanted.has(pageNumber) &&
          !viewportRelevant(pageNumber)) ||
        state.rendered.get(pageNumber)?.task !== task
      ) {
        const record = state.rendered.get(pageNumber);
        if (record?.task === task) destroyRendered(pageNumber, record);
        return;
      }

      const textLayer = document.createElement('div');
      textLayer.className = 'textLayer';
      holder.append(textLayer);

      const textContent = await page.getTextContent();
      const textTask = pdfjs.renderTextLayer({
        textContentSource: textContent,
        container: textLayer,
        viewport,
        textDivs: []
      });

      await textTask.promise;

      const annotations = await page.getAnnotations({
        intent: 'display'
      });

      if (annotations.length) {
        const layer = document.createElement('div');
        layer.className = 'annotationLayer pdfjs-annotations';
        holder.append(layer);

        const annotationLayer = new pdfjs.AnnotationLayer({
          div: layer,
          page,
          viewport: viewport.clone({ dontFlip: true }),
          accessibilityManager: null,
          annotationCanvasMap: null
        });

        await annotationLayer.render({
          annotations,
          annotationStorage: state.doc.annotationStorage,
          renderForms: true,
          linkService: {
            getDestinationHash: () => '',
            getAnchorUrl: () => '',
            addLinkAttributes: (anchor, url) => {
              anchor.href = url || '#';
            },
            goToDestination: destination =>
              goToDestination(destination)
          },
          downloadManager: null,
          imageResourcesPath: '',
          enableScripting: false,
          hasJSActions: false,
          fieldObjects: null
        });
      }

      const review = document.createElement('div');
      review.className =
        'page-review-layer' +
        (isFreeAnnotationTool(state.tool)
          ? ''
          : ' inactive');

      review.dataset.page = pageNumber;
      holder.append(review);

      wireReviewLayer(review, pageNumber);
      renderPageReview(pageNumber);
    }

    function rerender() {
      if (!state.doc) return;

      state.renderEpoch += 1;

      for (const [pageNumber, record] of [...state.rendered]) {
        destroyRendered(pageNumber, record);
      }

      ensureWindow(state.page);
    }

    return Object.freeze({
      buildPlaceholders,
      ensureWindow,
      destroyRendered,
      rerender
    });
  }

  global.InkDeskPdfPageRenderer = Object.freeze({
    version: '0.20.3.0',
    createPageRenderer
  });
})(globalThis);

(function (global) {
  'use strict';

  const THUMB_RADIUS = 12;

  function createNavigationController({
    state,
    elements,
    clamp,
    ensureWindow
  }) {
    if (!state || !elements || !clamp || !ensureWindow) {
      throw new Error(
        'InkDesk PDF navigation controller requires state, elements, clamp and ensureWindow.'
      );
    }

    const E = elements;

    function renderThumbnailWindow() {
      if (!state.doc) return;

      const wanted = new Set();

      for (
        let pageNumber = Math.max(1, state.page - THUMB_RADIUS);
        pageNumber <= Math.min(
          state.doc.numPages,
          state.page + THUMB_RADIUS
        );
        pageNumber += 1
      ) {
        wanted.add(pageNumber);
      }

      for (const pageNumber of [...state.thumbs.keys()]) {
        if (wanted.has(pageNumber)) continue;

        const canvas = document.querySelector(
          `.page-item[data-page="${pageNumber}"] canvas.page-thumb`
        );

        if (canvas) {
          const placeholder = document.createElement('span');
          placeholder.className = 'page-thumb thumb-placeholder';
          placeholder.textContent = String(pageNumber);
          canvas.width = 0;
          canvas.height = 0;
          canvas.replaceWith(placeholder);
        }

        state.thumbs.delete(pageNumber);
      }

      for (const pageNumber of wanted) {
        if (state.thumbs.has(pageNumber)) continue;

        const item = document.querySelector(
          `.page-item[data-page="${pageNumber}"]`
        );

        const old = item?.querySelector('.page-thumb');
        if (!item) continue;

        const canvas = document.createElement('canvas');
        canvas.className = 'page-thumb';
        old?.replaceWith(canvas);
        state.thumbs.set(pageNumber, true);

        state.doc
          .getPage(pageNumber)
          .then(page => {
            if (!state.thumbs.has(pageNumber)) {
              page.cleanup();
              return;
            }

            const base = page.getViewport({ scale: 1 });
            const viewport = page.getViewport({
              scale: Math.min(
                84 / base.width,
                108 / base.height
              )
            });

            canvas.width = Math.ceil(viewport.width);
            canvas.height = Math.ceil(viewport.height);

            return page
              .render({
                canvasContext: canvas.getContext('2d'),
                viewport
              })
              .promise.then(() => page.cleanup());
          })
          .catch(() => state.thumbs.delete(pageNumber));
      }
    }

    function syncNavigation() {
      E.pageNumber.value = state.page;

      document
        .querySelectorAll('.page-item.active')
        .forEach(item => item.classList.remove('active'));

      document
        .querySelector(
          `.page-item[data-page="${state.page}"]`
        )
        ?.classList.add('active');

      renderThumbnailWindow();
    }

    async function navigateToPage(
      pageNumber,
      { smooth = false } = {}
    ) {
      if (!state.doc) return;

      const nextPage = clamp(
        Number(pageNumber) || 1,
        1,
        state.doc.numPages
      );

      state.navLockUntil =
        performance.now() + (smooth ? 900 : 450);

      state.page = nextPage;
      await ensureWindow(nextPage);

      state.pages.get(nextPage)?.scrollIntoView({
        behavior: smooth ? 'smooth' : 'auto',
        block: 'start',
        inline: 'start'
      });

      syncNavigation();
    }

    async function goToDestination(destination) {
      try {
        const target =
          typeof destination === 'string'
            ? await state.doc.getDestination(destination)
            : destination;

        if (!target) return;

        const reference = target[0];
        const index =
          typeof reference === 'object'
            ? await state.doc.getPageIndex(reference)
            : Number(reference);

        navigateToPage(index + 1);
      } catch (error) {
        console.warn(error);
      }
    }

    function renderPageList() {
      E.pageList.replaceChildren();

      const fragment = document.createDocumentFragment();

      for (
        let pageNumber = 1;
        pageNumber <= state.doc.numPages;
        pageNumber += 1
      ) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'page-item';
        button.dataset.page = pageNumber;
        button.innerHTML = [
          `<span class="page-thumb thumb-placeholder">${pageNumber}</span>`,
          '<span class="page-item-meta">',
          `<strong>Page ${pageNumber}</strong>`,
          '</span>'
        ].join('');

        button.onclick = () => navigateToPage(pageNumber);
        fragment.append(button);
      }

      E.pageList.append(fragment);
      syncNavigation();
    }

    async function renderOutline() {
      E.outlineList.replaceChildren();

      const outline = await state.doc.getOutline();

      if (!outline?.length) {
        E.outlineList.textContent = 'No document index.';
        return;
      }

      const add = (items, level = 0) => {
        items.forEach(item => {
          const button = document.createElement('button');
          button.className = 'outline-item';
          button.style.paddingLeft = `${8 + level * 14}px`;
          button.textContent = item.title || 'Untitled';
          button.onclick = () => goToDestination(item.dest);
          E.outlineList.append(button);

          if (item.items?.length) {
            add(item.items, level + 1);
          }
        });
      };

      add(outline);
    }

    function renderBookmarks() {
      E.bookmarkList.replaceChildren();

      for (
        const pageNumber of state.bookmarks.sort(
          (left, right) => left - right
        )
      ) {
        const button = document.createElement('button');
        button.className = 'bookmark-item';
        button.textContent = `Page ${pageNumber}`;
        button.onclick = () => navigateToPage(pageNumber);
        E.bookmarkList.append(button);
      }

      if (!state.bookmarks.length) {
        E.bookmarkList.textContent = 'No bookmarks.';
      }
    }

    function wirePageControls() {
      E.prevPage.onclick = () =>
        navigateToPage(state.page - 1);

      E.nextPage.onclick = () =>
        navigateToPage(state.page + 1);

      E.pageNumber.onchange = () =>
        navigateToPage(E.pageNumber.value);
    }

    function wireSidebarTabs() {
      document
        .querySelectorAll('.sidebar-tab')
        .forEach(tab => {
          tab.onclick = () => {
            document
              .querySelectorAll('.sidebar-tab')
              .forEach(item => {
                item.classList.toggle(
                  'active',
                  item === tab
                );
              });

            document
              .querySelectorAll('.side-panel')
              .forEach(panel => {
                panel.classList.toggle(
                  'active',
                  panel.dataset.panel === tab.dataset.tab
                );
              });
          };
        });
    }

    wirePageControls();
    wireSidebarTabs();

    return Object.freeze({
      syncNavigation,
      navigateToPage,
      goToDestination,
      renderPageList,
      renderThumbnailWindow,
      renderOutline,
      renderBookmarks
    });
  }

  global.InkDeskPdfNavigationController = Object.freeze({
    version: '0.20.2.17',
    createNavigationController
  });
})(globalThis);

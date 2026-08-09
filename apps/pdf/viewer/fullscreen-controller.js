(function (global) {
  'use strict';

  // Universal InkDesk content-focus mode. Full screen hides editor chrome and
  // adapts the current PDF page to the available viewport width. Browser native
  // fullscreen is intentionally not required, avoiding WebKit canvas teardown.
  function create({ state, elements, fitWidth, rerender }) {
    const body = document.body;
    let savedZoom = null;
    let transitionToken = 0;

    function active() {
      return body.classList.contains('pdf-fullscreen') ||
        body.classList.contains('content-focus-mode') ||
        body.classList.contains('immersive');
    }

    function sync(enabled) {
      body.classList.toggle('immersive', enabled);
      body.classList.toggle('pdf-fullscreen', enabled);
      body.classList.toggle('content-focus-mode', enabled);
      elements.fullscreenBtn?.setAttribute('aria-pressed', enabled ? 'true' : 'false');
      elements.fullscreenBtn?.setAttribute('title', enabled ? 'Exit full screen' : 'Full screen');
    }

    function afterLayout(callback) {
      const token = ++transitionToken;
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (token === transitionToken) callback();
      }));
    }

    function enter() {
      if (active()) return;
      savedZoom = state?.zoom ?? null;
      if (state) state.fullscreenFit = true;
      sync(true);
      afterLayout(() => {
        if (!active() || !state?.doc) return;
        Promise.resolve(fitWidth?.(12, 0.10)).catch(console.error);
      });
    }

    function exit() {
      if (!active()) return;
      ++transitionToken;
      sync(false);
      if (state) state.fullscreenFit = false;
      const restore = savedZoom;
      savedZoom = null;
      if (restore !== null && state?.doc) {
        afterLayout(() => {
          if (active() || !state?.doc) return;
          state.zoom = restore;
          rerender?.();
        });
      }
    }

    function toggle() {
      active() ? exit() : enter();
    }

    return { toggle, enter, exit, sync };
  }

  global.InkDeskPdfFullscreen = Object.freeze({ create });
})(window);

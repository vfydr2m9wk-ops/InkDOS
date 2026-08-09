(function (global) {
  'use strict';

  function create({ state, elements, fitWidth, rerender }) {
    const E = elements;
    let resizeTimer = 0;

    function mobilePortrait() {
      return global.innerWidth <= 650 &&
        global.matchMedia('(orientation: portrait)').matches;
    }

    function active() {
      return Boolean(document.fullscreenElement) ||
        document.body.classList.contains('immersive');
    }

    function afterLayout() {
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (active() && mobilePortrait() && state.doc) {
          fitWidth(12).catch(console.error);
        } else {
          rerender();
        }
      }));
    }

    function sync() {
      document.body.classList.toggle('pdf-fullscreen', active());
      afterLayout();
    }

    function exit() {
      document.body.classList.remove('immersive');
      document.body.classList.remove('pdf-fullscreen');
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      } else {
        afterLayout();
      }
    }

    async function toggle() {
      if (active()) {
        exit();
        return;
      }
      try {
        await E.viewerApp.requestFullscreen();
        sync();
      } catch (error) {
        document.body.classList.add('immersive');
        sync();
      }
    }

    document.addEventListener('fullscreenchange', () => {
      if (!document.fullscreenElement) document.body.classList.remove('immersive');
      sync();
    });

    global.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = global.setTimeout(sync, 180);
    });

    return { toggle, exit, sync };
  }

  global.InkDeskPdfFullscreen = Object.freeze({ create });
})(window);

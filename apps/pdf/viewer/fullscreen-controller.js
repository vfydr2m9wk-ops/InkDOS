(function (global) {
  'use strict';

  // InkDesk "full screen" is intentionally a content-focus mode rather than
  // the browser Fullscreen API. This keeps the already-rendered PDF DOM/canvases
  // in place on WebKit/iOS while hiding InkDesk editing chrome on every device.
  function create({ state, elements, fitWidth, rerender }) {
    const body = document.body;

    function active() {
      return body.classList.contains('immersive') ||
        body.classList.contains('pdf-fullscreen');
    }

    function sync(activeState) {
      const enabled = typeof activeState === 'boolean' ? activeState : active();
      body.classList.toggle('immersive', enabled);
      body.classList.toggle('pdf-fullscreen', enabled);
      body.classList.toggle('content-focus-mode', enabled);
    }

    function exit() {
      sync(false);
    }

    function toggle() {
      sync(!active());
    }

    // If another host/browser mechanism changes native fullscreen externally,
    // never tear down the rendered PDF. Only mirror the content-focus chrome.
    document.addEventListener('fullscreenchange', () => {
      if (!document.fullscreenElement && active()) return;
      if (document.fullscreenElement) sync(true);
    });
    document.addEventListener('webkitfullscreenchange', () => {
      if (document.webkitFullscreenElement) sync(true);
    });

    return { toggle, exit, sync };
  }

  global.InkDeskPdfFullscreen = Object.freeze({ create });
})(window);

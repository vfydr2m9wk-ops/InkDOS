(function (global) {
  'use strict';

  const stage = document.getElementById('viewerStage');
  const fitButton = document.getElementById('pdfFitWidth');

  if (!stage || !fitButton) return;

  let width = 0;
  let timer = 0;
  let fitMode = true;

  function debugApi() {
    return global.InkDOSPdfDebug || null;
  }

  function currentZoom() {
    return debugApi()?.getState?.().zoom || '';
  }

  function applyResponsiveFit() {
    const api = debugApi();
    if (!api?.setZoom) return;
    api.setZoom('page-width');
  }

  fitButton.addEventListener(
    'click',
    event => {
      fitMode = true;
      event.preventDefault();
      event.stopImmediatePropagation();
      applyResponsiveFit();
    },
    true
  );

  const observer =
    typeof ResizeObserver === 'function'
      ? new ResizeObserver(entries => {
          const nextWidth = Math.round(
            entries[0]?.contentRect?.width || stage.clientWidth || 0
          );
          if (nextWidth < 1 || Math.abs(nextWidth - width) < 2) return;
          width = nextWidth;

          const zoom = currentZoom();
          if (zoom !== 'page-width' && zoom !== 'page-fit') {
            fitMode = false;
          }

          if (!fitMode && zoom !== 'page-width' && zoom !== 'page-fit') {
            return;
          }

          clearTimeout(timer);
          timer = setTimeout(() => {
            const api = debugApi();
            if (!api?.setZoom) return;
            const mode = currentZoom();
            api.setZoom(mode === 'page-fit' ? 'page-fit' : 'page-width');
          }, 90);
        })
      : null;

  observer?.observe(stage);

  global.addEventListener(
    'pagehide',
    () => {
      observer?.disconnect();
      clearTimeout(timer);
    },
    { once: true }
  );
})(window);

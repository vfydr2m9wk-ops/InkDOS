(function (global) {
  'use strict';

  const VERSION = '0.20.2.17';

function finiteNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number(fallback || 0);
}

function clampNumber(value, minimum, maximum) {
  return Math.max(
    finiteNumber(minimum, 0),
    Math.min(
      finiteNumber(maximum, 0),
      finiteNumber(value, 0)
    )
  );
}

function rulerTickModel(pageWidthPx, dpi) {
  const width = Math.max(1, finiteNumber(pageWidthPx, 816));
  const pixelsPerInch = Math.max(48, finiteNumber(dpi, 96));
  const eighth = pixelsPerInch / 8;
  const count = Math.floor(width / eighth);
  const ticks = [];

  for (let index = 0; index <= count; index += 1) {
    const position = index * eighth;
    const remainder = index % 8;
    const kind =
      remainder === 0
        ? 'major'
        : remainder === 4
          ? 'half'
          : remainder % 2 === 0
            ? 'quarter'
            : 'minor';

    ticks.push(Object.freeze({
      position,
      ratio: clampNumber(position / width, 0, 1),
      kind,
      label: kind === 'major'
        ? String(Math.round(position / pixelsPerInch))
        : ''
    }));
  }

  if (
    ticks.length &&
    width - ticks[ticks.length - 1].position > eighth * 0.45
  ) {
    ticks.push(Object.freeze({
      position: width,
      ratio: 1,
      kind: 'edge',
      label: ''
    }));
  }

  return Object.freeze(ticks);
}

function rulerMetrics(page, globalObject) {
  if (!page || typeof page.getBoundingClientRect !== 'function') {
    return null;
  }

  const rect = page.getBoundingClientRect();
  const style =
    globalObject &&
    typeof globalObject.getComputedStyle === 'function'
      ? globalObject.getComputedStyle(page)
      : page.__computedStyle || {};

  const unscaledWidth = Math.max(
    1,
    finiteNumber(
      page.offsetWidth,
      finiteNumber(style.width, finiteNumber(rect.width, 816))
    )
  );

  const displayWidth = Math.max(
    1,
    finiteNumber(rect.width, unscaledWidth)
  );

  const zoom = displayWidth / unscaledWidth;

  const paddingLeft = clampNumber(
    parseFloat(style.paddingLeft) || 0,
    0,
    unscaledWidth
  );

  const paddingRight = clampNumber(
    parseFloat(style.paddingRight) || 0,
    0,
    unscaledWidth
  );

  const contentWidth = Math.max(
    1,
    unscaledWidth - paddingLeft - paddingRight
  );

  return Object.freeze({
    page,
    rect: Object.freeze({
      left: finiteNumber(rect.left, 0),
      top: finiteNumber(rect.top, 0),
      right: finiteNumber(rect.right, finiteNumber(rect.left, 0) + displayWidth),
      bottom: finiteNumber(rect.bottom, finiteNumber(rect.top, 0)),
      width: displayWidth,
      height: Math.max(1, finiteNumber(rect.height, 1))
    }),
    pageWidth: unscaledWidth,
    displayWidth,
    zoom,
    paddingLeft,
    paddingRight,
    contentWidth,
    contentStartDisplay: paddingLeft * zoom,
    contentEndDisplay: (unscaledWidth - paddingRight) * zoom
  });
}

function visibleDocumentPage(documentObject, viewport) {
  if (!documentObject || !viewport) return null;

  const selection =
    documentObject.getSelection &&
    documentObject.getSelection();

  if (selection && selection.rangeCount) {
    let node = selection.anchorNode;
    if (node && node.nodeType === 3) node = node.parentElement;
    const selectedPage =
      node &&
      typeof node.closest === 'function' &&
      node.closest('.page');

    if (selectedPage) return selectedPage;
  }

  const pages = Array.from(
    documentObject.querySelectorAll('.pages-host > .page')
  );

  if (!pages.length) return null;

  const viewportRect = viewport.getBoundingClientRect();
  let best = null;
  let bestArea = -1;

  pages.forEach(function (page) {
    const rect = page.getBoundingClientRect();
    const visibleWidth = Math.max(
      0,
      Math.min(rect.right, viewportRect.right) -
        Math.max(rect.left, viewportRect.left)
    );
    const visibleHeight = Math.max(
      0,
      Math.min(rect.bottom, viewportRect.bottom) -
        Math.max(rect.top, viewportRect.top)
    );
    const area = visibleWidth * visibleHeight;

    if (area > bestArea) {
      bestArea = area;
      best = page;
    }
  });

  return best || pages[0];
}

function selectedDocumentBlock(documentObject, pagesHost) {
  if (!documentObject || !pagesHost) return null;

  const selection =
    documentObject.getSelection &&
    documentObject.getSelection();

  if (!selection || !selection.rangeCount) return null;

  let node = selection.anchorNode;
  if (node && node.nodeType === 3) node = node.parentElement;

  if (!node || !pagesHost.contains(node)) return null;

  return (
    typeof node.closest === 'function' &&
    node.closest(
      '.page-content p,' +
      '.page-content h1,' +
      '.page-content h2,' +
      '.page-content h3,' +
      '.page-content li,' +
      '.page-content td'
    )
  );
}

function documentIndentState(block, globalObject) {
  if (!block) {
    return Object.freeze({
      left: 0,
      first: 0,
      right: 0
    });
  }

  const style =
    globalObject &&
    typeof globalObject.getComputedStyle === 'function'
      ? globalObject.getComputedStyle(block)
      : block.__computedStyle || {};

  const left = Math.max(
    0,
    parseFloat(style.marginLeft) || 0
  );

  const textIndent =
    parseFloat(style.textIndent) || 0;

  const right = Math.max(
    0,
    parseFloat(style.marginRight) || 0
  );

  return Object.freeze({
    left,
    first: Math.max(0, left + textIndent),
    right
  });
}

function clampIndentState(state, metrics) {
  const contentWidth = Math.max(
    1,
    finiteNumber(metrics && metrics.contentWidth, 644)
  );

  let left = clampNumber(
    state && state.left,
    0,
    contentWidth
  );

  let first = clampNumber(
    state && state.first,
    0,
    contentWidth
  );

  let right = clampNumber(
    state && state.right,
    0,
    contentWidth
  );

  const occupiedLeft = Math.max(left, first);
  const maximumRight = Math.max(
    0,
    contentWidth - occupiedLeft - 4
  );

  right = Math.min(right, maximumRight);

  const maximumLeft = Math.max(
    0,
    contentWidth - right - 4
  );

  left = Math.min(left, maximumLeft);
  first = Math.min(first, maximumLeft);

  return Object.freeze({ left, first, right });
}

function pointerToDocumentIndent(clientX, metrics) {
  if (!metrics) return 0;

  const localPage = (
    finiteNumber(clientX, metrics.rect.left) -
    metrics.rect.left
  ) / Math.max(metrics.zoom, 0.001);

  return clampNumber(
    localPage - metrics.paddingLeft,
    0,
    metrics.contentWidth
  );
}

function applyDocumentIndent(block, state, pagesHost) {
  if (!block) return false;

  block.style.marginLeft = state.left + 'px';
  block.style.textIndent = (state.first - state.left) + 'px';
  block.style.marginRight = state.right + 'px';

  if (
    pagesHost &&
    typeof pagesHost.dispatchEvent === 'function'
  ) {
    let event = null;

    if (typeof global.Event === 'function') {
      event = new global.Event('input', {
        bubbles: true,
        cancelable: false
      });
    } else if (
      pagesHost.ownerDocument &&
      typeof pagesHost.ownerDocument.createEvent === 'function'
    ) {
      event = pagesHost.ownerDocument.createEvent('Event');
      event.initEvent('input', true, false);
    }

    if (event) pagesHost.dispatchEvent(event);
  }

  return true;
}

  global.InkDeskDocumentRulerModel = Object.freeze({
    version: VERSION,
    finiteNumber,
    clampNumber,
    rulerTickModel,
    rulerMetrics,
    visibleDocumentPage,
    selectedDocumentBlock,
    documentIndentState,
    clampIndentState,
    pointerToDocumentIndent,
    applyDocumentIndent
  });
})(typeof window !== 'undefined' ? window : globalThis);

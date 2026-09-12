(function (g) {
  'use strict';

  const tauri = g.__TAURI__;
  if (!tauri || !tauri.dialog || !tauri.fs) return;

  const dialog = tauri.dialog;
  const fs = tauri.fs;
  const opener = tauri.opener;

  g.InkDOSDesktop = Object.freeze({
    host: 'tauri',
    nativeDialogs: true,
    nativeFilesystem: true,
    deliveryConfirmed: true
  });
  document.documentElement.dataset.inkdosHost = 'tauri';

  function abortError(message) {
    try {
      return new DOMException(message || 'Operation cancelled.', 'AbortError');
    } catch (_) {
      const error = new Error(message || 'Operation cancelled.');
      error.name = 'AbortError';
      return error;
    }
  }

  function basename(path) {
    const parts = String(path || '').split(/[\\/]/);
    return parts[parts.length - 1] || 'Untitled';
  }

  function extensionsFromTypes(types) {
    const extensions = new Set();
    for (const type of Array.isArray(types) ? types : []) {
      const accept = type && type.accept && typeof type.accept === 'object' ? type.accept : {};
      for (const values of Object.values(accept)) {
        for (const value of Array.isArray(values) ? values : []) {
          const extension = String(value || '').trim().replace(/^\./, '');
          if (extension && !extension.includes('/')) extensions.add(extension);
        }
      }
    }
    return Array.from(extensions);
  }

  function extensionsFromAccept(accept) {
    const extensions = new Set();
    for (const value of String(accept || '').split(',')) {
      const token = value.trim();
      if (token.startsWith('.') && token.length > 1) extensions.add(token.slice(1));
    }
    return Array.from(extensions);
  }

  function filters(name, extensions) {
    return extensions.length ? [{ name: name || 'InkDOS file', extensions }] : undefined;
  }

  function mimeForName(name) {
    const lower = String(name || '').toLowerCase();
    if (lower.endsWith('.docx')) return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    if (lower.endsWith('.xlsx')) return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    if (lower.endsWith('.pptx')) return 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
    if (lower.endsWith('.pdf')) return 'application/pdf';
    if (lower.endsWith('.epub')) return 'application/epub+zip';
    if (lower.endsWith('.rtf')) return 'application/rtf';
    if (lower.endsWith('.xml')) return 'application/xml';
    if (lower.endsWith('.txt')) return 'text/plain';
    return 'application/octet-stream';
  }

  async function bytesFromWritableValue(value) {
    if (value instanceof Blob) return new Uint8Array(await value.arrayBuffer());
    if (value instanceof ArrayBuffer) return new Uint8Array(value);
    if (ArrayBuffer.isView(value)) return new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
    if (typeof value === 'string') return new TextEncoder().encode(value);
    if (value && value.type === 'write' && 'data' in value) return bytesFromWritableValue(value.data);
    throw new TypeError('InkDOS desktop save received an unsupported writable value.');
  }

  g.showSaveFilePicker = async function showSaveFilePicker(options) {
    const opts = options || {};
    const extensions = extensionsFromTypes(opts.types);
    const path = await dialog.save({
      title: 'Save InkDOS file',
      defaultPath: opts.suggestedName || undefined,
      filters: filters('InkDOS file', extensions)
    });
    if (!path) throw abortError('Save cancelled.');

    return Object.freeze({
      kind: 'file',
      name: basename(path),
      async createWritable() {
        let pending = new Uint8Array(0);
        let closed = false;
        return {
          async write(value) {
            if (closed) throw new Error('Writable file is already closed.');
            pending = await bytesFromWritableValue(value);
          },
          async close() {
            if (closed) return;
            await fs.writeFile(path, pending);
            closed = true;
          },
          async abort() {
            pending = new Uint8Array(0);
            closed = true;
          }
        };
      }
    });
  };

  const nativeInputClick = g.HTMLInputElement && g.HTMLInputElement.prototype.click;
  if (nativeInputClick) {
    g.HTMLInputElement.prototype.click = function inkdosDesktopInputClick() {
      const input = this;
      if (String(input.type || '').toLowerCase() !== 'file' || input.dataset.inkdosNativePicking === '1') {
        return nativeInputClick.call(input);
      }
      if (typeof g.DataTransfer !== 'function' || typeof g.File !== 'function') {
        return nativeInputClick.call(input);
      }

      input.dataset.inkdosNativePicking = '1';
      const extensions = extensionsFromAccept(input.accept);
      Promise.resolve(dialog.open({
        title: 'Open InkDOS file',
        multiple: !!input.multiple,
        directory: false,
        filters: filters('InkDOS file', extensions)
      })).then(async selected => {
        if (!selected) return;
        const paths = Array.isArray(selected) ? selected : [selected];
        const transfer = new DataTransfer();
        for (const path of paths) {
          const bytes = await fs.readFile(path);
          const name = basename(path);
          transfer.items.add(new File([bytes], name, { type: mimeForName(name), lastModified: Date.now() }));
        }
        input.files = transfer.files;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }).catch(error => {
        console.error('InkDOS desktop file picker failed:', error);
      }).finally(() => {
        delete input.dataset.inkdosNativePicking;
      });
    };
  }

  if (opener && typeof opener.openUrl === 'function') {
    document.addEventListener('click', event => {
      const target = event.target instanceof Element ? event.target.closest('a[href]') : null;
      if (!target) return;
      let url;
      try { url = new URL(target.href, location.href); } catch (_) { return; }
      if ((url.protocol === 'http:' || url.protocol === 'https:') && url.origin !== location.origin) {
        event.preventDefault();
        opener.openUrl(url.href).catch(error => console.error('InkDOS could not open external URL:', error));
      }
    }, true);
  }
})(globalThis);

(function (g) {
  'use strict';

  const tauri = typeof window !== 'undefined' ? window.__TAURI__ : g.__TAURI__;
  if (!tauri || !tauri.dialog || !tauri.fs) return;

  const dialog = tauri.dialog;
  const fs = tauri.fs;
  const opener = tauri.opener;
  const core = tauri.core;

  g.InkDOSDesktop = Object.freeze({
    host: 'tauri',
    nativeDialogs: true,
    nativeFilesystem: true,
    deliveryConfirmed: true,
    manualUpdater: !!(core && typeof core.invoke === 'function')
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

  function extensionForName(name) {
    const match = String(name || '').toLowerCase().match(/\.([^.\\/]+)$/);
    return match ? match[1] : '';
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
      if (token.startsWith('.') && token.length > 1) extensions.add(token.slice(1).toLowerCase());
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

  async function fileFromNativePath(path) {
    const bytes = await fs.readFile(path);
    const name = basename(path);
    return new File([bytes], name, { type: mimeForName(name), lastModified: Date.now() });
  }

  async function fileFromNativeToken(token) {
    if (!core || typeof core.invoke !== 'function') {
      throw new Error('InkDOS desktop cannot resolve this associated file.');
    }
    const payload = await core.invoke('inkdos_read_open_file', { token });
    const name = String(payload && payload.name ? payload.name : 'InkDOS file');
    const raw = payload && payload.bytes;
    const bytes = raw instanceof Uint8Array ? raw : new Uint8Array(Array.isArray(raw) ? raw : []);
    return new File([bytes], name, { type: mimeForName(name), lastModified: Date.now() });
  }

  function compatibleFileInput(file) {
    const extension = extensionForName(file && file.name);
    const inputs = Array.from(document.querySelectorAll('input[type="file"]'));
    for (const input of inputs) {
      const allowed = extensionsFromAccept(input.accept);
      if (!allowed.length || (extension && allowed.includes(extension))) return input;
    }
    return null;
  }

  async function injectNativeFile(file) {
    const input = compatibleFileInput(file);
    if (!input) {
      const extension = extensionForName(file && file.name);
      throw new Error(`Unsupported file format: .${extension || '(none)'}`);
    }
    if (typeof g.DataTransfer !== 'function' || typeof g.File !== 'function') {
      throw new Error('InkDOS desktop cannot inject the associated file in this webview.');
    }

    const allowed = extensionsFromAccept(input.accept);
    const extension = extensionForName(file && file.name);
    if (allowed.length && (!extension || !allowed.includes(extension))) {
      throw new Error(`Unsupported file format: .${extension || '(none)'}`);
    }

    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }

  function autoOpenNativeInjectedFile() {
    const token = g.__INKDOS_OPEN_TOKEN__;
    if (!token) return;
    delete g.__INKDOS_OPEN_TOKEN__;

    let attempts = 0;
    let filePromise = null;
    const tryInject = () => {
      attempts += 1;
      if (!filePromise) filePromise = fileFromNativeToken(token);
      filePromise.then(file => injectNativeFile(file)).then(opened => {
        if (!opened && attempts < 40) g.setTimeout(tryInject, 50);
        else if (!opened) console.error('InkDOS desktop could not find this workspace file input.');
      }).catch(error => {
        console.error('InkDOS desktop associated-file open failed:', error);
        if (dialog && typeof dialog.message === 'function') {
          dialog.message(String(error && error.message ? error.message : error), {
            title: 'InkDOS — Unsupported file',
            kind: 'error'
          }).catch(() => {});
        }
      });
    };
    tryInject();
  }

  function createUpdateModal() {
    let overlay = document.getElementById('inkdosDesktopUpdateModal');
    if (overlay) return overlay;
    overlay = document.createElement('div');
    overlay.id = 'inkdosDesktopUpdateModal';
    overlay.hidden = true;
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'InkDOS update');
    overlay.style.cssText = 'position:fixed;inset:0;z-index:2147483600;display:none;place-items:center;padding:20px;background:rgba(0,0,0,.44)';

    const card = document.createElement('section');
    card.style.cssText = 'width:min(460px,100%);max-height:min(620px,90vh);overflow:auto;border:1px solid rgba(127,127,127,.35);border-radius:14px;padding:18px;background:Canvas;color:CanvasText;box-shadow:0 20px 60px rgba(0,0,0,.32);font:14px/1.45 system-ui,-apple-system,sans-serif';
    const title = document.createElement('h2');
    title.textContent = 'InkDOS update';
    title.style.cssText = 'margin:0 0 10px;font-size:18px';
    const status = document.createElement('p');
    status.dataset.updateStatus = '1';
    status.style.cssText = 'margin:0 0 12px';
    const versions = document.createElement('div');
    versions.dataset.updateVersions = '1';
    versions.style.cssText = 'display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0 0 12px';
    const notes = document.createElement('pre');
    notes.dataset.updateNotes = '1';
    notes.style.cssText = 'display:none;white-space:pre-wrap;overflow-wrap:anywhere;margin:0 0 14px;padding:10px;border-radius:9px;background:rgba(127,127,127,.10);font:13px/1.45 system-ui,-apple-system,sans-serif';
    const actions = document.createElement('div');
    actions.style.cssText = 'display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap';
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.dataset.updateCancel = '1';
    cancel.textContent = 'Cancel';
    const install = document.createElement('button');
    install.type = 'button';
    install.dataset.updateInstall = '1';
    install.textContent = 'Install';
    install.hidden = true;
    for (const button of [cancel, install]) {
      button.style.cssText = 'min-height:36px;padding:6px 12px;border-radius:8px;border:1px solid rgba(127,127,127,.45);background:ButtonFace;color:ButtonText';
    }
    actions.append(cancel, install);
    card.append(title, status, versions, notes, actions);
    overlay.append(card);
    document.body.append(overlay);
    return overlay;
  }

  function showUpdateModal(overlay) {
    overlay.hidden = false;
    overlay.style.display = 'grid';
  }

  function hideUpdateModal(overlay) {
    overlay.hidden = true;
    overlay.style.display = 'none';
  }

  function setVersionRows(container, currentVersion, latestVersion) {
    container.replaceChildren();
    for (const [label, value] of [['Installed', currentVersion], ['Latest', latestVersion]]) {
      const key = document.createElement('strong');
      key.textContent = label;
      const text = document.createElement('span');
      text.textContent = String(value || '—');
      container.append(key, text);
    }
  }

  function installManualUpdaterUI() {
    if (!core || typeof core.invoke !== 'function' || document.getElementById('inkdosUpdateButton')) return;

    const button = document.createElement('button');
    button.id = 'inkdosUpdateButton';
    button.type = 'button';
    button.title = 'Check for updates';
    button.setAttribute('aria-label', 'Check for updates');
    button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" style="width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round"><path d="M20 11a8 8 0 1 0-2.35 5.65"/><path d="M20 4v7h-7"/></svg><span data-update-label>Check for updates</span>';

    const homeActions = document.querySelector('.home-appearance');
    const drawer = ['generalMenu', 'appDrawer', 'moreMenu', 'mainMenu']
      .map(id => document.getElementById(id))
      .find(Boolean);
    const menuList = drawer && drawer.querySelector('.menu-list');
    if (homeActions) {
      button.className = 'theme-button';
      const label = button.querySelector('[data-update-label]');
      if (label) label.style.display = 'none';
      homeActions.insertBefore(button, homeActions.firstChild);
    } else if (drawer && menuList) {
      button.className = 'menu-item';
      menuList.append(button);
    } else {
      button.style.cssText = 'position:fixed;right:12px;top:12px;z-index:2147483500;display:flex;align-items:center;gap:7px;min-height:34px;padding:6px 10px;border-radius:9px;border:1px solid rgba(127,127,127,.4);background:Canvas;color:CanvasText';
      document.body.append(button);
    }

    const overlay = createUpdateModal();
    const status = overlay.querySelector('[data-update-status]');
    const versions = overlay.querySelector('[data-update-versions]');
    const notes = overlay.querySelector('[data-update-notes]');
    const install = overlay.querySelector('[data-update-install]');
    const cancel = overlay.querySelector('[data-update-cancel]');
    let approvedVersion = null;
    let busy = false;

    cancel.addEventListener('click', () => {
      if (busy) return;
      approvedVersion = null;
      hideUpdateModal(overlay);
    });

    button.addEventListener('click', async () => {
      if (busy) return;
      busy = true;
      button.disabled = true;
      approvedVersion = null;
      install.hidden = true;
      install.disabled = false;
      cancel.textContent = 'Cancel';
      cancel.disabled = true;
      status.textContent = 'Checking for updates…';
      versions.replaceChildren();
      notes.textContent = '';
      notes.style.display = 'none';
      showUpdateModal(overlay);
      try {
        const result = await core.invoke('inkdos_check_for_updates');
        setVersionRows(versions, result && result.currentVersion, result && result.latestVersion);
        if (result && result.available) {
          approvedVersion = String(result.latestVersion || '');
          status.textContent = `InkDOS ${approvedVersion} is available.`;
          notes.textContent = String(result.notes || 'No release notes were provided.');
          notes.style.display = 'block';
          install.hidden = false;
          cancel.textContent = 'Cancel';
        } else {
          status.textContent = "You're using the latest version.";
          cancel.textContent = 'Close';
        }
      } catch (error) {
        status.textContent = String(error && error.message ? error.message : error || 'InkDOS could not check for updates.');
        cancel.textContent = 'Close';
      } finally {
        busy = false;
        button.disabled = false;
        cancel.disabled = false;
      }
    });

    install.addEventListener('click', async () => {
      if (busy || !approvedVersion) return;
      busy = true;
      install.disabled = true;
      cancel.disabled = true;
      const version = approvedVersion;
      status.textContent = `Installing InkDOS ${version}…`;
      try {
        await core.invoke('inkdos_install_update', { expectedVersion: version });
        status.textContent = `InkDOS ${version} was installed. Restart InkDOS to use the new version.`;
        install.hidden = true;
        cancel.textContent = 'Close';
        approvedVersion = null;
      } catch (error) {
        status.textContent = String(error && error.message ? error.message : error || 'InkDOS could not install the update.');
        install.disabled = false;
      } finally {
        busy = false;
        cancel.disabled = false;
      }
    });
  }

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
        for (const path of paths) transfer.items.add(await fileFromNativePath(path));
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

  if (document.readyState === 'complete') g.setTimeout(autoOpenNativeInjectedFile, 0);
  else g.addEventListener('load', () => g.setTimeout(autoOpenNativeInjectedFile, 0), { once: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installManualUpdaterUI, { once: true });
  else installManualUpdaterUI();

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

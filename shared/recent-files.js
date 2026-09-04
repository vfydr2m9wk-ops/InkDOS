(function (global) {
  'use strict';

  const STORAGE_KEY = 'inkdos.recent.v2';
  const LEGACY_KEY = 'inkdos.recent.v1';
  const MAX_ITEMS = 30;
  const DB_NAME = 'inkdos-recent-handles';
  const DB_VERSION = 1;
  const STORE_NAME = 'handles';

  function registry() { return global.InkDOSModules || null; }

  function extensionOf(name) {
    const runtime = registry();
    if (runtime && runtime.extensionOf) return runtime.extensionOf(name);
    const match = String(name || '').trim().toLowerCase().match(/\.([a-z0-9]+)$/);
    return match ? match[1] : '';
  }

  function appForExtension(extension) {
    const runtime = registry();
    if (!runtime) return null;
    const app = runtime.resolveExtension(String(extension || '').replace(/^\./, ''));
    return app ? app.id : null;
  }

  function safeParse(value) {
    try {
      const parsed = JSON.parse(value || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) { return []; }
  }

  function storageGet(key) {
    try { return global.localStorage ? global.localStorage.getItem(key) : null; }
    catch (error) { return null; }
  }
  function storageSet(key, value) {
    try {
      if (global.localStorage) global.localStorage.setItem(key, value);
      return true;
    } catch (error) { return false; }
  }
  function storageRemove(key) {
    try { if (global.localStorage) global.localStorage.removeItem(key); }
    catch (error) { console.debug('InkDOS could not remove obsolete recent metadata.', error); }
  }

  function normalize(item) {
    if (!item || typeof item !== 'object' || !item.name) return null;
    const extension = String(item.extension || extensionOf(item.name)).toLowerCase();
    const appId = String(item.appId || appForExtension(extension) || '');
    if (!extension || !appId) return null;
    const size = Math.max(0, Number(item.size || 0));
    const lastModified = Math.max(0, Number(item.lastModified || 0));
    const id = String(item.id || [appId, String(item.name), size, lastModified].join(':'));
    return Object.freeze({
      id,
      name: String(item.name),
      extension,
      appId,
      size,
      lastModified,
      lastOpened: Number(item.lastOpened || item.openedAt || Date.now()),
      created: Boolean(item.created),
      hasHandle: Boolean(item.hasHandle),
    });
  }

  function migrateLegacy() {
    if (storageGet(STORAGE_KEY) !== null) return;
    const legacy = safeParse(storageGet(LEGACY_KEY));
    if (!legacy.length) return;
    const migrated = legacy.map((item) => normalize({
      name: item.name,
      size: item.size,
      extension: item.module,
      lastOpened: item.openedAt,
    })).filter(Boolean);
    storageSet(STORAGE_KEY, JSON.stringify(migrated));
    storageRemove(LEGACY_KEY);
  }

  function read() {
    migrateLegacy();
    return safeParse(storageGet(STORAGE_KEY))
      .map(normalize)
      .filter(Boolean)
      .sort((a, b) => b.lastOpened - a.lastOpened);
  }

  function emitChange(items) {
    if (!global.dispatchEvent || typeof global.CustomEvent !== 'function') return;
    global.dispatchEvent(new CustomEvent('inkdos:recent-files-changed', {
      detail: { count: items.length },
    }));
  }

  function writeItems(items) {
    const next = items.map(normalize).filter(Boolean)
      .sort((a, b) => b.lastOpened - a.lastOpened)
      .slice(0, MAX_ITEMS);
    storageSet(STORAGE_KEY, JSON.stringify(next));
    emitChange(next);
    return next;
  }

  function list(options = {}) {
    const appId = String(options.appId || '');
    return read().filter((item) => !appId || item.appId === appId);
  }

  function stableId(file, appId) {
    return [appId, String(file.name || ''), Number(file.size || 0), Number(file.lastModified || 0)].join(':');
  }

  function registerMetadata(metadata) {
    const item = normalize(metadata);
    if (!item) throw new Error('Recent file metadata is incomplete.');
    const items = read().filter((existing) => existing.id !== item.id);
    items.unshift(item);
    writeItems(items);
    return item;
  }

  async function openHandleDb() {
    if (!global.indexedDB) throw new Error('File handles are unavailable in this browser.');
    return new Promise((resolve, reject) => {
      const request = global.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) db.createObjectStore(STORE_NAME);
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('Recent file handles could not be opened.'));
    });
  }

  async function saveHandle(id, handle) {
    if (!handle) return false;
    try {
      const db = await openHandleDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).put(handle, id);
        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(tx.error);
      });
      db.close();
      return true;
    } catch (error) {
      console.debug('InkDOS could not retain a recent file handle.', error);
      return false;
    }
  }

  async function getHandle(id) {
    try {
      const db = await openHandleDb();
      const value = await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const request = tx.objectStore(STORE_NAME).get(id);
        request.onsuccess = () => resolve(request.result || null);
        request.onerror = () => reject(request.error);
      });
      db.close();
      return value;
    } catch (error) { return null; }
  }

  async function deleteHandle(id) {
    try {
      const db = await openHandleDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).delete(id);
        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
      });
      db.close();
    } catch (error) { console.debug('InkDOS could not remove a recent handle.', error); }
  }

  async function clearHandles() {
    try {
      const db = await openHandleDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).clear();
        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
      });
      db.close();
    } catch (error) { console.debug('InkDOS recent handles could not be cleared.', error); }
  }

  async function registerOpened(file, appId, options = {}) {
    if (!(file instanceof Blob) || !file.name) throw new Error('A local file is required.');
    const owner = String(appId || appForExtension(extensionOf(file.name)) || '');
    if (!owner) throw new Error('No InkDOS app owns this file type.');
    const id = stableId(file, owner);
    const hasHandle = await saveHandle(id, options.handle);
    return registerMetadata({
      id,
      name: file.name,
      extension: extensionOf(file.name),
      appId: owner,
      size: file.size,
      lastModified: file.lastModified,
      lastOpened: Date.now(),
      created: false,
      hasHandle,
    });
  }

  function registerCreated(metadata) {
    const appId = String(metadata && metadata.appId || '');
    const name = String(metadata && metadata.name || '');
    if (!appId || !name) throw new Error('Created-file metadata requires appId and name.');
    return registerMetadata({
      id: String(metadata.id || ['created', appId, name].join(':')),
      name,
      extension: String(metadata.extension || extensionOf(name)),
      appId,
      size: Number(metadata.size || 0),
      lastModified: Number(metadata.lastModified || Date.now()),
      lastOpened: Date.now(),
      created: true,
      hasHandle: false,
    });
  }

  function touch(id) {
    const item = read().find((value) => value.id === id);
    if (!item) return null;
    return registerMetadata(Object.assign({}, item, { lastOpened: Date.now() }));
  }

  async function remove(id) {
    writeItems(read().filter((item) => item.id !== id));
    await deleteHandle(id);
  }

  async function clear() {
    writeItems([]);
    await clearHandles();
  }

  async function resolveFile(id) {
    const item = read().find((value) => value.id === id) || null;
    if (!item) return { item: null, file: null, available: false };
    const handle = await getHandle(id);
    if (!handle || typeof handle.getFile !== 'function') return { item, file: null, available: false };
    try {
      const file = await handle.getFile();
      touch(id);
      return { item, file, handle, available: true };
    } catch (error) { return { item, file: null, available: false, error }; }
  }

  global.InkDOSRecentFiles = Object.freeze({
    version: '1',
    list,
    filter: (appId) => list({ appId }),
    registerOpened,
    registerCreated,
    touch,
    remove,
    clear,
    resolveFile,
    appForExtension,
    extensionOf,
    _test: Object.freeze({ normalize, stableId }),
  });
})(typeof window !== 'undefined' ? window : globalThis);

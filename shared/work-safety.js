/* InkDOS work safety: crash/close recovery drafts, persistent storage and the new-version notice.
 *
 * A workspace attaches a recovery adapter (isDirty, snapshot, restore). While its document has
 * unsaved changes, a draft (the file as the workspace would save it) is written to IndexedDB
 * every ~45 s of editing and whenever the page goes to the background or is closed. Each page
 * keeps its own draft; when a workspace opens and finds a draft whose page is no longer open
 * (no answer to a roll call between InkDOS pages), it offers to recover it. A draft is deleted when its page saves or the user
 * discards it. Drafts stay on this device; persistent storage is requested with the first draft
 * so the browser does not evict them under storage pressure.
 *
 * The service worker never replaces itself under open pages; this module only tells the user that
 * a new version is waiting and will be used once every InkDOS window is closed.
 */
(function (g) {
  'use strict';
  if (g.InkDOSWorkSafety) return;

  const DB = 'inkdos-work-safety', VER = 1, DRAFTS = 'drafts', BEATS = 'beats'; // BEATS kept for schema stability
  const TAB = (g.crypto && g.crypto.randomUUID ? g.crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2));
  const BEAT_MS = 15000, SNAP_MS = 45000, KEEP_MS = 30 * 864e5, MAX_PER_APP = 5;

  const LANG = String(document.documentElement.lang || navigator.language || 'en').toLowerCase();
  const L = (() => {
    const t = {
      en: { found: (n, t) => `Unsaved changes to “${n}” from ${t} were kept on this device.`, recover: 'Recover', discard: 'Discard', update: 'A new InkDOS version is ready. It will be used when every InkDOS window is closed.', ok: 'OK', untitled: 'Untitled' },
      pt: { found: (n, t) => `Alterações não salvas de “${n}” de ${t} foram guardadas neste dispositivo.`, recover: 'Recuperar', discard: 'Descartar', update: 'Uma nova versão do InkDOS está pronta. Ela será usada quando todas as janelas do InkDOS forem fechadas.', ok: 'OK', untitled: 'Sem título' },
      es: { found: (n, t) => `Se guardaron en este dispositivo cambios sin guardar de “${n}” de ${t}.`, recover: 'Recuperar', discard: 'Descartar', update: 'Hay una nueva versión de InkDOS. Se usará cuando se cierren todas las ventanas de InkDOS.', ok: 'Aceptar', untitled: 'Sin título' },
      fr: { found: (n, t) => `Des modifications non enregistrées de « ${n} » (${t}) ont été conservées sur cet appareil.`, recover: 'Récupérer', discard: 'Ignorer', update: 'Une nouvelle version d’InkDOS est prête. Elle sera utilisée quand toutes les fenêtres InkDOS seront fermées.', ok: 'OK', untitled: 'Sans titre' },
      de: { found: (n, t) => `Nicht gespeicherte Änderungen an „${n}“ von ${t} wurden auf diesem Gerät aufbewahrt.`, recover: 'Wiederherstellen', discard: 'Verwerfen', update: 'Eine neue InkDOS-Version ist bereit. Sie wird verwendet, wenn alle InkDOS-Fenster geschlossen sind.', ok: 'OK', untitled: 'Unbenannt' },
      ru: { found: (n, t) => `Несохранённые изменения «${n}» от ${t} сохранены на этом устройстве.`, recover: 'Восстановить', discard: 'Удалить', update: 'Готова новая версия InkDOS. Она будет использоваться после закрытия всех окон InkDOS.', ok: 'ОК', untitled: 'Без названия' },
      ja: { found: (n, t) => `「${n}」の未保存の変更（${t}）がこのデバイスに保存されています。`, recover: '復元', discard: '破棄', update: 'InkDOS の新しいバージョンの準備ができました。すべての InkDOS ウィンドウを閉じると使用されます。', ok: 'OK', untitled: '無題' },
      zh: { found: (n, t) => `“${n}”在 ${t} 的未保存更改已保留在此设备上。`, recover: '恢复', discard: '丢弃', update: 'InkDOS 新版本已就绪，关闭所有 InkDOS 窗口后将会使用。', ok: '确定', untitled: '未命名' }
    };
    return t[LANG.slice(0, 2)] || t.en;
  })();

  // ---- storage
  function openDb() {
    return new Promise((resolve, reject) => {
      if (!g.indexedDB) return reject(new Error('IndexedDB unavailable'));
      const r = indexedDB.open(DB, VER);
      r.onupgradeneeded = () => { const db = r.result; if (!db.objectStoreNames.contains(DRAFTS)) db.createObjectStore(DRAFTS, { keyPath: 'key' }); if (!db.objectStoreNames.contains(BEATS)) db.createObjectStore(BEATS, { keyPath: 'tab' }); };
      r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error);
    });
  }
  async function tx(store, mode, fn) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const t = db.transaction(store, mode), s = t.objectStore(store); let out;
      Promise.resolve(fn(s)).then(v => { out = v; });
      t.oncomplete = () => { db.close(); resolve(out); }; t.onerror = t.onabort = () => { db.close(); reject(t.error); };
    });
  }
  const req = r => new Promise((resolve, reject) => { r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error); });
  const putDraft = d => tx(DRAFTS, 'readwrite', s => { s.put(d); });
  const delDraft = key => tx(DRAFTS, 'readwrite', s => { s.delete(key); });
  const allDrafts = () => tx(DRAFTS, 'readonly', s => req(s.getAll()));
  // which InkDOS pages are open right now: every page answers a roll call on a broadcast channel
  const channel = typeof BroadcastChannel === 'function' ? new BroadcastChannel('inkdos-work-safety') : null;
  if (channel) channel.onmessage = e => { if (e.data && e.data.type === 'who') channel.postMessage({ type: 'here', tab: TAB }); };
  function openTabs() {
    if (!channel) return Promise.resolve(new Set());
    return new Promise(resolve => {
      const seen = new Set(), listen = e => { if (e.data && e.data.type === 'here') seen.add(e.data.tab); };
      channel.addEventListener('message', listen); channel.postMessage({ type: 'who' });
      setTimeout(() => { channel.removeEventListener('message', listen); resolve(seen); }, 400);
    });
  }

  let persistAsked = false;
  function askPersistence() {
    if (persistAsked) return; persistAsked = true;
    try { if (navigator.storage && navigator.storage.persisted) navigator.storage.persisted().then(p => { if (!p && navigator.storage.persist) navigator.storage.persist().catch(() => {}); }).catch(() => {}); } catch (_) {}
  }

  // ---- small notice bar
  function bar(text, actions) {
    const el = document.createElement('div');
    el.className = 'inkdos-safety-bar'; el.setAttribute('role', 'status');
    el.style.cssText = 'position:fixed;left:50%;bottom:44px;transform:translateX(-50%);z-index:2147483000;max-width:min(680px,calc(100vw - 24px));display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 12px;border-radius:10px;font:13px/1.4 system-ui,sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.18);background:#fff;color:#1f2329;border:1px solid #d9dde3';
    if (g.matchMedia && g.matchMedia('(prefers-color-scheme: dark)').matches && document.documentElement.dataset.theme !== 'light') { el.style.background = '#23262c'; el.style.color = '#e8eaed'; el.style.borderColor = '#3a3e46'; }
    const msg = document.createElement('span'); msg.textContent = text; msg.style.flex = '1 1 260px'; el.append(msg);
    for (const a of actions) {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = a.label;
      b.style.cssText = 'font:inherit;padding:5px 12px;border-radius:7px;cursor:pointer;border:1px solid currentColor;background:transparent;color:inherit' + (a.primary ? ';background:#c4362c;border-color:#c4362c;color:#fff' : '');
      b.addEventListener('click', async () => { el.remove(); try { await a.run(); } catch (e) { console.error(e); } });
      el.append(b);
    }
    (document.body || document.documentElement).append(el);
    return el;
  }

  // ---- recovery
  const handles = [];
  function attachRecovery(adapter) {
    const app = String(adapter.app), key = app + ':' + TAB;
    let lastSnap = 0, lastRevision = null, wrote = false, running = false, offered = false;

    async function snapshot(force) {
      if (running) return;
      let dirty = false;
      try { dirty = !!adapter.isDirty(); } catch (_) { return; }
      if (!dirty) { if (wrote) { wrote = false; lastRevision = null; delDraft(key).catch(() => {}); } return; }
      const revision = typeof adapter.revision === 'function' ? adapter.revision() : null;
      const now = Date.now();
      if (!force && (now - lastSnap < SNAP_MS || (revision !== null && revision === lastRevision))) return;
      if (force && revision !== null && revision === lastRevision && wrote) return;
      running = true;
      try {
        const out = await adapter.snapshot();
        if (!out || !out.data) return;
        const data = out.data instanceof Blob ? out.data : new Blob([out.data]);
        await putDraft({ key, app, tab: TAB, name: out.name || L.untitled, savedAt: Date.now(), data });
        wrote = true; lastSnap = Date.now(); lastRevision = revision; askPersistence();
      } catch (e) { console.warn('InkDOS recovery draft not written', e); } finally { running = false; }
    }

    async function offer() {
      if (offered) return; offered = true;
      let drafts = [];
      try {
        const [list, alive] = await Promise.all([allDrafts(), openTabs()]);
        const mine = list.filter(d => d.app === app && d.tab !== TAB).sort((a, b) => b.savedAt - a.savedAt);
        for (const d of mine.slice(MAX_PER_APP)) delDraft(d.key).catch(() => {});
        for (const d of mine) if (Date.now() - d.savedAt > KEEP_MS) delDraft(d.key).catch(() => {});
        drafts = mine.slice(0, MAX_PER_APP).filter(d => !alive.has(d.tab) && Date.now() - d.savedAt <= KEEP_MS);
      } catch (_) { return; }
      const d = drafts[0];
      if (!d) return;
      const when = new Date(d.savedAt).toLocaleString();
      bar(L.found(d.name, when), [
        { label: L.recover, primary: true, run: async () => { await adapter.restore(new File([d.data], d.name, { type: d.data.type || '' })); await delDraft(d.key).catch(() => {}); } },
        { label: L.discard, run: () => delDraft(d.key) }
      ]);
    }

    setInterval(() => snapshot(false), BEAT_MS);
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') snapshot(true); });
    g.addEventListener('pagehide', () => { snapshot(true); });
    setTimeout(offer, 1200);
    const handle = Object.freeze({ snapshotNow: () => snapshot(true), offer });
    handles.push(handle);
    return handle;
  }

  // ---- new version waiting
  function watchUpdates() {
    if (!navigator.serviceWorker || !navigator.serviceWorker.getRegistration) return;
    let shown = false;
    const show = () => { if (shown || !navigator.serviceWorker.controller) return; shown = true; bar(L.update, [{ label: L.ok, run: () => {} }]); };
    navigator.serviceWorker.getRegistration().then(reg => {
      if (!reg) return;
      if (reg.waiting) show();
      reg.addEventListener('updatefound', () => { const w = reg.installing; if (w) w.addEventListener('statechange', () => { if (w.state === 'installed') show(); }); });
      setInterval(() => reg.update().catch(() => {}), 6 * 3600e3);
    }).catch(() => {});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', watchUpdates, { once: true }); else watchUpdates();

  g.InkDOSWorkSafety = Object.freeze({ attachRecovery, _test: { TAB, allDrafts, handles } });
})(globalThis);

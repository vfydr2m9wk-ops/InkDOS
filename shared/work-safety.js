/* InkDOS work safety: crash/close recovery drafts, persistent storage and the new-version notice.
 *
 * A workspace attaches a recovery adapter (isDirty, snapshot, restore). While its document has
 * unsaved changes, a draft (the file as the workspace would save it) is written to IndexedDB
 * every ~45 s of editing and whenever the page goes to the background or is closed. Each page
 * keeps its own draft; when a workspace opens and finds a draft whose page is no longer open
 * (no answer to a roll call between InkDOS pages), it offers to recover it. A draft is deleted when its page saves or the user
 * discards it. Drafts stay on this device, encrypted, for at most 7 days, and can be turned off in
 * Settings; persistent storage is requested with the first draft
 * so the browser does not evict them under storage pressure.
 *
 * The service worker never replaces itself under open pages; this module only tells the user that
 * a new version is waiting and will be used once every InkDOS window is closed.
 */
(function (g) {
  'use strict';
  if (g.InkDOSWorkSafety) return;

  const DB = 'inkdos-work-safety', VER = 2, DRAFTS = 'drafts', BEATS = 'beats', KEYS = 'keys'; // BEATS kept for schema stability
  const ENABLED_KEY = 'inkdos.recoveryDrafts';
  const TAB = (g.crypto && g.crypto.randomUUID ? g.crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2));
  const BEAT_MS = 15000, SNAP_MS = 45000, KEEP_MS = 7 * 864e5, MAX_PER_APP = 5;

  const LANG = String(document.documentElement.lang || navigator.language || 'en').toLowerCase();
  const L = (() => {
    const t = {
      en: { found: (n, t) => `Unsaved changes to “${n}” from ${t} were kept on this device.`, recover: 'Recover', discard: 'Discard', update: 'A new InkDOS version is ready. It will be used when every InkDOS window is closed.', ok: 'OK', untitled: 'Untitled' , pwTitle: 'Protect recovery drafts', pwWhy: "Choose a password for this session's recovery drafts. It keeps them unreadable to anyone else using this browser or device. The password is never stored: InkDOS forgets it when the page closes, and without it the drafts cannot be recovered.", pwLabel: 'Password', pwRepeat: 'Repeat password', pwUse: 'Use password', pwSkip: 'Skip (no draft this session)', pwMismatch: 'The passwords do not match or are shorter than 6 characters.', unlockTitle: 'Unlock recovery draft', unlockWhy: 'Enter the password used when this draft was kept. It is not stored anywhere.', unlock: 'Unlock', cancel: 'Cancel', wrong: 'Wrong password.', foundLocked: t => `Unsaved changes from ${t} were kept on this device, protected by a password.` },
      pt: { found: (n, t) => `Alterações não salvas de “${n}” de ${t} foram guardadas neste dispositivo.`, recover: 'Recuperar', discard: 'Descartar', update: 'Uma nova versão do InkDOS está pronta. Ela será usada quando todas as janelas do InkDOS forem fechadas.', ok: 'OK', untitled: 'Sem título' , pwTitle: 'Proteger rascunhos de recuperação', pwWhy: 'Escolha uma senha para os rascunhos de recuperação desta sessão. Ela os deixa ilegíveis para qualquer outra pessoa que use este navegador ou dispositivo. A senha nunca é guardada: o InkDOS a esquece ao fechar a página e, sem ela, os rascunhos não podem ser recuperados.', pwLabel: 'Senha', pwRepeat: 'Repita a senha', pwUse: 'Usar senha', pwSkip: 'Pular (sem rascunho nesta sessão)', pwMismatch: 'As senhas não conferem ou têm menos de 6 caracteres.', unlockTitle: 'Desbloquear rascunho de recuperação', unlockWhy: 'Digite a senha usada quando este rascunho foi guardado. Ela não fica salva em lugar nenhum.', unlock: 'Desbloquear', cancel: 'Cancelar', wrong: 'Senha incorreta.', foundLocked: t => `Alterações não salvas de ${t} foram guardadas neste dispositivo, protegidas por senha.` },
      es: { found: (n, t) => `Se guardaron en este dispositivo cambios sin guardar de “${n}” de ${t}.`, recover: 'Recuperar', discard: 'Descartar', update: 'Hay una nueva versión de InkDOS. Se usará cuando se cierren todas las ventanas de InkDOS.', ok: 'Aceptar', untitled: 'Sin título' , pwTitle: 'Proteger borradores de recuperación', pwWhy: 'Elija una contraseña para los borradores de recuperación de esta sesión. Los hace ilegibles para cualquier otra persona que use este navegador o dispositivo. La contraseña nunca se guarda: InkDOS la olvida al cerrar la página y, sin ella, los borradores no se pueden recuperar.', pwLabel: 'Contraseña', pwRepeat: 'Repita la contraseña', pwUse: 'Usar contraseña', pwSkip: 'Omitir (sin borrador en esta sesión)', pwMismatch: 'Las contraseñas no coinciden o tienen menos de 6 caracteres.', unlockTitle: 'Desbloquear borrador', unlockWhy: 'Escriba la contraseña usada cuando se guardó este borrador. No se guarda en ningún lugar.', unlock: 'Desbloquear', cancel: 'Cancelar', wrong: 'Contraseña incorrecta.', foundLocked: t => `Se guardaron en este dispositivo cambios sin guardar de ${t}, protegidos con contraseña.` },
      fr: { found: (n, t) => `Des modifications non enregistrées de « ${n} » (${t}) ont été conservées sur cet appareil.`, recover: 'Récupérer', discard: 'Ignorer', update: 'Une nouvelle version d’InkDOS est prête. Elle sera utilisée quand toutes les fenêtres InkDOS seront fermées.', ok: 'OK', untitled: 'Sans titre' , pwTitle: 'Protéger les brouillons de récupération', pwWhy: 'Choisissez un mot de passe pour les brouillons de récupération de cette session. Il les rend illisibles pour toute autre personne utilisant ce navigateur ou cet appareil. Le mot de passe n’est jamais enregistré : InkDOS l’oublie à la fermeture de la page et, sans lui, les brouillons ne peuvent pas être récupérés.', pwLabel: 'Mot de passe', pwRepeat: 'Répéter le mot de passe', pwUse: 'Utiliser le mot de passe', pwSkip: 'Ignorer (pas de brouillon pour cette session)', pwMismatch: 'Les mots de passe ne correspondent pas ou font moins de 6 caractères.', unlockTitle: 'Déverrouiller le brouillon', unlockWhy: 'Saisissez le mot de passe utilisé lors de la conservation de ce brouillon. Il n’est enregistré nulle part.', unlock: 'Déverrouiller', cancel: 'Annuler', wrong: 'Mot de passe incorrect.', foundLocked: t => `Des modifications non enregistrées (${t}) ont été conservées sur cet appareil, protégées par mot de passe.` },
      de: { found: (n, t) => `Nicht gespeicherte Änderungen an „${n}“ von ${t} wurden auf diesem Gerät aufbewahrt.`, recover: 'Wiederherstellen', discard: 'Verwerfen', update: 'Eine neue InkDOS-Version ist bereit. Sie wird verwendet, wenn alle InkDOS-Fenster geschlossen sind.', ok: 'OK', untitled: 'Unbenannt' , pwTitle: 'Wiederherstellungsentwürfe schützen', pwWhy: 'Wählen Sie ein Passwort für die Wiederherstellungsentwürfe dieser Sitzung. Es macht sie für andere Personen, die diesen Browser oder dieses Gerät nutzen, unlesbar. Das Passwort wird nie gespeichert: InkDOS vergisst es beim Schließen der Seite, und ohne es können die Entwürfe nicht wiederhergestellt werden.', pwLabel: 'Passwort', pwRepeat: 'Passwort wiederholen', pwUse: 'Passwort verwenden', pwSkip: 'Überspringen (kein Entwurf in dieser Sitzung)', pwMismatch: 'Die Passwörter stimmen nicht überein oder sind kürzer als 6 Zeichen.', unlockTitle: 'Entwurf entsperren', unlockWhy: 'Geben Sie das Passwort ein, das beim Aufbewahren dieses Entwurfs verwendet wurde. Es wird nirgends gespeichert.', unlock: 'Entsperren', cancel: 'Abbrechen', wrong: 'Falsches Passwort.', foundLocked: t => `Nicht gespeicherte Änderungen von ${t} wurden auf diesem Gerät aufbewahrt, durch ein Passwort geschützt.` },
      ru: { found: (n, t) => `Несохранённые изменения «${n}» от ${t} сохранены на этом устройстве.`, recover: 'Восстановить', discard: 'Удалить', update: 'Готова новая версия InkDOS. Она будет использоваться после закрытия всех окон InkDOS.', ok: 'ОК', untitled: 'Без названия' , pwTitle: 'Защита черновиков восстановления', pwWhy: 'Задайте пароль для черновиков восстановления этого сеанса. Он делает их нечитаемыми для других пользователей этого браузера или устройства. Пароль нигде не сохраняется: InkDOS забывает его при закрытии страницы, и без него черновики восстановить нельзя.', pwLabel: 'Пароль', pwRepeat: 'Повторите пароль', pwUse: 'Использовать пароль', pwSkip: 'Пропустить (без черновика в этом сеансе)', pwMismatch: 'Пароли не совпадают или короче 6 символов.', unlockTitle: 'Разблокировать черновик', unlockWhy: 'Введите пароль, использованный при сохранении этого черновика. Он нигде не хранится.', unlock: 'Разблокировать', cancel: 'Отмена', wrong: 'Неверный пароль.', foundLocked: t => `Несохранённые изменения от ${t} сохранены на этом устройстве под паролем.` },
      ja: { found: (n, t) => `「${n}」の未保存の変更（${t}）がこのデバイスに保存されています。`, recover: '復元', discard: '破棄', update: 'InkDOS の新しいバージョンの準備ができました。すべての InkDOS ウィンドウを閉じると使用されます。', ok: 'OK', untitled: '無題' , pwTitle: '復元用下書きの保護', pwWhy: 'このセッションの復元用下書きのパスワードを設定してください。このブラウザーやデバイスを使う他の人には読めなくなります。パスワードは保存されません。ページを閉じると InkDOS は忘れ、パスワードがないと下書きは復元できません。', pwLabel: 'パスワード', pwRepeat: 'パスワード（確認）', pwUse: 'パスワードを使用', pwSkip: 'スキップ（このセッションは下書きなし）', pwMismatch: 'パスワードが一致しないか、6 文字未満です。', unlockTitle: '下書きのロック解除', unlockWhy: 'この下書きを保存したときのパスワードを入力してください。どこにも保存されません。', unlock: 'ロック解除', cancel: 'キャンセル', wrong: 'パスワードが違います。', foundLocked: t => `${t} の未保存の変更が、パスワードで保護されてこのデバイスに保存されています。` },
      zh: { found: (n, t) => `“${n}”在 ${t} 的未保存更改已保留在此设备上。`, recover: '恢复', discard: '丢弃', update: 'InkDOS 新版本已就绪，关闭所有 InkDOS 窗口后将会使用。', ok: '确定', untitled: '未命名' , pwTitle: '保护恢复草稿', pwWhy: '为本次会话的恢复草稿设置密码。使用此浏览器或设备的其他人将无法读取。密码不会被保存：关闭页面后 InkDOS 即会忘记，没有密码将无法恢复草稿。', pwLabel: '密码', pwRepeat: '再次输入密码', pwUse: '使用密码', pwSkip: '跳过（本次会话不保存草稿）', pwMismatch: '两次密码不一致或少于 6 个字符。', unlockTitle: '解锁恢复草稿', unlockWhy: '输入保存此草稿时使用的密码。密码不会保存在任何地方。', unlock: '解锁', cancel: '取消', wrong: '密码错误。', foundLocked: t => `${t} 的未保存更改已在此设备上以密码保护保留。` }
    };
    return t[LANG.slice(0, 2)] || t.en;
  })();

  // ---- storage
  function openDb() {
    return new Promise((resolve, reject) => {
      if (!g.indexedDB) return reject(new Error('IndexedDB unavailable'));
      const r = indexedDB.open(DB, VER);
      r.onupgradeneeded = () => { const db = r.result; if (!db.objectStoreNames.contains(DRAFTS)) db.createObjectStore(DRAFTS, { keyPath: 'key' }); if (!db.objectStoreNames.contains(BEATS)) db.createObjectStore(BEATS, { keyPath: 'tab' }); if (!db.objectStoreNames.contains(KEYS)) db.createObjectStore(KEYS); };
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

  // Drafts are encrypted (AES-GCM) with a key generated in this browser and stored non-extractable, so the
  // draft bytes and file names are not readable in the browser's storage files; without WebCrypto no draft
  // is kept. Drafts can be turned off in Settings; turning them off deletes every draft.
  const subtle = g.crypto && g.crypto.subtle;
  let keyPromise = null;
  function draftKey() {
    if (!keyPromise) keyPromise = tx(KEYS, 'readonly', s => req(s.get('draft'))).then(async k => {
      if (k) return k;
      const fresh = await subtle.generateKey({ name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
      await tx(KEYS, 'readwrite', s => { s.put(fresh, 'draft'); });
      return fresh;
    }).catch(e => { keyPromise = null; throw e; });
    return keyPromise;
  }
  async function seal(bytes, key) { const iv = g.crypto.getRandomValues(new Uint8Array(12)); return { iv, ct: new Uint8Array(await subtle.encrypt({ name: 'AES-GCM', iv }, key || await draftKey(), bytes)) }; }
  async function open(sealed, key) { return new Uint8Array(await subtle.decrypt({ name: 'AES-GCM', iv: sealed.iv }, key || await draftKey(), sealed.ct)); }
  // password mode: the key is derived from a password (PBKDF2-SHA-256) that is asked once per page and kept
  // only in memory; neither the password nor the derived key is ever stored
  const PBKDF2_ROUNDS = 310000;
  async function passwordKey(password, salt) {
    const base = await subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
    return subtle.deriveKey({ name: 'PBKDF2', salt, iterations: PBKDF2_ROUNDS, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
  }
  const session = { key: null, salt: null, declined: false, asking: false };
  const text = new TextEncoder(), untext = new TextDecoder();
  function mode() { try { const m = g.localStorage.getItem(ENABLED_KEY); return m === 'off' || m === 'password' ? m : 'on'; } catch (_) { return 'on'; } }
  function enabled() { return mode() !== 'off'; }
  async function setMode(m) {
    m = m === 'off' || m === 'password' ? m : 'on';
    try { g.localStorage.setItem(ENABLED_KEY, m); } catch (_) {}
    session.key = null; session.salt = null; session.declined = false;
    if (m === 'off') await tx(DRAFTS, 'readwrite', s => { s.clear(); }).catch(() => {});
  }
  const setEnabled = on => setMode(on ? 'on' : 'off');

  // password dialog. The field is a plain text input masked with CSS where the browser supports it, outside
  // any form, with autocomplete off and password-manager opt-outs, so browsers do not offer to save it.
  function askPassword({ title, why, repeat, confirmLabel, cancelLabel, verify }) {
    return new Promise(resolve => {
      const shade = document.createElement('div');
      shade.className = 'inkdos-safety-dialog';
      shade.style.cssText = 'position:fixed;inset:0;z-index:2147483001;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;padding:16px';
      const dark = g.matchMedia && g.matchMedia('(prefers-color-scheme: dark)').matches && document.documentElement.dataset.theme !== 'light';
      const box = document.createElement('div');
      box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-label', title);
      box.style.cssText = 'width:min(440px,100%);border-radius:12px;padding:18px;font:14px/1.45 system-ui,sans-serif;box-shadow:0 12px 40px rgba(0,0,0,.3);' + (dark ? 'background:#23262c;color:#e8eaed' : 'background:#fff;color:#1f2329');
      const h = document.createElement('h2'); h.textContent = title; h.style.cssText = 'margin:0 0 8px;font-size:17px';
      const p = document.createElement('p'); p.textContent = why; p.style.cssText = 'margin:0 0 12px;opacity:.85';
      const masked = !!(g.CSS && CSS.supports && CSS.supports('-webkit-text-security', 'disc'));
      const field = label => {
        const l = document.createElement('label'); l.style.cssText = 'display:block;margin:0 0 10px;font-size:13px';
        const i = document.createElement('input');
        i.type = masked ? 'text' : 'password';
        if (masked) i.style.setProperty('-webkit-text-security', 'disc');
        i.autocomplete = masked ? 'off' : 'new-password'; i.spellcheck = false; i.setAttribute('autocapitalize', 'off'); i.setAttribute('autocorrect', 'off');
        i.name = 'k' + Math.random().toString(36).slice(2);
        for (const a of ['data-lpignore', 'data-1p-ignore', 'data-bwignore', 'data-form-type']) i.setAttribute(a, a === 'data-form-type' ? 'other' : 'true');
        i.style.cssText += ';display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:7px 9px;border-radius:7px;border:1px solid #9aa1ab;font:inherit;background:transparent;color:inherit';
        l.append(label, i); return [l, i];
      };
      const [l1, i1] = field(L.pwLabel), extra = repeat ? field(L.pwRepeat) : null;
      const err = document.createElement('p'); err.style.cssText = 'margin:0 0 10px;color:#c4362c;min-height:1.2em;font-size:13px';
      const row = document.createElement('div'); row.style.cssText = 'display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap';
      const btn = (label, primary) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.style.cssText = 'font:inherit;padding:6px 14px;border-radius:7px;cursor:pointer;border:1px solid currentColor;background:transparent;color:inherit' + (primary ? ';background:#c4362c;border-color:#c4362c;color:#fff' : ''); return b; };
      const cancel = btn(cancelLabel), ok = btn(confirmLabel, true);
      row.append(cancel, ok);
      box.append(h, p, l1, ...(extra ? [extra[0]] : []), err, row); shade.append(box); document.body.append(shade);
      const done = v => { i1.value = ''; if (extra) extra[1].value = ''; shade.remove(); resolve(v); };
      cancel.addEventListener('click', () => done(null));
      const submit = async () => {
        const v = i1.value;
        if (repeat && (v.length < 6 || v !== extra[1].value)) { err.textContent = L.pwMismatch; return; }
        if (!v) return;
        if (verify) { ok.disabled = true; const good = await verify(v); ok.disabled = false; if (!good) { err.textContent = L.wrong; i1.select(); return; } }
        done(v);
      };
      ok.addEventListener('click', submit);
      box.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); submit(); } else if (e.key === 'Escape') done(null); });
      setTimeout(() => i1.focus(), 0);
    });
  }
  async function sessionPasswordKey() {
    if (session.key) return session.key;
    if (session.declined || session.asking || document.visibilityState !== 'visible') return null;
    session.asking = true;
    try {
      const pw = await askPassword({ title: L.pwTitle, why: L.pwWhy, repeat: true, confirmLabel: L.pwUse, cancelLabel: L.pwSkip });
      if (!pw) { session.declined = true; return null; }
      session.salt = g.crypto.getRandomValues(new Uint8Array(16));
      session.key = await passwordKey(pw, session.salt);
      return session.key;
    } finally { session.asking = false; }
  }
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
      if (!dirty || !enabled()) { if (wrote) { wrote = false; lastRevision = null; delDraft(key).catch(() => {}); } return; }
      const revision = typeof adapter.revision === 'function' ? adapter.revision() : null;
      const now = Date.now();
      if (!force && (now - lastSnap < SNAP_MS || (revision !== null && revision === lastRevision))) return;
      if (force && revision !== null && revision === lastRevision && wrote) return;
      running = true;
      try {
        const out = await adapter.snapshot();
        if (!out || !out.data) return;
        if (!enabled() || !subtle) return;
        const protect = mode() === 'password', pkey = protect ? await sessionPasswordKey() : null;
        if (protect && !pkey) return;
        const raw = out.data instanceof Blob ? new Uint8Array(await out.data.arrayBuffer()) : new Uint8Array(out.data);
        const [body, name] = await Promise.all([seal(raw, pkey), seal(text.encode(out.name || L.untitled), pkey)]);
        await putDraft(protect ? { key, app, tab: TAB, savedAt: Date.now(), v: 3, salt: session.salt, rounds: PBKDF2_ROUNDS, body, name }
          : { key, app, tab: TAB, savedAt: Date.now(), v: 2, body, name });
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
        for (const d of mine) if (Date.now() - d.savedAt > KEEP_MS || (d.v !== 2 && d.v !== 3)) delDraft(d.key).catch(() => {}); // expired or unencrypted (older versions)
        if (!enabled() || !subtle) return;
        drafts = mine.slice(0, MAX_PER_APP).filter(d => (d.v === 2 || d.v === 3) && !alive.has(d.tab) && Date.now() - d.savedAt <= KEEP_MS);
      } catch (_) { return; }
      const d = drafts[0];
      if (!d) return;
      const when = new Date(d.savedAt).toLocaleString();
      if (d.v === 3) {
        bar(L.foundLocked(when), [
          { label: L.recover, primary: true, run: async () => {
            let key = null;
            const pw = await askPassword({ title: L.unlockTitle, why: L.unlockWhy, confirmLabel: L.unlock, cancelLabel: L.cancel,
              verify: async v => { try { const k = await passwordKey(v, d.salt); await open(d.name, k); key = k; return true; } catch (_) { return false; } } });
            if (!pw || !key) { offered = false; return offer(); }
            const name = untext.decode(await open(d.name, key));
            await adapter.restore(new File([await open(d.body, key)], name)); await delDraft(d.key).catch(() => {});
          } },
          { label: L.discard, run: () => delDraft(d.key) }
        ]);
        return;
      }
      let name;
      try { name = untext.decode(await open(d.name)); } catch (_) { delDraft(d.key).catch(() => {}); return; } // key lost or data damaged
      bar(L.found(name, when), [
        { label: L.recover, primary: true, run: async () => { await adapter.restore(new File([await open(d.body)], name)); await delDraft(d.key).catch(() => {}); } },
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

  g.InkDOSWorkSafety = Object.freeze({ attachRecovery, get draftsEnabled() { return enabled(); }, setDraftsEnabled: setEnabled, get draftsMode() { return mode(); }, setDraftsMode: setMode, _test: { TAB, allDrafts, handles } });
})(globalThis);

// Page world of InkDOS workspace pages: receives the file from bridge-isolated.js and gives it to the
// workspace through its own launch bridge (InkDOSFileLaunch.routeFile), the same path used when the
// operating system opens a file in InkDOS. The workspace itself is unchanged.
'use strict';
(() => {
  if (!/[#&]inkdos-ext=/.test(location.hash)) return;
  window.addEventListener('message', event => {
    if (event.source !== window || event.data?.source !== 'inkdos-extension') return;
    const file = event.data.file || {};
    try { history.replaceState(history.state, '', location.pathname + location.search); } catch (_) {}
    if (file.error || !file.data) { console.warn('InkDOS extension: the file is no longer available; open it again from the link.'); return; }
    const raw = atob(file.data), bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    const launched = new File([bytes], file.name, {type: file.type || ''});
    const started = Date.now();
    const deliver = () => {
      const bridge = window.InkDOSFileLaunch;
      if (bridge && typeof bridge.routeFile === 'function') { bridge.routeFile(launched).catch(error => console.error('InkDOS extension open failed:', error)); return; }
      if (Date.now() - started < 20000) setTimeout(deliver, 50);
    };
    deliver();
  });
})();

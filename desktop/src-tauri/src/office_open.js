(function () {
  'use strict';
  // InkDOS desktop: the file opened from the system, handed to this ONLYOFFICE window once (embed mode, own origin)
  if (location.origin !== 'https://inkdos-tools.github.io' || location.pathname !== '/editor') return;
  try { if (sessionStorage.getItem('inkdos-office-file')) return; sessionStorage.setItem('inkdos-office-file', '1'); } catch (_) {}
  var name = __NAME__, data = __DATA__;
  addEventListener('message', function ready(event) {
    if (event.origin !== location.origin || !event.data || event.data.type !== 'document:ready') return;
    removeEventListener('message', ready);
    var text = atob(data), bytes = new Uint8Array(text.length);
    for (var i = 0; i < text.length; i++) bytes[i] = text.charCodeAt(i);
    data = null;
    window.postMessage({ id: 'inkdos-launch', type: 'document:open-file', payload: { file: new File([bytes], name), fileName: name } }, location.origin);
  });
})();

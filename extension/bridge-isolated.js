// Runs on InkDOS workspace pages opened by the extension (#inkdos-ext=<token>): fetches the file from the
// extension and passes it to the page world (bridge-main.js), which hands it to the workspace.
'use strict';
(() => {
  const m = /[#&]inkdos-ext=([0-9a-f-]{36})/.exec(location.hash);
  if (!m) return;
  chrome.runtime.sendMessage({type: 'inkdos-ext-file', token: m[1]}, file => {
    window.postMessage({source: 'inkdos-extension', file: file || {error: 'unavailable'}}, location.origin);
  });
})();

// A PDF opened in a tab was redirected here (see applyViewerRule in background.js): the background downloads it with
// the browser's session and this page moves on to the InkDOS PDF workspace. If that fails, the PDF can still be
// opened in the browser's own viewer.
'use strict';
(() => {
  const target = location.hash.slice(1);
  const title = document.getElementById('title'), detail = document.getElementById('detail'), browser = document.getElementById('browser');
  const inBrowser = () => chrome.runtime.sendMessage({type: 'inkdos-allow-once', url: target}, () => location.replace(target));
  browser.addEventListener('click', inBrowser);
  if (!/^https?:\/\//i.test(target)) { title.textContent = 'Nothing to open'; return; }
  detail.textContent = decodeURIComponent(target.split(/[?#]/)[0].split('/').pop() || '') || target;
  browser.hidden = false;
  chrome.runtime.sendMessage({type: 'inkdos-open-url', url: target}, reply => {
    if (reply?.url) { location.replace(reply.url); return; }
    title.textContent = 'InkDOS could not open this file';
    detail.textContent = reply?.error || chrome.runtime.lastError?.message || 'Unknown error';
  });
})();

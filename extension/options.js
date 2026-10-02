'use strict';
const DEFAULTS = {pdfViewer: true, downloads: true};
chrome.storage.local.get(Object.keys(DEFAULTS), saved => {
  for (const [key, value] of Object.entries({...DEFAULTS, ...saved})) {
    const box = document.getElementById(key);
    box.checked = value;
    box.addEventListener('change', () => chrome.storage.local.set({[key]: box.checked}));
  }
});

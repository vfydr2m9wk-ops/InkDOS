// InkDOS hand-over page: invisible, framed by an ONLYOFFICE or BentoPDF page of the engine site
// (https://inkdos-tools.github.io) that InkDOS opened as a separate page (inside the XeOS web desktop, where a framed
// editor does not scroll). It gives that page the one document InkDOS kept for it (IndexedDB 'inkdos-tool-handoff',
// key from ?id=), once, and only to the engine origin (postMessage target), then forgets it and anything older
// than a day.
(function () {
  'use strict';
  var TOOLS = 'https://inkdos-tools.github.io', DAY = 864e5;
  var id = new URLSearchParams(location.search).get('id');
  if (window.parent === window || !id || !/^[A-Za-z0-9-]{8,64}$/.test(id) || !window.indexedDB) return;
  var req = indexedDB.open('inkdos-tool-handoff', 1);
  req.onupgradeneeded = function () { req.result.createObjectStore('files'); };
  req.onsuccess = function () {
    var db = req.result, tx = db.transaction('files', 'readwrite'), files = tx.objectStore('files'), item = null;
    files.get(id).onsuccess = function (event) { item = event.target.result || null; files.delete(id); };
    files.openCursor().onsuccess = function (event) {
      var cursor = event.target.result;
      if (!cursor) return;
      if (!cursor.value || !(cursor.value.at > Date.now() - DAY)) cursor.delete();
      cursor.continue();
    };
    tx.oncomplete = function () {
      db.close();
      if (item && item.file instanceof Blob) window.parent.postMessage({ type: 'inkdos-handoff-file', file: item.file, name: item.name }, TOOLS);
    };
  };
})();

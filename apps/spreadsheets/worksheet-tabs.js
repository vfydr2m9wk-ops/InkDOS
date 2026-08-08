(function (global) {
  'use strict';

  function nextSheetName(sheets) {
    const used = new Set((sheets || []).map(sheet => String(sheet.name || '').toLowerCase()));
    let index = 1;
    let name = '';
    do {
      name = `Sheet${index++}`;
    } while (used.has(name.toLowerCase()));
    return name;
  }

  function render(container, book, options) {
    if (!container || !book) return;
    const settings = options || {};
    container.innerHTML = '';
    const all = (book.sheets || []).map((sheet, index) => ({ sheet, index }));
    const visible = all.filter(item => item.sheet.state !== 'hidden' && item.sheet.state !== 'veryHidden');
    for (const item of (visible.length ? visible : all)) {
      const button = document.createElement('button');
      button.textContent = item.sheet.name;
      button.className = item.index === book.active ? 'active' : '';
      button.addEventListener('click', () => {
        if (typeof settings.onActivate === 'function') settings.onActivate(item.index);
      });
      container.appendChild(button);
    }
    const add = document.createElement('button');
    add.id = 'addSheetBtn';
    add.type = 'button';
    add.textContent = '+';
    add.title = 'Add worksheet';
    add.setAttribute('aria-label', 'Add worksheet');
    add.addEventListener('click', () => {
      if (typeof settings.canAdd === 'function' && !settings.canAdd()) return;
      if (typeof settings.createBlank !== 'function') return;
      const blank = settings.createBlank();
      if (!blank) return;
      const name = nextSheetName(book.sheets);
      blank.name = name;
      blank.path = '';
      blank.xml = '';
      book.sheets.push(blank);
      const index = book.sheets.length - 1;
      book.active = index;
      if (typeof settings.onAdd === 'function') settings.onAdd(name, index);
    });
    container.appendChild(add);
  }

  global.InkDeskSpreadsheetWorksheetTabs = Object.freeze({ render, nextSheetName });
})(typeof window !== 'undefined' ? window : globalThis);

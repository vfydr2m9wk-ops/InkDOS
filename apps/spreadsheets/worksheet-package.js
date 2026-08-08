(function (global) {
  'use strict';

  const MAIN_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main';
  const REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships';
  const PACKAGE_REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships';

  function parseXml(text, context) {
    if (global.InkDeskRuntime) return global.InkDeskRuntime.parseXml(text, context);
    const document = new DOMParser().parseFromString(text, 'application/xml');
    if (document.querySelector('parsererror')) throw new Error(`Invalid XML in ${context}`);
    return document;
  }

  function serialize(document) {
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      new XMLSerializer().serializeToString(document).replace(/^<\?xml[^>]*>\s*/, '');
  }

  function localAll(node, name) {
    return node ? [...node.querySelectorAll('*')].filter(item => item.localName === name) : [];
  }

  function localOne(node, name) {
    return localAll(node, name)[0] || null;
  }

  function nextWorksheetPath(zip, usedPaths, start) {
    let number = start;
    while (usedPaths.has(`xl/worksheets/sheet${number}.xml`) || zip.file(`xl/worksheets/sheet${number}.xml`)) number++;
    return { path: `xl/worksheets/sheet${number}.xml`, next: number + 1 };
  }

  async function appendNewSheets(zip, book, options) {
    const pending = (book.sheets || []).filter(sheet => !sheet.path || !zip.file(sheet.path));
    if (!pending.length) return false;
    const serializeSheet = options && options.serializeSheet;
    if (typeof serializeSheet !== 'function') throw new Error('Worksheet serializer is unavailable.');

    const workbookRaw = await zip.file('xl/workbook.xml')?.async('text');
    const relationshipsRaw = await zip.file('xl/_rels/workbook.xml.rels')?.async('text');
    const contentTypesRaw = await zip.file('[Content_Types].xml')?.async('text');
    if (!workbookRaw || !relationshipsRaw || !contentTypesRaw) {
      throw new Error('Workbook package metadata is incomplete; a new worksheet cannot be added safely.');
    }

    const workbook = parseXml(workbookRaw, 'xl/workbook.xml');
    const relationships = parseXml(relationshipsRaw, 'xl/_rels/workbook.xml.rels');
    const contentTypes = parseXml(contentTypesRaw, '[Content_Types].xml');
    const sheetsNode = localOne(workbook, 'sheets');
    if (!sheetsNode) throw new Error('Workbook sheet registry is missing.');

    const usedPaths = new Set(Object.keys(zip.files).filter(path => /^xl\/worksheets\/sheet\d+\.xml$/i.test(path)));
    const usedRelationshipIds = new Set(localAll(relationships, 'Relationship').map(node => node.getAttribute('Id') || ''));
    let worksheetNumber = 1;
    let sheetId = Math.max(0, ...localAll(workbook, 'sheet').map(node => Number(node.getAttribute('sheetId') || 0)));

    for (const sheet of pending) {
      const allocation = nextWorksheetPath(zip, usedPaths, worksheetNumber);
      const path = allocation.path;
      worksheetNumber = allocation.next;
      usedPaths.add(path);
      sheetId++;

      let relationshipId = `rIdInkDeskSheet${sheetId}`;
      let suffix = 1;
      while (usedRelationshipIds.has(relationshipId)) relationshipId = `rIdInkDeskSheet${sheetId}_${suffix++}`;
      usedRelationshipIds.add(relationshipId);

      const sheetNode = workbook.createElementNS(MAIN_NS, 'sheet');
      sheetNode.setAttribute('name', String(sheet.name || `Sheet${sheetId}`));
      sheetNode.setAttribute('sheetId', String(sheetId));
      if (sheet.state && sheet.state !== 'visible') sheetNode.setAttribute('state', sheet.state);
      sheetNode.setAttributeNS(REL_NS, 'r:id', relationshipId);
      sheetsNode.appendChild(sheetNode);

      const relationship = relationships.createElementNS(PACKAGE_REL_NS, 'Relationship');
      relationship.setAttribute('Id', relationshipId);
      relationship.setAttribute('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet');
      relationship.setAttribute('Target', path.replace(/^xl\//, ''));
      relationships.documentElement.appendChild(relationship);

      const partName = '/' + path;
      const hasOverride = localAll(contentTypes, 'Override').some(node => node.getAttribute('PartName') === partName);
      if (!hasOverride) {
        const override = contentTypes.createElementNS(contentTypes.documentElement.namespaceURI, 'Override');
        override.setAttribute('PartName', partName);
        override.setAttribute('ContentType', 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml');
        contentTypes.documentElement.appendChild(override);
      }

      sheet.path = path;
      sheet.xml = '';
      zip.file(path, serializeSheet(sheet), { createFolders: false });
    }

    const view = localOne(workbook, 'workbookView');
    if (view) {
      const active = Math.max(0, Math.min(Number(book.active || 0), Math.max(0, (book.sheets || []).length - 1)));
      view.setAttribute('activeTab', String(active));
    }
    zip.file('xl/workbook.xml', serialize(workbook), { createFolders: false });
    zip.file('xl/_rels/workbook.xml.rels', serialize(relationships), { createFolders: false });
    zip.file('[Content_Types].xml', serialize(contentTypes), { createFolders: false });
    return true;
  }

  global.InkDeskSpreadsheetWorksheetPackage = Object.freeze({ appendNewSheets });
})(typeof window !== 'undefined' ? window : globalThis);

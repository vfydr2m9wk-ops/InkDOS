(function (global) {
  'use strict';

  const MAIN_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main';
  const REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships';
  const PACKAGE_REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships';

  function parseXml(text, context) {
    if (global.InkDOSRuntime) return global.InkDOSRuntime.parseXml(text, context);
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

  function normalizeWorkbookTarget(target) {
    let value = String(target || '').replace(/\\/g, '/');
    if (!value) return '';
    if (value.startsWith('/')) value = value.slice(1);
    if (value.startsWith('./')) value = value.slice(2);
    if (!value.startsWith('xl/')) value = 'xl/' + value.replace(/^\.\.\//, '');
    return value;
  }

  function worksheetRelsPath(path) {
    const parts = String(path || '').split('/');
    const file = parts.pop();
    return parts.concat('_rels', `${file}.rels`).join('/');
  }

  function ownerPartFromRelsPath(path) {
    const value = String(path || '').replace(/\\/g, '/');
    if (value === '_rels/.rels') return '';
    const marker = '/_rels/';
    const at = value.lastIndexOf(marker);
    if (at < 0 || !value.endsWith('.rels')) return '';
    return value.slice(0, at + 1) + value.slice(at + marker.length, -5);
  }

  function normalizePartTarget(ownerPath, target) {
    let value = String(target || '').replace(/\\/g, '/');
    if (!value) return '';
    if (value.startsWith('/')) return value.slice(1);
    const base = String(ownerPath || '').split('/');
    if (base.length) base.pop();
    const out = [];
    for (const part of base.concat(value.split('/'))) {
      if (!part || part === '.') continue;
      if (part === '..') out.pop();
      else out.push(part);
    }
    return out.join('/');
  }

  async function relationshipTargets(zip, relsPath) {
    const raw = await zip.file(relsPath)?.async('text');
    if (!raw) return [];
    const document = parseXml(raw, relsPath);
    const owner = ownerPartFromRelsPath(relsPath);
    const targets = [];
    for (const relationship of localAll(document, 'Relationship')) {
      if ((relationship.getAttribute('TargetMode') || '').toLowerCase() === 'external') continue;
      const target = normalizePartTarget(owner, relationship.getAttribute('Target') || '');
      if (target) targets.push(target);
    }
    return targets;
  }

  async function incomingReferenceCounts(zip) {
    const counts = new Map();
    const relsPaths = Object.keys(zip.files).filter(path => path.endsWith('.rels') && zip.file(path));
    for (const relsPath of relsPaths) {
      for (const target of await relationshipTargets(zip, relsPath)) {
        counts.set(target, (counts.get(target) || 0) + 1);
      }
    }
    return counts;
  }

  async function removeOrphanedDependencies(zip, initialTargets, contentTypes) {
    const queue = [...new Set(initialTargets)].filter(Boolean);
    const removed = new Set();
    while (queue.length) {
      const part = queue.shift();
      if (!part || removed.has(part) || !zip.file(part)) continue;
      const incoming = await incomingReferenceCounts(zip);
      if ((incoming.get(part) || 0) > 0) continue;
      const relsPath = worksheetRelsPath(part);
      const children = await relationshipTargets(zip, relsPath);
      zip.remove(part);
      zip.remove(relsPath);
      removeContentTypeOverride(contentTypes, '/' + part);
      removed.add(part);
      for (const child of children) if (!removed.has(child)) queue.push(child);
    }
    return removed;
  }

  function removeContentTypeOverride(contentTypes, partName) {
    for (const node of localAll(contentTypes, 'Override')) {
      if (node.getAttribute('PartName') === partName) node.parentNode.removeChild(node);
    }
  }

  async function removeDeletedSheets(zip, book) {
    const workbookRaw = await zip.file('xl/workbook.xml')?.async('text');
    const relationshipsRaw = await zip.file('xl/_rels/workbook.xml.rels')?.async('text');
    const contentTypesRaw = await zip.file('[Content_Types].xml')?.async('text');
    if (!workbookRaw || !relationshipsRaw || !contentTypesRaw) return false;

    const workbook = parseXml(workbookRaw, 'xl/workbook.xml');
    const relationships = parseXml(relationshipsRaw, 'xl/_rels/workbook.xml.rels');
    const contentTypes = parseXml(contentTypesRaw, '[Content_Types].xml');
    const sheetsNode = localOne(workbook, 'sheets');
    if (!sheetsNode) return false;

    const keptPaths = new Set((book.sheets || []).map(sheet => String(sheet.path || '')).filter(Boolean));
    const relationshipById = new Map(localAll(relationships, 'Relationship').map(node => [node.getAttribute('Id') || '', node]));
    const originalSheets = localAll(sheetsNode, 'sheet');
    const deletedIndices = [];
    const deletedDependencyTargets = [];
    let changed = false;

    for (const [index, sheetNode] of originalSheets.entries()) {
      const relationshipId = sheetNode.getAttributeNS(REL_NS, 'id') || sheetNode.getAttribute('r:id') || '';
      const relationship = relationshipById.get(relationshipId);
      const path = normalizeWorkbookTarget(relationship?.getAttribute('Target') || '');
      if (!path || keptPaths.has(path)) continue;
      const relsPath = worksheetRelsPath(path);
      deletedDependencyTargets.push(...await relationshipTargets(zip, relsPath));
      deletedIndices.push(index);
      sheetNode.parentNode.removeChild(sheetNode);
      if (relationship?.parentNode) relationship.parentNode.removeChild(relationship);
      zip.remove(path);
      zip.remove(relsPath);
      removeContentTypeOverride(contentTypes, '/' + path);
      changed = true;
    }

    if (!changed) return false;

    for (const definedName of localAll(workbook, 'definedName')) {
      if (!definedName.hasAttribute('localSheetId')) continue;
      const oldIndex = Number(definedName.getAttribute('localSheetId'));
      if (!Number.isInteger(oldIndex)) continue;
      if (deletedIndices.includes(oldIndex)) {
        definedName.parentNode.removeChild(definedName);
        continue;
      }
      const shift = deletedIndices.filter(index => index < oldIndex).length;
      definedName.setAttribute('localSheetId', String(Math.max(0, oldIndex - shift)));
    }

    for (const relationship of [...localAll(relationships, 'Relationship')]) {
      if (!/\/calcChain$/i.test(relationship.getAttribute('Type') || '')) continue;
      const target = normalizeWorkbookTarget(relationship.getAttribute('Target') || 'calcChain.xml');
      zip.remove(target);
      if (relationship.parentNode) relationship.parentNode.removeChild(relationship);
      removeContentTypeOverride(contentTypes, '/' + target);
    }

    await removeOrphanedDependencies(zip, deletedDependencyTargets, contentTypes);

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

      let relationshipId = `rIdInkDOSSheet${sheetId}`;
      let suffix = 1;
      while (usedRelationshipIds.has(relationshipId)) relationshipId = `rIdInkDOSSheet${sheetId}_${suffix++}`;
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

  async function syncSheets(zip, book, options) {
    const removed = await removeDeletedSheets(zip, book);
    const added = await appendNewSheets(zip, book, options);
    return removed || added;
  }

  global.InkDOSSpreadsheetWorksheetPackage = Object.freeze({ appendNewSheets, removeDeletedSheets, syncSheets });
})(typeof window !== 'undefined' ? window : globalThis);

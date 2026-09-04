(function (global) {
  'use strict';

  function escapeRegex(value) {
    return String(value || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function isError(value) {
    return typeof value === 'string' && /^#[A-Z0-9/?!.]+$/i.test(value.trim());
  }

  function parseRef(token, currentSheet, sheets) {
    const raw = String(token || '').trim();
    const match = /^(?:(?:'((?:[^']|'')+)'|([^'!]+))!)?\$?([A-Z]{1,3})\$?(\d+)$/i.exec(raw);
    if (!match) return null;
    const explicit = Boolean(match[1] || match[2]);
    const sheetName = (match[1] ? match[1].replace(/''/g, "'") : match[2]) || currentSheet.name;
    const target = (sheets || []).find(sheet => sheet.name === sheetName);
    if (explicit && !target) return { error: '#REF!', sheet: null, ref: match[3].toUpperCase() + match[4] };
    return { sheet: target || currentSheet, ref: match[3].toUpperCase() + match[4] };
  }

  function parseRange(token, currentSheet, sheets, decodeRange) {
    const raw = String(token || '').trim();
    const match = /^(?:(?:'((?:[^']|'')+)'|([^'!]+))!)?\$?([A-Z]{1,3})\$?(\d+):\$?([A-Z]{1,3})\$?(\d+)$/i.exec(raw);
    if (!match) return null;
    const explicit = Boolean(match[1] || match[2]);
    const sheetName = (match[1] ? match[1].replace(/''/g, "'") : match[2]) || currentSheet.name;
    const target = (sheets || []).find(sheet => sheet.name === sheetName);
    if (explicit && !target) return { error: '#REF!', sheet: null, range: null };
    return { sheet: target || currentSheet, range: decodeRange(`${match[3]}${match[4]}:${match[5]}${match[6]}`) };
  }

  function rewriteCodeSegments(formula, rewrite) {
    const text = String(formula || '');
    const stringLiteral = /"(?:[^"]|"")*"/g;
    let output = '';
    let cursor = 0;
    let match;
    while ((match = stringLiteral.exec(text))) {
      output += rewrite(text.slice(cursor, match.index)) + match[0];
      cursor = match.index + match[0].length;
    }
    return output + rewrite(text.slice(cursor));
  }

  function invalidateDeletedReferences(sheets, sheetName) {
    const name = String(sheetName || '');
    if (!name) return 0;
    const quoted = `'${name.replace(/'/g, "''")}'`;
    const reference = "\\$?[A-Z]{1,3}\\$?\\d+(?::\\$?[A-Z]{1,3}\\$?\\d+)?";
    const quotedPattern = new RegExp(`${escapeRegex(quoted)}!${reference}`, 'gi');
    const simplePattern = /^[A-Za-z_][A-Za-z0-9_.]*$/.test(name)
      ? new RegExp(`(^|[^A-Za-z0-9_.\]])${escapeRegex(name)}!${reference}`, 'gi')
      : null;
    let changed = 0;
    const rewrite = segment => {
      let next = segment.replace(quotedPattern, () => {
        changed++;
        return '#REF!';
      });
      if (simplePattern) {
        next = next.replace(simplePattern, (match, prefix) => {
          changed++;
          return prefix + '#REF!';
        });
      }
      return next;
    };
    for (const worksheet of sheets || []) {
      for (const cell of worksheet.cells.values()) {
        if (!cell?.f) continue;
        const next = rewriteCodeSegments(cell.f, rewrite);
        if (next !== cell.f) cell.f = next;
      }
    }
    return changed;
  }

  global.InkDOSSpreadsheetFormulaIntegrity = Object.freeze({
    invalidateDeletedReferences,
    isError,
    parseRange,
    parseRef,
  });
})(typeof window !== 'undefined' ? window : globalThis);

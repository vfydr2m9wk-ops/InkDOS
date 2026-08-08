(function (global, factory) {
  'use strict';

  const api = factory();
  global.InkDeskSpreadsheetFormulaModel = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const VERSION = '0.20.2.25';
  const MAX_SUGGESTIONS = 4;

  const FUNCTIONS = Object.freeze([
    ['SUM', 'SUM(number1, [number2], …)', 'Adds numbers and ranges'],
    ['AVERAGE', 'AVERAGE(number1, …)', 'Returns the arithmetic mean'],
    ['COUNT', 'COUNT(value1, …)', 'Counts numeric values'],
    ['COUNTA', 'COUNTA(value1, …)', 'Counts non-empty values'],
    ['MIN', 'MIN(number1, …)', 'Returns the smallest value'],
    ['MAX', 'MAX(number1, …)', 'Returns the largest value'],
    ['MEDIAN', 'MEDIAN(number1, …)', 'Returns the median'],
    ['PRODUCT', 'PRODUCT(number1, …)', 'Multiplies values'],
    ['ABS', 'ABS(number)', 'Returns absolute value'],
    ['ROUND', 'ROUND(number, digits)', 'Rounds a number'],
    ['ROUNDUP', 'ROUNDUP(number, digits)', 'Rounds away from zero'],
    ['ROUNDDOWN', 'ROUNDDOWN(number, digits)', 'Rounds toward zero'],
    ['MOD', 'MOD(number, divisor)', 'Returns the remainder'],
    ['POWER', 'POWER(number, power)', 'Raises to a power'],
    ['IF', 'IF(test, true, false)', 'Conditional result'],
    ['IFERROR', 'IFERROR(value, fallback)', 'Handles formula errors'],
    ['AND', 'AND(logical1, …)', 'TRUE when all are true'],
    ['OR', 'OR(logical1, …)', 'TRUE when any is true'],
    ['NOT', 'NOT(logical)', 'Reverses a logical value'],
    ['XLOOKUP', 'XLOOKUP(value, lookup, return, [missing])', 'Looks up a value'],
    ['FILTER', 'FILTER(array, include, [empty])', 'Filters a range'],
    ['CONCAT', 'CONCAT(text1, …)', 'Joins text'],
    ['LEFT', 'LEFT(text, [count])', 'Takes left characters'],
    ['RIGHT', 'RIGHT(text, [count])', 'Takes right characters'],
    ['MID', 'MID(text, start, count)', 'Takes middle characters'],
    ['LEN', 'LEN(text)', 'Counts characters'],
    ['TRIM', 'TRIM(text)', 'Normalizes spaces'],
    ['UPPER', 'UPPER(text)', 'Uppercase text'],
    ['LOWER', 'LOWER(text)', 'Lowercase text'],
    ['TODAY', 'TODAY()', 'Current local date'],
    ['NOW', 'NOW()', 'Current date and time'],
    ['DAY', 'DAY(date)', 'Day of month'],
    ['MONTH', 'MONTH(date)', 'Month number'],
    ['YEAR', 'YEAR(date)', 'Year number']
  ]);

  function clamp(value, minimum, maximum) {
    return Math.max(
      Number(minimum) || 0,
      Math.min(Number(maximum) || 0, Number(value) || 0)
    );
  }

  function encodeColumn(index) {
    let value = Math.max(0, Number(index) || 0) + 1;
    let result = '';
    while (value > 0) {
      const remainder = (value - 1) % 26;
      result = String.fromCharCode(65 + remainder) + result;
      value = Math.floor((value - 1) / 26);
    }
    return result;
  }

  function cellReference(cell) {
    if (!cell || !cell.dataset) return '';
    const row = Number(cell.dataset.r);
    const column = Number(cell.dataset.c);
    if (!Number.isFinite(row) || !Number.isFinite(column)) return '';
    return encodeColumn(column) + (row + 1);
  }

  function parenthesisDepth(value) {
    let depth = 0;
    let quoted = false;
    const source = String(value || '');
    for (let index = 0; index < source.length; index += 1) {
      const character = source[index];
      if (character === '"') {
        if (quoted && source[index + 1] === '"') index += 1;
        else quoted = !quoted;
        continue;
      }
      if (quoted) continue;
      if (character === '(') depth += 1;
      if (character === ')') depth = Math.max(0, depth - 1);
    }
    return depth;
  }

  function balanceFormula(value) {
    const source = String(value || '');
    if (!source.startsWith('=')) return source;
    const missing = parenthesisDepth(source);
    return missing > 0 ? source + ')'.repeat(missing) : source;
  }

  function suggestionContext(value, cursor) {
    const source = String(value || '');
    if (!source.startsWith('=')) return null;
    const position = clamp(
      Number.isFinite(Number(cursor)) ? Number(cursor) : source.length,
      1,
      source.length
    );
    const before = source.slice(0, position);
    const match = before.match(/([A-Z][A-Z0-9.]*)$/i);
    if (!match || match[1].length < 2) return null;
    const query = match[1].toUpperCase();
    const start = position - match[1].length;
    const previous = source[start - 1] || '';
    const validBoundary = start === 1 || /[=,+\-*/^&<>]/.test(previous) || previous === '(';
    if (!validBoundary) return null;
    return Object.freeze({
      query,
      start,
      end: position,
      depth: parenthesisDepth(source.slice(0, start)),
      root: start === 1
    });
  }

  function matchingFunctions(context) {
    if (!context) return [];
    return FUNCTIONS.filter(function (item) {
      return item[0].startsWith(context.query);
    }).slice(0, MAX_SUGGESTIONS);
  }

  function applyFunctionSuggestion(value, start, end, functionName) {
    const source = String(value || '');
    const from = clamp(start, 0, source.length);
    const to = clamp(end, from, source.length);
    const insertion = String(functionName || '').toUpperCase() + '(';
    return Object.freeze({
      value: source.slice(0, from) + insertion + source.slice(to),
      caret: from + insertion.length
    });
  }

  function formulaCanSelectReference(value, cursor) {
    const source = String(value || '');
    if (!source.startsWith('=')) return false;
    const position = clamp(cursor, 1, source.length);
    if (suggestionContext(source, position)) return false;
    const before = source.slice(0, position).trimEnd();
    if (!before || before === '=') return false;
    if (/[=(,+\-*/^%]$/.test(before)) return true;
    return (
      parenthesisDepth(before) > 0 &&
      /(?:\$?[A-Z]{1,3}\$?\d+|\d+(?:\.\d+)?|\)|%)$/i.test(before)
    );
  }

  function shouldAppendReference(value, cursor) {
    const source = String(value || '');
    const position = clamp(cursor, 0, source.length);
    const before = source.slice(0, position).trimEnd();
    return (
      parenthesisDepth(before) > 0 &&
      /(?:\$?[A-Z]{1,3}\$?\d+|\d+(?:\.\d+)?|\)|%)$/i.test(before)
    );
  }

  function formulaIsComplete(value) {
    const source = String(value || '').trim();
    return (
      source.startsWith('=') &&
      source.length > 1 &&
      parenthesisDepth(source) === 0 &&
      !/[=(,+\-*/^]$/.test(source)
    );
  }

  return Object.freeze({
    version: VERSION,
    maxSuggestions: MAX_SUGGESTIONS,
    functions: FUNCTIONS,
    clamp,
    encodeColumn,
    cellReference,
    parenthesisDepth,
    balanceFormula,
    suggestionContext,
    matchingFunctions,
    applyFunctionSuggestion,
    formulaCanSelectReference,
    shouldAppendReference,
    formulaIsComplete
  });
});

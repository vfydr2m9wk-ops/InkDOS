/**
 * Presentations Compatibility Engine Foundation
 * Public, dependency-free helpers loaded before app.js.
 * The runtime remains classic-script compatible so it can run from file:// in WebKit.
 */
(function (global) {
  'use strict';

  const FONT_FALLBACKS = {
    'Aptos Display': ['Aptos Display', 'Aptos', 'Arial'],
    'Aptos': ['Aptos', 'Arial'],
    'Calibri Light': ['Calibri Light', 'Calibri', 'Arial'],
    'Calibri': ['Calibri', 'Arial'],
    'Arial Narrow': ['Arial Narrow', 'Arial'],
    'Helvetica Neue': ['Helvetica Neue', 'Helvetica', 'Arial'],
    'Times New Roman': ['Times New Roman', 'Times'],
    'Cambria': ['Cambria', 'Times New Roman', 'Times'],
    'Georgia': ['Georgia', 'Times New Roman', 'Times'],
    'Tahoma': ['Tahoma', 'Arial'],
    'Trebuchet MS': ['Trebuchet MS', 'Arial'],
    'Verdana': ['Verdana', 'Arial'],
    'Perpetua': ['Perpetua', 'Times New Roman', 'Georgia', 'Times'],
    'Franklin Gothic Book': ['Franklin Gothic Book', 'Arial', 'Helvetica'],
    'Wingdings 2': ['Arial', 'Helvetica']
  };

  function normalizeFontName(value) {
    return String(value || 'Arial').replace(/^[\'\"]|[\'\"]$/g, '').trim();
  }

  function isFontAvailable(name) {
    try {
      return Boolean(document.fonts && document.fonts.check('16px "' + String(name).replace(/"/g, '') + '"'));
    } catch (_) {
      return false;
    }
  }

  function resolveThemeAlias(name, theme) {
    const aliases = {
      '+mj-lt': theme && theme.fonts && theme.fonts.majorLatin,
      '+mn-lt': theme && theme.fonts && theme.fonts.minorLatin,
      '+mj-ea': theme && theme.fonts && theme.fonts.majorEastAsia,
      '+mn-ea': theme && theme.fonts && theme.fonts.minorEastAsia,
      '+mj-cs': theme && theme.fonts && theme.fonts.majorComplex,
      '+mn-cs': theme && theme.fonts && theme.fonts.minorComplex
    };
    return aliases[name] || name;
  }

  function safeFont(value, theme) {
    const requested = resolveThemeAlias(normalizeFontName(value), theme) || 'Arial';
    const candidates = FONT_FALLBACKS[requested] || [requested, 'Arial'];
    const available = candidates.find(isFontAvailable);
    const ordered = available ? [available].concat(candidates.filter(function (item) { return item !== available; })) : candidates;
    return ordered.map(function (item) { return '"' + String(item).replace(/"/g, '') + '"'; }).join(', ') + ', sans-serif';
  }

  function schemeColor(name, theme, fallback) {
    if (!name || !theme || !theme.colors) return fallback;
    return theme.colors[name] || fallback;
  }

  global.LocalPresentationsCompatibility = Object.freeze({
    version: '0.5.0-pptx-preservation',
    normalizeFontName: normalizeFontName,
    safeFont: safeFont,
    schemeColor: schemeColor,
    fontFallbacks: FONT_FALLBACKS
  });
}(window));

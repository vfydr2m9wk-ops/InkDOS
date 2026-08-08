# InkDesk v0.20.2.22 — Spreadsheet Formula Draft Safety Hardening

## Scope

This release hardens the boundary between Spreadsheet formula drafts and workbook lifecycle operations. It does not add formula features or change the visual layout.

## Stability changes

- Pending formula drafts now count as unsaved work for New, Open and before-unload protection.
- Save refuses to serialize an XLSX copy while a pending draft would otherwise be omitted from the workbook model.
- Confirmed workbook replacement clears the formula draft session so stale drafts cannot leak into another workbook.
- Failed XLS/XLSX parsing remains transactional: the current workbook and its formula draft are kept until the replacement parses successfully.
- `formula-session.js` gains deterministic `hasDrafts()` and `reset()` operations, coordinated through the new DOM-free `formula-safety.js` module.

## Validation

The release adds a dedicated formula-safety unit suite and extends the existing Spreadsheet Chromium consistency regression. The hosted full profile remains authoritative for the complete Python suite, all 17 browser regression scripts and checksum verification.

# Validation — 0.19.3-beta.6

Date: 2026-08-05

## Automated evidence

- 15 repository unit tests passed.
- Repository structure and local-reference validation passed after manifest generation.
- Privacy and metadata audit passed.
- JavaScript syntax checks passed for PDF, spreadsheet and service-worker code.
- Edge/Chromium opened the synthetic three-page PDF with PDF.js 4.10.38, rendered 30 selectable text spans, resolved three outline items and reported no page errors.
- Edge/Chromium opened the synthetic 4,000-page PDF, jumped from page 1 to page 3,500 and retained five full page canvases plus 25 thumbnail canvases.
- Spreadsheet automation displayed formula suggestions, inserted `SUM(` by keyboard and selected a 3×3 range by pointer drag without page errors.

## Scope limits

Physical Safari/iPadOS, Firefox, installed PWA cache upgrades and embedded-host worker policies were not available and remain manual checks. No private reference document was copied into this validation record or package.

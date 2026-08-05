# Known Limitations — 0.19.3-beta.7

## General

- InkDesk is beta software and does not provide complete Microsoft Office or Microsoft Edge fidelity.
- Large ZIP/XML/BIFF8 files can cause memory pressure. Image-heavy PDFs can still exceed browser canvas or worker limits, especially on tablet-class devices, despite the five-page render window.
- Password-protected/encrypted Office files, ZIP64 packages, macros and embedded active applications are unsupported.
- Native Safari, physical iPadOS, Firefox, installed-PWA updates and embedded hosts still require manual validation for this build.

## Documents

- Pagination can vary when fonts are substituted.
- Fields, comments, equations, tracked changes, text boxes and complex DrawingML are partial.
- Leading XML BOMs and NFC path differences are normalized, but unusual section inheritance and non-standard package naming still need more fixtures.

## Spreadsheets

- BIFF8 `.xls` is import-only and exports as XLSX.
- Unsupported formulas use cached workbook values when available and are not recalculated.
- External links, data connections, Power Query, pivots, VBA/ActiveX/OLE and advanced chart fidelity are unsupported or partial.
- Text overflow follows empty-cell rules in page view, but unusual merged/formatted regions may still differ from Excel.

## Presentations

- SmartArt, embedded media/OLE, complex groups, advanced animation/transitions and exact PowerPoint text autofit are partial.
- Imported direct and inherited backgrounds are resolved, but unusual theme effects can still differ.
- Package-preserving export cannot safely reproduce every structural slide edit.

## PDF Workspace

- PDF rendering is provided by bundled classic PDF.js 3.11.174. Browser canvas, worker and memory limits still vary, especially on tablet-class devices and image-heavy scans.
- The Pages panel keeps lightweight entries for every page but creates raster thumbnails only near the current page. At most five full page canvases are retained.
- Scanned image-only PDFs have no selectable text until OCR is performed.
- Dynamic XFA, digital signatures and uncommon annotation types can be displayed or saved only to the extent supported by PDF.js.
- Highlight, underline and marker tools create region-based InkDesk review overlays. They are not character-anchored PDF annotations.
- InkDesk comments, inserted text, marks and personal bookmarks are stored by PDF fingerprint and exported as review JSON. They are not falsely presented as embedded PDF annotations.
- **Save PDF copy** serializes changes supported by PDF.js annotation storage; unsupported documents must use review JSON. PDF signing, OCR, redaction, page reordering and conversion are not implemented.
- Automated validation includes a synthetic 4,000-page PDF in Chromium; physical iPadOS/WebKit performance and memory behavior still require manual validation.

## PWA and hosts

- The service worker caches same-origin application assets, not user documents.
- Direct `file://` behavior varies and has no service worker.

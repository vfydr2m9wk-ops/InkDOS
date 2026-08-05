# PDF component — 0.19.3-beta.7

The PDF workspace uses the bundled classic PDF.js 3.11.174 display library and worker. The classic distribution is required for direct `file://` startup in Edge/Chromium, where ES-module scripts are blocked by the local opaque origin. It does not use `object`, `embed`, `iframe`, a CDN or a remote conversion service.

Each active page contains a canvas layer, selectable PDF.js text layer, PDF.js annotation/form layer and an InkDesk review layer. The review layer stores normalized coordinates plus the page number; zoom and layout changes rebuild the visual layer from those document-relative values.

Navigation from the page field, buttons, thumbnails and outline calls `navigateToPage`. An intersection observer updates the active page during continuous scrolling. Horizontal mode changes the same page sequence to a row; it is not a detached native-viewer setting.

For long files, every page receives only a lightweight placeholder. The active page and two neighbors on either side are rendered. Leaving that window cancels pending work, calls page cleanup and resets canvas width and height to release graphics memory. Thumbnails render lazily near the current page. Canvas pixels are capped to prevent extreme zoom and high-density screens from allocating unbounded surfaces.

AcroForm controls are rendered through PDF.js annotation storage. `saveDocument()` is exposed as “Save PDF copy” and can persist only features supported by PDF.js for that document. InkDesk overlay reviews remain a separate `inkdesk-pdf-review/2` JSON export. This distinction is intentional and visible in the toolbar.

PDFs made only from scanned images have no selectable text until OCR is performed. Dynamic XFA, signatures and arbitrary third-party annotation types may not be writable.

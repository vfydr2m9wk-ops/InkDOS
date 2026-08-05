# Upgrade notes — 0.19.3-beta.7

Delete or replace the complete beta.6 folder before extracting beta.7. A partial copy may retain the old `.mjs` PDF.js files or a beta.6 service-worker cache and reproduce the inactive PDF button.

The beta.7 PDF runtime uses `shared/vendor/pdfjs/pdf.min.js` and `pdf.worker.min.js`. It is intentionally a classic-script build so the downloaded package works when `index.html` is opened directly through `file://` in Edge/Chromium.

If a browser has previously installed InkDesk as a PWA, close all InkDesk tabs and reopen the new package so the `inkdesk-shell-v0.19.3-beta.7` cache can replace the older shell.

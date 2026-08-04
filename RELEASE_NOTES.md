# InkDesk 0.19.0-beta — Structural Cleanup and Integrity Review

This release is a focused reliability and maintainability update. It does not redesign the interface or replace local behavior with cloud services.

The most important fixes protect active documents during failed opens, preserve zero-valued spreadsheet formulas, repair DOCX rename/export behavior, add presentation text Undo/Redo, prevent stale spreadsheet downloads, and add defensive limits for untrusted ZIP/XML Office packages.

Runtime dependencies remain fully bundled. Exact existing copies of JSZip and pako were consolidated into `shared/vendor/` with their notices. A standard web manifest and same-origin service worker now support hosted installation/offline caching where the browser permits it; direct installation and offline reload were not executed in the review environment because its Chromium policy blocked both local files and localhost navigation.

The automated suite now includes 43 unit/package tests and eight Chromium browser regressions. Native Firefox, Safari/WebKit, iPadOS, embedded-host, and real installed-PWA validation are not claimed.

**Release classification: Beta quality.** The tested core workflows are materially safer, but broader native-device validation and a privacy-preserving crash-recovery design are still required before a stable 1.0 recommendation.

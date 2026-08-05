# Known Limitations — 0.19.2-beta

## General

- InkDesk is beta software and does not provide complete Microsoft Office fidelity.
- Browser download completion is not observable. A download remains unverified until the exact bytes are reopened and fingerprinted.
- Active documents/history are memory-only; crash/session recovery is not implemented.
- Package/XML validation currently runs on the main thread. Files near configured limits can still create memory or responsiveness pressure, especially on iPad-class devices.
- Heavy ZIP/XML/BIFF8/model construction has not yet been moved to Web Workers; cancellation and adaptive complexity limits remain future hardening work.
- Password-protected/encrypted files, ZIP64 packages, nested archives, and packages beyond conservative limits are rejected.
- Native Safari, physical iPadOS, installed PWA behavior, embedded hosts, and large-file pressure were not tested in the local review environment.

## Documents

- Pagination is approximate and font substitution can alter layout.
- Fields, comments, equations, embedded Office objects, tracked-change semantics, and complex DrawingML are partial.
- Unsafe/unknown active content is removed or flattened to inert text; this can reduce fidelity.
- Legacy `.doc` is unsupported.

## Spreadsheets

- BIFF8 `.xls` is import-only and exports as XLSX.
- Formula recalculation is deliberately limited. Unsupported formulas retain their OOXML formula and cached value when available, but are not recalculated.
- External links, data connections, Power Query, pivots, VBA/ActiveX/OLE, and advanced chart fidelity are unsupported or partial.
- Recalculation has formula length, token, nesting, step, reference, recursion, cycle, pass, and total-evaluation limits.

## Presentations

- Imported package-preserving export requires the original slide order/set. Structural slide changes that cannot be patched safely are blocked.
- SmartArt, embedded media/OLE, complex groups, advanced animations/transitions, charts, themes, and exact text layout are partial.
- New-presentation notes graph creation is not supported.
- The workspace remains architecturally large and needs further separation.

## PWA and hosts

- The service worker caches same-origin application assets, not documents.
- Cache manifest structure is tested; actual installed-PWA update/offline behavior remains browser/device validation.
- Direct `file://` behavior varies and has no service worker.

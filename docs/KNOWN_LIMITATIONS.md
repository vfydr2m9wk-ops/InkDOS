# Known Limitations

## General

- InkDesk does not aim for Microsoft Office feature parity or pixel-identical rendering.
- Saving normally creates a new download rather than silently overwriting the selected source file.
- Browser/host policies control file selection, downloads, fullscreen, service workers and installation.
- Fonts can be substituted and change pagination or slide geometry.
- Private IndexedDB recovery exists for the supported editing workspaces, but it is not a substitute for external backups or verified exported copies.
- Compressed Office inputs are subject to conservative size, entry-count, expansion, path-safety, encryption, ZIP64 and compression-ratio limits.
- Password-protected and encrypted Office files are unsupported.
- The generic Launcher file handoff was intentionally removed; choose a workspace first and use its Open control.
- Native Safari/WebKit, iPadOS and installed-PWA behavior still require physical-device validation for the 1.0 beta.

## Documents

- Fields, comments, equations, embedded Office objects, tracked-change semantics and complex DrawingML layouts are not fully editable.
- Pagination is approximate and can vary with font availability.
- New documents use a compact generated DOCX package rather than a full Word template.
- Legacy `.doc` is unsupported.

## Spreadsheets

- BIFF8 `.xls` is import-only and is exported as `.xlsx`.
- VBA, ActiveX, unusual legacy records, advanced charts and embedded OLE objects are unsupported or best effort.
- BIFF formula token streams are not reconstructed; cached displayed results may be imported as values where necessary.
- Formula evaluation is intentionally limited to InkDesk's supported deterministic grammar/functions and is not a complete Excel calculation engine.
- External links, data connections, Power Query, pivots and broad dynamic-array compatibility are incomplete.

## Presentations

- Preservation-aware PPTX export prioritizes existing package relationships; unsupported structural edits may be restricted rather than silently rebuilding unrelated parts.
- SmartArt, embedded media, OLE objects, advanced animations, complex groups, chart/theme fidelity and exact text layout remain partial.
- Presenter notes are best supported when the imported package already contains the required notes relationships.

## PDF

- InkDesk is a focused PDF viewer/review workspace, not a complete PDF authoring system.
- Complex forms, signatures, advanced editing and exact preservation of every PDF feature are outside the beta contract.

## TXT / EPUB

- TXT is plain-text only.
- DRM-protected and fixed-layout EPUB workflows are outside the supported subset.

## PWA and offline hosting

- The same-origin service worker and app shell are structurally validated.
- Static HTTP(S) is the preferred deployment mode.
- Real installation/offline reload behavior remains browser- and host-dependent and must be checked on the target device.

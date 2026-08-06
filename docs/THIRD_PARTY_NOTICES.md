# Third-Party Notices

InkDesk keeps runtime dependencies local so the editors do not require a CDN or network connection.

| Component | Version | Purpose | Canonical file | License | SHA-256 |
|---|---:|---|---|---|---|
| JSZip | 3.10.1 | Read and write ZIP-based OOXML packages | `shared/vendor/jszip.min.js` | MIT or GPL-3.0, at the user's choice | `acc7e41455a80765b5fd9c7ee1b8078a6d160bbbca455aeae854de65c947d59e` |
| pako inflate | 1.0.11 | Raw DEFLATE support used by the DOCX compatibility parser | `shared/vendor/pako_inflate.min.js` | MIT | `2ca27e9a8dae569cdeac42752ed1aed1afeff7f19282d3cc12c0aaa54a08bc04` |
| PDF.js (`pdfjs-dist`) | 3.11.174 | Local PDF rendering, text layers, forms and worker processing | `shared/vendor/pdfjs/pdf.min.js`, `shared/vendor/pdfjs/pdf.worker.min.js` | Apache-2.0 | Generated during the publication workflow from the pinned npm package |

Full notices are retained in:

- `shared/vendor/LICENSE-JSZIP.txt`
- `shared/vendor/LICENSE-PAKO.txt`

The cleanup consolidated byte-identical workspace copies into one shared copy. No dependency version was changed. Both libraries work offline. JSZip 3.10.1 is newer than the versions affected by the historical prototype-pollution and path-sanitization advisories reviewed for this audit.

## Fonts

No proprietary Microsoft fonts are bundled. Font family names can appear as document metadata, but availability and substitution are controlled by the user's platform.

Contributors must document the source, exact version, license, purpose, and offline behavior of any added dependency or asset. Required attribution must not be removed.
## PDF.js publication bootstrap

The source package records the exact acquisition contract in `VENDOR_SOURCES.json`. The publication workflow downloads `pdfjs-dist@3.11.174` from npm, copies the classic display and worker builds into `shared/vendor/pdfjs/`, preserves the upstream Apache-2.0 license as `LICENSE-PDFJS.txt`, and regenerates repository checksums before strict validation. The published application then uses those local files and does not require a PDF.js CDN at runtime.

InkDesk sets `isEvalSupported: false` when opening PDFs. Version 3.11.174 is retained temporarily for compatibility with the current classic-script PDF workspace; migration to a supported modern PDF.js line is tracked as a v0.20.x hardening task.


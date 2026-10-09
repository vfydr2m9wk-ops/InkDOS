# Third-party notices

InkDOS itself is MIT-licensed (`LICENSE`). It ships pinned copies of these third-party libraries, each kept next to
its license text and provenance file. App-private vendor copies are intentionally not deduplicated.

| Library | License | Where |
| --- | --- | --- |
| [PDF.js](https://github.com/mozilla/pdf.js) 6.4.299 (legacy build, WebAssembly image decoders, modified worker) | Apache-2.0 | `apps/pdf/vendor/pdfjs/` |
| [pdf-lib](https://github.com/Hopding/pdf-lib) | MIT | `apps/pdf/vendor/pdf-lib/`, `apps/spreadsheets/vendor/pdf-lib/` |
| [Tesseract.js](https://github.com/naptha/tesseract.js) and tesseract.js-core, with Tesseract language data | Apache-2.0 | `apps/pdf/vendor/tesseract/`, `licenses/TESSERACT-*.txt` |
| [JSZip](https://github.com/Stuk/jszip) | MIT or GPL-3.0 (used under MIT) | Documents, Spreadsheets, Presentations, PDF; `licenses/JSZIP.txt` |
| [pako](https://github.com/nodeca/pako) | MIT and Zlib | Documents, Spreadsheets, EPUB; `licenses/PAKO.txt` |
| [node-forge](https://github.com/digitalbazaar/forge) | BSD-3-Clause or GPL-2.0 (used under BSD) | `labs/pdf/`; `licenses/NODE-FORGE.txt` |

The Windows app is built with [Tauri](https://tauri.app) (MIT or Apache-2.0).

## Tools opened on request

These run on a separate site (https://inkdos-tools.github.io), not inside
InkDOS. Each is published there with its own license and a link to its source:

- [ONLYOFFICE](https://github.com/ONLYOFFICE) editors via [ranuts/document](https://github.com/ranuts/document): AGPL-3.0. The site's own repository, [inkdos-tools.github.io](https://github.com/inkdos-tools/inkdos-tools.github.io), is AGPL-3.0.
- [BentoPDF](https://github.com/alam00000/bentopdf) and the other tools built by [InkDOS-tools](https://github.com/inkdos-tools/InkDOS-tools), whose README lists each tool with its license.

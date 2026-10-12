# Third-party notices

InkDOS itself is MIT-licensed (`LICENSE`). It ships pinned copies of these third-party libraries, each kept next to
its license text and provenance file. App-private vendor copies are intentionally not deduplicated.

| Library | License | Where |
| --- | --- | --- |
| [PDF.js](https://github.com/mozilla/pdf.js) 6.4.299 (legacy build, WebAssembly image decoders, modified worker) | Apache-2.0 | `apps/pdf/vendor/pdfjs/` |
| [pdf-lib](https://github.com/Hopding/pdf-lib) | MIT | `apps/pdf/vendor/pdf-lib/`, `apps/spreadsheets/vendor/pdf-lib/` |
| [JSZip](https://github.com/Stuk/jszip) | MIT or GPL-3.0 (used under MIT) | Documents, Spreadsheets, Presentations, PDF; `licenses/JSZIP.txt` |
| [pako](https://github.com/nodeca/pako) | MIT and Zlib | Documents, Spreadsheets, EPUB; `licenses/PAKO.txt` |
| [Phosphor Icons](https://github.com/phosphor-icons/core) 2.1.1 (19 regular icons, inlined) | MIT | `apps/pdf/ui/edit-pdf-button.js` (PDF tools tags) |

The Windows app (`desktop/`, not published at present) is built with [Tauri](https://tauri.app) (MIT or Apache-2.0).

## Tools opened on request

These run on a separate engine site, not inside InkDOS. Each is published there with its own license file and a
reference to its source (`UPSTREAM-LICENSE.txt`, `UPSTREAM-SOURCE.txt`):

- [ONLYOFFICE](https://github.com/ONLYOFFICE) editors via [ranuts/document](https://github.com/ranuts/document): AGPL-3.0.
- [BentoPDF](https://github.com/alam00000/bentopdf): AGPL-3.0.
- [Pyodide](https://github.com/pyodide/pyodide) (Python terminal): MPL-2.0.
- The pnk viewer for Apple Pages, Numbers and Keynote (view only).
- Legacy tools group of the Home (`config/frozen-legacy.json`, `legacy-home-tools`): [Squoosh](https://github.com/GoogleChromeLabs/squoosh)
  (Apache-2.0), ArchiveDrop, [CyberChef](https://github.com/gchq/CyberChef) (Apache-2.0) and
  [IT-Tools](https://github.com/CorentinTh/it-tools) (GPL-3.0).

The engine site's own license and source files are authoritative for each of these.

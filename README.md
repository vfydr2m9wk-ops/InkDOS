# InkDOS

**Use it:** https://vfydr2m9wk-ops.github.io/InkDOS/ · **Also on one address (Cloudflare):** https://inkdos-offic.pages.dev · **Past versions:** [legacy branch](https://github.com/vfydr2m9wk-ops/InkDOS/tree/legacy/releases) (no downloads are published for now)

InkDOS is a personal, local-first office hub: one Home that opens documents, spreadsheets, presentations, PDFs, e-books and plain text, entirely in the browser. There is no account, no server and no telemetry. Files are opened from the device and saved back to it.

## Why it exists

I wanted one place to open and edit my files on every device I actually use (an iPad, often inside the XeOS web desktop, iPad Safari, and Chrome on a PC) without installing a full office suite on each one and without uploading documents anywhere. Office suites in the browser usually mean a cloud account; desktop suites mean a large install per device. InkDOS sits in between: a static web app that works offline once loaded.

There is no installable version any more: the Windows app is no longer published, and the web app always has the current version (see [SUPPORT.md](SUPPORT.md)).

It began as a set of editors written for this project. Over time the goal changed: instead of rebuilding what mature open-source projects already do well, InkDOS now gathers them behind one Home and keeps them on the device.

## Where it stands

Every file opens in InkDOS first. The mature open-source tools come in only when you ask, for that file:

| | **Opens in** | **On request** |
| --- | --- | --- |
| Word, Excel, PowerPoint (also DOC, XLS, PPT, OpenDocument) | InkDOS Documents, Spreadsheets, Presentations | **Edit with ONLYOFFICE**: the ONLYOFFICE editors running in the browser ([ranuts/document](https://github.com/ranuts/document)) |
| PDF | InkDOS PDF workspace (forms, highlights, notes, text; verified saves) | **Edit PDF**: the BentoPDF toolkit (split, merge, OCR, convert) |
| EPUB | InkDOS EPUB reader (search, bookmarks, highlights, resume) | |
| Plain text | InkDOS text editor (keeps encoding and line endings, recovers drafts) | |
| Apple Pages, Numbers, Keynote | shown by the pnk viewer, view only | |

- **ONLYOFFICE and BentoPDF** run from a separate engine site, kept apart from InkDOS on purpose so third-party code never runs with InkDOS's own data. On the web they open only on request ("Edit with ONLYOFFICE", "Edit PDF") as a page of their own, with the file as it is on screen; the browser's Back returns to InkDOS.
- The **download button** on Home lists those tools and keeps them on the device (Download all, Check for updates).

Files opened from the system (the browser's file handling, XeOS) go to the matching InkDOS app.

**Offline:** on Safari and Chromium-based browsers, everything is kept on the device after the first use or after Download all. Web views without service workers (XeOS today) load from the internet.

**Supported:** iOS/iPadOS WebKit (Safari, XeOS), and Chromium-based browsers (Chrome, Edge). Firefox is not supported or tested; see [SUPPORT.md](SUPPORT.md) for why.

## Privacy and storage

- No backend and no analytics. Every tool runs in the browser.
- Each site's Content Security Policy only lets it reach its own address.
- No list of recent files is kept: files are found again with the device's own file manager.
- The only thing stored is the InkDOS editors' recovery drafts, kept on the device and encrypted (AES-GCM) with a key that cannot be exported from it.

## Credits

InkDOS stands on the work of these projects:

- [ONLYOFFICE](https://github.com/ONLYOFFICE) via [ranuts/document](https://github.com/ranuts/document)
- [BentoPDF](https://github.com/alam00000/bentopdf) and [PDF.js](https://github.com/mozilla/pdf.js) (the engine of the InkDOS PDF workspace)
- [Pyodide](https://pyodide.org)
- [Tauri](https://tauri.app)
- pdf-lib, JSZip and pako in the InkDOS editors

InkDOS's own code is under the MIT license (`LICENSE`). Each project above keeps its own license; see `docs/THIRD_PARTY_NOTICES.md` and the license files shipped with each tool.

## For contributors

- `index.html`, `assets/`, `service-worker.js` and `manifest.webmanifest`: the Home and offline shell.
- `apps/<workspace>/`: the InkDOS editors.
- `desktop/`: the Windows app (Tauri v2), kept in the repository but no longer published.
- `VERSION.json`: the product version.

The project is maintained with AI-assisted changes and human review: small, component-local changes, regression tests before merging, and protected frozen legacy code. See `AGENTS.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md` and `docs/KNOWN_LIMITATIONS.md`.

Do not commit real user files; use synthetic fixtures only (see `SECURITY.md`). Security issues: report privately as described in `SECURITY.md`.

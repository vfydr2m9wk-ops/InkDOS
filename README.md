# InkDOS

**Use it:** https://vfydr2m9wk-ops.github.io/InkDOS/ · **Tools (ONLYOFFICE, BentoPDF):** https://inkdos-offic.pages.dev · **Windows app:** [latest release](https://github.com/vfydr2m9wk-ops/InkDOS/releases/latest)

InkDOS is a personal, local-first office hub: one Home that opens documents, spreadsheets, presentations, PDFs, e-books and plain text, entirely in the browser or in a small Windows app. There is no account, no server and no telemetry. Files are opened from the device and saved back to it.

## Why it exists

I wanted one place to open and edit my files on every device I actually use (an iPad, often inside the XeOS web desktop, iPad Safari, and a Windows PC) without installing a full office suite on each one and without uploading documents anywhere. Office suites in the browser usually mean a cloud account; desktop suites mean a large install per device. InkDOS sits in between: a static web app that works offline once loaded, and the same thing packaged for Windows.

It began as a set of editors written for this project. Over time the goal changed: instead of rebuilding what mature open-source projects already do well, InkDOS now gathers them behind one Home and keeps them on the device.

## Where it stands

Every file opens in InkDOS first. The mature open-source tools come in only when you ask, for that file:

| | **Opens in** | **On request** |
| --- | --- | --- |
| Word, Excel, PowerPoint (also DOC, XLS, PPT, OpenDocument) | InkDOS Documents, Spreadsheets, Presentations | **Edit with ONLYOFFICE**: the ONLYOFFICE editors running in the browser ([ranuts/document](https://github.com/ranuts/document)) |
| PDF | InkDOS PDF workspace (forms, highlights, notes, text; verified saves) | the BentoPDF toolkit (split, merge, OCR, convert) |
| EPUB | InkDOS EPUB reader (search, bookmarks, highlights, resume) | |
| Plain text | InkDOS text editor (keeps encoding and line endings, recovers drafts) | |
| Apple Pages, Numbers, Keynote | shown by the pnk viewer, view only | |

- **The tools** live on their own site, **https://inkdos-offic.pages.dev**, kept separate from InkDOS on purpose so third-party code never runs with InkDOS's own data. ONLYOFFICE opens over the InkDOS app with "Back to InkDOS"; it gets the file as it was opened.
- That site also has its own Home with an **Offline tools** panel that downloads the editors and tools to the device in one go.

Files opened from the system (Windows "Open with", the browser's file handling, XeOS) go to the matching InkDOS app.

**Offline:** on Safari, Chromium-based browsers and the Windows app, everything is kept on the device after the first use or after Download all. Web views without service workers (XeOS today) load from the internet.

**Why the tools are on Cloudflare Pages:** the editors are large (about 100 MB), and GitHub Pages tells browsers to recheck every file after 10 minutes. In a web view without service workers that keeps its sessions and site data (XeOS on iPad), that meant hundreds of requests and a slow reload on every open. Cloudflare Pages lets the site tell the browser to keep the program files for a long time (up to a year for build files), so once loaded the editors open from the device's own cache. Pages themselves are always rechecked, and **Check for updates** in the Offline tools panel fetches a new version right away. The same site is still published at [inkdos-tools.github.io](https://inkdos-tools.github.io) as a mirror.

**Supported:** iOS/iPadOS WebKit (Safari, XeOS), Chromium-based browsers, and the Windows app (Tauri). Other platforms may work but are not maintained.

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
- pdf-lib, JSZip, pako and Tesseract.js in the InkDOS editors

Each keeps its own license; see `docs/THIRD_PARTY_NOTICES.md` and the license files shipped with each tool.

## For contributors

- `index.html`, `assets/`, `service-worker.js` and `manifest.webmanifest`: the Home and offline shell.
- `apps/<workspace>/`: the InkDOS editors.
- `desktop/`: the Windows app (Tauri v2), its installer and updater.
- `VERSION.json`: the product version.

The project is maintained with AI-assisted changes and human review: small, component-local changes, regression tests before merging, and protected frozen legacy code. See `AGENTS.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md` and `docs/KNOWN_LIMITATIONS.md`.

The full-version tools are built in their own repositories: [InkDOS-tools](https://github.com/inkdos-tools/InkDOS-tools) and [inkdos-tools.github.io](https://github.com/inkdos-tools/inkdos-tools.github.io).

Do not commit real user files; use synthetic fixtures only (see `SECURITY.md`). Security issues: report privately as described in `SECURITY.md`.

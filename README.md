# InkDOS

**Use it:** https://vfydr2m9wk-ops.github.io/InkDOS/ · **Windows app:** [latest release](https://github.com/vfydr2m9wk-ops/InkDOS/releases/latest)

InkDOS is a personal, local-first office hub: one Home that opens documents, spreadsheets, presentations, PDFs, e-books and plain text, entirely in the browser or in a small Windows app. There is no account, no server and no telemetry. Files are opened from the device and saved back to it.

## Why it exists

I wanted one place to open and edit my files on every device I actually use (an iPad, often inside the XeOS web desktop, iPad Safari, and a Windows PC) without installing a full office suite on each one, without uploading documents anywhere, and without a heavy app eating RAM. Office suites in the browser usually mean a cloud account; desktop suites mean a large install per device. InkDOS sits in between: a static web app that works offline once loaded, and the same thing packaged for Windows.

It began as a set of lightweight editors written for this project. Over time the goal changed: instead of rebuilding what mature open-source projects already do well, InkDOS now gathers them behind one Home and keeps them on the device.

## Where it stands

InkDOS has two engines, switched on the Home:

| | **Full version** | **Light version** |
| --- | --- | --- |
| Word, Excel, PowerPoint | ONLYOFFICE editors running in the browser ([ranuts/document](https://github.com/ranuts/document)) | InkDOS's own editors |
| PDF | PDF.js viewer, plus the BentoPDF toolkit (edit, split, merge, sign, OCR, convert) | InkDOS PDF workspace |
| EPUB and e-books | foliate-js (EPUB, MOBI, FB2, CBZ) | InkDOS EPUB reader |
| Plain text | CodeMirror | InkDOS text editor |
| Extras | Python terminal (Pyodide) | none |
| Default on | Windows app | Web (light enough for XeOS on iPad) |

- **Full version:** built from established projects. It lives on its own site, [inkdos-tools.github.io](https://inkdos-tools.github.io), kept separate from InkDOS on purpose so third-party code never runs with InkDOS's own data. Its **Offline tools** panel downloads every tool to the device in one go and shows what is already stored.
- **Light version:** the original InkDOS editors. Smaller and faster, with narrower format support. It stays as the light option and as the fallback.

Files opened from the system (Windows "Open with", or the browser's file handling) go to the matching app of the chosen engine.

**Offline:** on Safari, Chromium-based browsers and the Windows app, everything is kept on the device after the first use or after Download all. Web views without service workers (XeOS today) always load from the internet.

**Supported:** iOS/iPadOS WebKit (Safari, XeOS), Chromium-based browsers, and the Windows app (Tauri). Other platforms may work but are not maintained.

## Privacy and storage

- No backend and no analytics. Every tool runs in the browser.
- Each site's Content Security Policy only lets it reach its own address. The one exception is the optional online Python terminal, which may install packages from PyPI.
- Drafts and recent files stay in the browser's storage on the device.
- InkDOS drafts and the ONLYOFFICE recent-files history are encrypted (AES-GCM) with a key that cannot be exported from the device.

## Credits

InkDOS stands on the work of these projects:

- [ONLYOFFICE](https://github.com/ONLYOFFICE) via [ranuts/document](https://github.com/ranuts/document)
- [BentoPDF](https://github.com/alam00000/bentopdf) and [PDF.js](https://github.com/mozilla/pdf.js)
- [foliate-js](https://github.com/johnfactotum/foliate-js)
- [CodeMirror](https://codemirror.net/5/)
- [Pyodide](https://pyodide.org)
- [Tauri](https://tauri.app)
- pdf-lib, JSZip, pako and Tesseract.js in the Light editors

Each keeps its own license; see `docs/THIRD_PARTY_NOTICES.md` and the license files shipped with each tool.

## For contributors

- `index.html`, `assets/`, `service-worker.js` and `manifest.webmanifest`: the Home and offline shell.
- `apps/<workspace>/`: the Light editors.
- `desktop/`: the Windows app (Tauri v2), its installer and updater.
- `VERSION.json`: the product version.

The project is maintained with AI-assisted changes and human review: small, component-local changes, regression tests before merging, and protected frozen legacy code. See `AGENTS.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md` and `docs/KNOWN_LIMITATIONS.md`.

The full-version tools are built in their own repositories: [InkDOS-tools](https://github.com/inkdos-tools/InkDOS-tools) and [inkdos-tools.github.io](https://github.com/inkdos-tools/inkdos-tools.github.io).

Do not commit real user files; use synthetic fixtures only (see `SECURITY.md`). Security issues: report privately as described in `SECURITY.md`.

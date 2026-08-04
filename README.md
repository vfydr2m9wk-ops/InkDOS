<p align="center">
  <img src="docs/images/readme-banner.png" alt="InkDesk — local-first browser productivity suite" width="100%">
</p>

# InkDesk

> **A lightweight local-first productivity suite.**

InkDesk is an open-source, browser-native suite for focused DOCX, XLS/XLSX, and PPTX workflows. It is distributed as static HTML, CSS, and JavaScript. Documents are parsed and edited in the current browser context; the project does not operate a document-processing backend, account service, telemetry service, or analytics endpoint.

**Project status: Beta (`0.19.1-beta`).** Compatibility is intentionally partial. InkDesk does not claim complete Microsoft Office fidelity, pixel-identical rendering, or safe support for every Office file.

## Workspaces

| Workspace | Formats | Focused behavior |
|---|---|---|
| Documents | DOCX | Common text/layout editing, inert DOCX-derived DOM construction, and package-preserving copy export |
| Spreadsheets | XLS import; XLSX open/export | BIFF8 import, common cells/styles, deterministic limited formula recalculation, and package-preserving XLSX copy export |
| Presentations | PPTX | Common slide editing/presentation mode and preservation-oriented PPTX patch export |

## Opening a file

The main `index.html` includes one **Open document** button. Choose a DOCX, XLS, XLSX, or PPTX file and InkDesk detects the extension and opens the matching workspace. Each workspace includes a house-shaped button that returns to the main InkDesk index.

When served over HTTP(S), the selected file is transferred once through short-lived IndexedDB storage and removed when consumed. When `index.html` is opened directly through `file://`, InkDesk keeps the index alive and transfers the selected `File` object to the matching embedded workspace with a token-scoped `postMessage` bridge. The file is not uploaded. Browser and local-file host policies still vary, so direct local opening requires device testing.

## Export status and data safety

InkDesk exports a **new copy**; it does not overwrite the selected source file. Triggering a browser download is not proof that the operating system wrote the file. After a download request, the workspace reports **“Download requested — not verified”** and keeps unsaved-change protection active. A copy becomes **verified** only when it is reopened and its SHA-256 fingerprint matches the generated export.

Keep the original file, work from backup copies, reopen exported files, and verify important content in an independent compatible application before relying on them for legal, medical, financial, academic, or other critical use.

## Security model

Imported OOXML packages are treated as untrusted ZIP/XML input. Before JSZip processing, InkDesk checks normalized package inventory, duplicate and colliding paths, local/central header consistency, encryption, ZIP64, methods, overlaps, size, entry count, and compression ratio. XML parsing rejects DTD/entity declarations and enforces per-part, aggregate, depth, node, and attribute limits. DOCX-derived editable content is rebuilt through a deny-by-default DOM allowlist. Spreadsheet arithmetic is interpreted by a deterministic parser rather than `eval` or `Function`.

These controls reduce attack surface; they do not replace browser sandboxing, fuzzing, native-device testing, or independent file validation.

## Privacy and offline operation

Runtime dependencies are bundled under `shared/vendor/`. The optional service worker caches only same-origin application assets when served over HTTP(S); it does not cache user documents. `file://` behavior depends on the host and service workers are unavailable there.

## Quick start

```bash
python3 -m http.server 8080
```

Open `http://localhost:8080/`. Compatible local-file or embedded hosts may open `index.html` directly, but static HTTP(S) hosting is more predictable.

## Validation commands

```bash
python3 scripts/verify_checksums.py
python3 scripts/validate_repository.py
python3 scripts/audit_source.py
python3 -m unittest discover -s tests -p "test_*.py"
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group package-security
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group lifecycle
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group isolation-offline
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group documents-presentations
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group spreadsheets
python3 scripts/run_release_validation.py
python3 scripts/build_release.py --output-dir dist
```

CI is configured to run browser regressions separately in Playwright Chromium, Firefox, and WebKit. A Playwright engine run is not native Safari, native Firefox packaging, or physical iPadOS validation.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Compatibility and validation matrix](COMPATIBILITY.md)
- [Security policy](SECURITY.md)
- [Testing](TESTING.md)
- [Manual device checklist](docs/MANUAL_DEVICE_CHECKLIST.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Release notes](RELEASE_NOTES.md)
- [Contributing](CONTRIBUTING.md)

## License

Original InkDesk code is MIT-licensed. Bundled third-party components retain their upstream licenses and notices.

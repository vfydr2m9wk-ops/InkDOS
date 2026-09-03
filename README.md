# InkDOS — Ink Desk Offline Suite

InkDOS is a local-first, offline and private browser productivity suite for focused DOCX, XLS/XLSX,
PPTX, PDF, TXT and EPUB workflows. It is not intended to replace Microsoft
Office, a full publishing system or a specialist PDF editor.

## InkDesk v1.0.0-beta.1

`1.0.0-beta.1` is the first public beta on the 1.0 line. It consolidates the long
0.20.2/0.20.3 stabilization train into a feature-frozen beta baseline: six
independent workspaces, local-first file handling, recovery and regression
guards, package-preserving Office round-trips where supported, and a consistent
landscape-first shell.

The 0.20.x sequence numbers remain in repository history as engineering
provenance; they are not separate public releases that users need to install.
Internal update sequence numbers are intentionally independent from the public
semantic version.

## Beta policy

The 1.0 beta is feature-frozen. Runtime changes should be limited to reproducible
data-integrity, compatibility, security or high-value/low-risk defects. New
features and broad visual refactors should wait until the beta baseline has
received real-device use.

The generic Launcher **Open a supported file** handoff has been removed because
it duplicated each workspace's Open flow while adding routing and browser-state
complexity. Open the target workspace first, then use that workspace's Open
control.

## Privacy

Selected files are processed in the browser. InkDesk includes no project-run
upload server, account system or analytics service. Saving normally creates a
new local copy rather than silently overwriting the selected source file.

## Run

Open `index.html` directly or serve the directory with a static HTTP server.
HTTP(S) is preferred for service workers, installation and the most predictable
browser behavior.

## Validate

```bash
npm run validate
npm run audit
npm test
npm run test:browser
npm run test:browser:matrix
```

The normal incremental-update gate uses Chromium. The optional matrix checks
installed Chromium, Firefox and WebKit engines; unavailable engines are reported
as not performed unless strict matrix mode is requested. Native Safari/iPadOS
and installed-PWA behavior still require physical-device validation.

## Status

This is **1.0 beta**, not 1.0 stable. The supported scope is intentionally
limited and documented in [`COMPATIBILITY.md`](COMPATIBILITY.md) and
[`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md).

## License

MIT for InkDesk original code. Bundled third-party components retain their
upstream licenses; see `docs/THIRD_PARTY_NOTICES.md`.

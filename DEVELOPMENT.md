# Development Guide

InkDesk intentionally has no mandatory build step. Runtime source is static HTML, CSS, and JavaScript.

## Setup

```bash
python3 -m http.server 8080
```

## Principles

- Keep documents local; do not add accounts, telemetry, remote processing, or mandatory cloud dependencies.
- Treat Office files as untrusted ZIP/XML input.
- Never clear dirty state merely because a Blob, object URL, anchor click, or browser save dialog was created.
- Preserve untouched OOXML parts and compare package inventories on export.
- Keep formula syntax deny-by-default and free of dynamic JavaScript compilation.
- Prefer small shared pure modules and incremental extraction over a framework rewrite.
- Update tests, checksums, version metadata, and documentation with behavior changes.

## Commands

```bash
npm run validate
npm run audit
npm test
PLAYWRIGHT_BROWSER=chromium npm run test:browser
npm run test:release
python3 scripts/build_release.py --output-dir dist
```

Set `PLAYWRIGHT_BROWSER` to `chromium`, `firefox`, or `webkit`. Install the selected Playwright engine first. Do not describe a Playwright WebKit or mobile-emulation run as native Safari/iPadOS validation.

## Release artifacts

`scripts/build_release.py` creates a deterministic runtime ZIP, SHA-256 file, and build metadata tied to the supplied commit/tag. It excludes `.git`, workflows, tests, scripts, caches, browser results, and prebuilt ZIPs. GitHub’s source archive remains the source artifact; a manually generated source ZIP must not be committed.

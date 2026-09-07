# InkDOS 2.0

InkDOS is a local-first, static browser productivity suite. Version 2.0 is a clean consolidation around five independently frozen applications and a small Home launcher.

## Available workspaces

| Workspace | Status | Formats |
| --- | --- | --- |
| Documents | Available | DOCX |
| Spreadsheets | Available | XLS / XLSX |
| Presentations | Available | PPT / PPTX |
| Plain Text | Available | TXT |
| EPUB Reader | Available | EPUB |
| PDF Workspace | Coming soon | PDF |

## Clean-tree rule

InkDOS 2.0 does not import the 1.x application runtime. The five application source trees are taken only from their canonical FINAL packages recorded in `SOURCE_LOCK.json`.

The suite integration is intentionally narrow: Home links into each app, and each app's `index.html` receives one Home icon linking back to `../../index.html`. No other app file is changed.

The applications retain app-private runtimes, including deliberate redundancy. Similar code is not deduplicated into a mutable suite-wide runtime because failure isolation is part of the 2.0 architecture.

## PDF

The PDF card is visible but disabled in 2.0.0. No PDF runtime or PDF.js tree is installed. PDF will be added as a later update.

## Local-first

There is no required backend, telemetry service, or remote document-processing service. GitHub Pages is used only as a static host/PWA surface.

## Repository layout

```text
index.html
assets/
apps/
  documents/
  spreadsheets/
  presentations/
  txt/
  epub/
docs/
scripts/
tests/
```

See `docs/ARCHITECTURE.md`, `docs/PROJECT_STATUS.md`, and `docs/UPDATE_MODEL.md`.

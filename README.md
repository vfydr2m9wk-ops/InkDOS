# InkDOS 2.0.3

InkDOS is a local-first, static browser productivity suite. Version 2.0.3 is a clean consolidation around six independently frozen applications and a small Home launcher.

## Available workspaces

| Workspace | Status | Formats |
| --- | --- | --- |
| Documents | Available | DOCX |
| Spreadsheets | Available | XLS / XLSX |
| Presentations | Available | PPT / PPTX |
| Plain Text | Available | TXT |
| EPUB Reader | Available | EPUB |
| PDF Workspace | Available | PDF |

## Clean-tree rule

InkDOS 2.0 does not import the 1.x application runtime. The six application source trees are taken only from their canonical FINAL packages recorded in `SOURCE_LOCK.json`.

The suite integration remains narrow: Home links into each app and each app returns through its Home icon. Release 2.0.3 adds the accepted PDF P4.2 runtime and its EPUB-style first-open card; the five previously installed app trees remain byte-identical.

The applications retain app-private runtimes, including deliberate redundancy. Similar code is not deduplicated into a mutable suite-wide runtime because failure isolation is part of the 2.0 architecture.

## PDF

PDF is an app-private, physically modular reader and annotation workspace. Open local PDFs, add text/ink/highlight/underline/comments and save copies. The engine and document state do not depend on Home or another app. Internal test fixtures and inspection hooks are excluded from the distribution.

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
  pdf/
docs/
scripts/
```

See `docs/ARCHITECTURE.md`, `docs/PROJECT_STATUS.md`, and `docs/UPDATE_MODEL.md`.

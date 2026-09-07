# InkDOS 2.0.4

InkDOS is a local-first, static browser productivity suite. Version 2.0.4 keeps six physically independent applications behind a small Home launcher and standardizes a system Share action across every workspace.

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

InkDOS 2.0 does not import the 1.x application runtime. Each application retains its canonical baseline and all deliberate integration changes are recorded in `SOURCE_LOCK.json` with integrated tree hashes.

The suite integration remains narrow: Home links into each app and each app returns through its Home icon. Release 2.0.4 adds app-local Share actions to Documents, Spreadsheets, Presentations and PDF, matching the Share behavior already present in Plain Text and EPUB. No suite-wide file-delivery runtime is introduced.

The applications retain app-private runtimes, including deliberate redundancy. Similar code is not deduplicated into a mutable suite-wide runtime because failure isolation is part of the 2.0 architecture.

## Share and save semantics

Share and Save are intentionally separate operations. Share exports the current file state to the host system Share Sheet when file-based Web Share is supported. It does not confirm persistent storage and therefore does not clear unsaved-state indicators. Save/Save copy retains each app's existing delivery and integrity semantics.

Legacy PPT remains read-only in Presentations, so Save and Share are disabled for that source type.

## PDF

PDF is an app-private, physically modular reader and annotation workspace. Open local PDFs, add text/ink/highlight/underline/comments, save copies, and share the current PDF state. The engine and document state do not depend on Home or another app. Internal test fixtures and inspection hooks are excluded from the distribution.

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

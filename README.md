# InkDOS 2.0.7

InkDOS is a local-first, static browser productivity suite. Version 2.0.7 keeps six physically independent applications behind a small Home launcher and enforces the same empty-workspace file-action contract in every app without introducing a shared mutable runtime.

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

InkDOS 2.0 does not import the 1.x application runtime. Each application retains its app-private engine, state, I/O and UI code. Deliberate integration changes are recorded in `SOURCE_LOCK.json` with integrated tree hashes.

The suite integration remains narrow: Home links into each app and each app returns through its Home icon. Similar logic may intentionally exist in multiple applications because physical failure isolation is part of the 2.0 architecture.

## Empty-workspace contract

Opening a workspace does not itself create a document. Before a real document is created, opened or recovered, Save and Share remain unavailable. Each application implements that rule using its own local state; there is no suite-wide document-state module.

Documents, Spreadsheets, Presentations and Plain Text become active only after New/Open succeeds as appropriate. EPUB and PDF become active only after a file is opened. Presentations now starts with zero slides and creates its first blank slide only when New presentation is explicitly requested.

## Share and save semantics

Share and Save are intentionally separate operations. Share exports the current file state to the host system Share Sheet when file-based Web Share is supported. It does not confirm persistent storage and therefore does not clear unsaved-state indicators. Save/Save copy retains each app's existing delivery and integrity semantics.

Legacy PPT remains read-only in Presentations, so Save and Share remain disabled for that source type.

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

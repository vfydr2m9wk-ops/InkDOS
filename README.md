# InkDOS 2.0.9

InkDOS is a local-first, static browser productivity suite. Version 2.0.9 keeps six physically independent applications behind a small Home launcher and adds horizontal appearance consistency without introducing a shared application runtime.

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

## Appearance consistency

Home supports Light, Dark and System through a compact appearance control. The six workspaces keep their existing appearance controls and their own app-private theme implementation.

Appearance consistency is horizontal rather than centralized. A workspace applies a user choice locally using its existing appearance controller, keeps its own app-specific preference key, and additionally publishes the preference value (`light`, `dark` or `system`) through `inkdos2:appearance`. Other open InkDOS pages consume that value through the browser storage event, while pages opened later read it at startup. No shared theme engine, shared CSS bundle or cross-app runtime module is required.

This means a workspace remains independently functional if copied out of the suite: its local appearance key and local theme engine still work, while the optional InkDOS preference communication simply has no peers.

## Empty-workspace contract

Opening a workspace does not itself create a document. Before a real document is created, opened or recovered, Save and Share remain unavailable. Each application implements that rule using its own local state; there is no suite-wide document-state module.

Documents, Spreadsheets, Presentations and Plain Text become active only after New/Open succeeds as appropriate. EPUB and PDF become active only after a file is opened. Presentations starts with zero slides and creates its first blank slide only when New presentation is explicitly requested.

InkDOS 2.0.8 made the PDF and Spreadsheets empty-state controls fail-safe at first paint: Save is disabled in the initial HTML as well as by the app-local runtime, and disabled file-menu actions have an explicit inactive visual state. Home workspace links remain release-versioned so browser navigation is less likely to reuse stale entry pages after an update.

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

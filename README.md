# InkDOS 2.0.12

InkDOS is a local-first, static browser productivity suite with six physically independent workspaces behind an optional Home launcher. Version 2.0.12 turns standalone extraction into an explicit release contract and restructures EPUB so its physical source layout matches its logical engine/state/I/O/view separation.

## Available workspaces

| Workspace | Status | Formats |
| --- | --- | --- |
| Documents | Available | DOCX |
| Spreadsheets | Available | XLS / XLSX |
| Presentations | Available | PPT / PPTX |
| Plain Text | Available | TXT |
| EPUB Reader | Available | EPUB |
| PDF Workspace | Available | PDF |

## Physical modularity and optional Home

Each workspace retains its own engine, state, I/O, frame, UI and view code. There is no shared application runtime root under `shared/`, `modules/` or `core/`, and no workspace is allowed to load another workspace's source files.

The Home button is an optional integration bridge rather than a standalone dependency. Home launches a workspace with `suite=1`. Each app-local frame module keeps its Home action only when that opt-in marker is present; when a workspace is opened directly or extracted from the suite, the frame hides the Home control and removes its active `href`. No shared Home controller is required.

Release validation copies every workspace into an isolated temporary directory and verifies that all non-Home resources required by its entry page still resolve inside that copied app root. It also scans for cross-app runtime references and checks that every file listed in the offline `APP_SHELL` exists.

## EPUB structure

EPUB retains the same reader behavior while its previously flattened root modules are physically separated by responsibility:

```text
apps/epub/
  app.js
  index.html
  assets/
  engine/
    annotations.js
    book-model.js
    content-projector.js
  io/
    epub-writer.js
    file-delivery.js
    package-reader.js
  runtime/
  session/
  state/
    annotation-store.js
    appearance.js
    reading-state.js
  ui/
    reader-controls.js
    reader-controls.css
    start-state.css
  view/
    reader-viewport.js
    reader.css
    renderer.js
```

The 2.0.12 change is structural: package parsing, content projection, annotations, writing and rendering algorithms were moved without intentionally changing their behavior. The start-state styling was also removed from inline `index.html` CSS and placed in the EPUB-local UI layer.

## Appearance consistency

Home supports Light, Dark and System. Each workspace keeps its own app-private appearance controller and preference key. The selected value is communicated horizontally through `inkdos2:appearance`; an extracted app still has its local appearance behavior, while suite-wide synchronization naturally disappears when no peers are present.

## Empty-workspace contract

Opening a workspace does not itself create a document. Save and Share remain unavailable until that app has a real active document, workbook, presentation, text file, book or PDF according to its own state model. Presentations starts with zero slides and creates its first slide only after explicit New or successful Open.

## Share and save semantics

Share and Save remain separate operations. Share exports the current file state through the host system Share Sheet when supported and does not itself confirm persistent storage.

The 2.0.11 single-delivery invariant remains in Documents, Spreadsheets, Presentations, Plain Text and PDF: Apple touch WebKit hosts can prefer file-based system Share for Save, and once a native picker has returned a destination handle a later write failure is terminal rather than starting a second delivery route.

## Format scope

The modularity polish does not broaden file-format fidelity. InkDOS remains intentionally narrower than a full desktop office suite such as LibreOffice: its supported formats and preservation behavior are workspace-specific and should be expanded through each app's private parser/writer boundaries rather than through a shared document engine.

## Local-first

There is no required backend, telemetry service or remote document-processing service. GitHub Pages is used only as a static host/PWA surface.

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

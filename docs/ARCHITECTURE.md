# Architecture

InkDOS is a static, client-side application with a hub and six independent workspaces. No compilation step or backend is required.

## Entry points

- `index.html`: primary hub.
- `InkDesk.html`: compatibility launcher for the hub.
- `Documents.html`, `Spreadsheets.html`, `Presentations.html`: compatibility launchers.
- `apps/documents/index.html`: Document Workspace.
- `apps/spreadsheets/index.html`: Spreadsheet Workspace.
- `apps/presentations/index.html`: Presentation Workspace.
- `manifest.webmanifest`: browser-install metadata.
- `service-worker.js`: same-origin application-shell cache for HTTP(S) deployments.

## Shared runtime

- `shared/office-shell.js` and `shared/office-shell.css`: common shell behavior and visual primitives.
- `shared/office-runtime.js`: filename sanitation, XML parsing boundary, ZIP/package validation, download handling, and object-URL cleanup.
- `shared/register-service-worker.js`: optional service-worker registration. Registration is skipped when the current protocol is not HTTP(S) or the API is unavailable.
- `shared/vendor/`: one canonical offline copy of JSZip and pako plus their license notices.

The shared runtime contains only behavior that is genuinely equivalent across workspaces. Format-specific parsing, serialization, editing, and state remain local to each workspace.

## Workspace ownership

### Documents

`apps/documents/app.js` owns the active document model, editable filename, dirty state, selection, history, and rendered pages. `docx-parser.js` parses supported DOCX parts into a temporary result. `docx-writer.js` exports a new DOCX copy.

### Spreadsheets

`apps/spreadsheets/app.js` owns the active workbook, sheet selection, cell selection, history, dirty state, print view, and pending export. `xlsx-engine.js` parses and serializes XLSX. `xls-biff8-engine.js` imports supported BIFF8 XLS content and converts it into the workbook model used for XLSX export.

### Presentations

`apps/presentations/app.js` owns the active presentation, selected slide/object, edit history, imported source package, presentation-mode state, and temporary image URLs. `engine/compatibility.js` resolves supported OOXML relationships and compatibility behavior.

Each workspace runs in its own page/global scope. Cross-workspace state is not stored in shared globals, local storage, or IndexedDB.

## Import flow

1. The browser supplies a `File` through a file input.
2. The shared runtime validates the compressed input size and package structure.
3. The workspace parser builds a temporary model and validates required XML.
4. The current document is replaced only after parsing and rendering succeed.
5. On failure, temporary URLs/resources are released and the previous document remains active.

Imported Office packages are untrusted. InkDOS does not execute macros, ActiveX, embedded scripts, or remote document instructions.

## Export flow

1. The workspace serializes the current in-memory model, not a stale cached model.
2. Package-preserving writers patch supported parts while retaining unrelated imported parts where possible.
3. A Blob and object URL are created.
4. The browser is asked to download a sanitized filename.
5. The object URL is revoked after the request boundary.
6. Dirty state is cleared only when export generation succeeds; the UI does not claim that the browser completed a filesystem write.

The original selected file is never silently overwritten.

## Storage and recovery

Document content is held in memory. InkDesk does not currently persist active documents, histories, or recovery snapshots to IndexedDB or local storage. The service worker stores application assets only; it does not cache user documents.

## Error boundaries

- File/package validation occurs before expensive decompression or model replacement.
- XML parser errors are converted into explicit exceptions.
- Open operations are transactional for DOCX, XLS/XLSX, and PPTX.
- Export failures preserve dirty state and are logged with technical context.
- Unsupported browser APIs use fallbacks or controlled messages.

## Compatibility layer

The code uses feature detection for service workers, clipboard, fullscreen, downloads, touch/pointer behavior, and optional browser capabilities. No core workflow depends exclusively on the File System Access API or another experimental API.

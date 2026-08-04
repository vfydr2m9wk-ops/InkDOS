# Architecture — InkDesk 0.19.1-beta

## System boundary

InkDesk is a static local-first browser application. User documents remain in the browser process unless the user explicitly invokes browser/host functionality outside InkDesk. There is no project-operated backend, account layer, database, telemetry, or remote document parser.

## Shared high-risk modules

| Module | Responsibility |
|---|---|
| `shared/file-lifecycle.js` | Per-workspace dirty/export state, unverified-download semantics, failure preservation, and fingerprint-gated reopen verification |
| `shared/office-runtime.js` | Input limits, normalized ZIP inventory validation, XML budgets, relationship validation, package inventory, SHA-256, filename sanitation, object URLs, and download feature detection |
| `shared/safe-dom.js` | Deny-by-default reconstruction of DOCX-derived editable DOM |
| `shared/formula-engine.js` | Deterministic bounded arithmetic tokenizer/parser/evaluator |
| `shared/office-shell.js` | Shared presentation and host-independent UI behavior |

Each workspace owns a separate lifecycle instance; state is not global or shared between documents, spreadsheets, and presentations.

## Import pipeline

1. Validate selected file size.
2. For OOXML, inspect the raw ZIP central directory and local headers before JSZip.
3. Reject ambiguous names, unsafe paths, unsupported/encrypted/ZIP64 packages, overlaps, and resource-limit violations.
4. Load with JSZip and validate relationship targets.
5. Parse XML through one aggregate budget with DTD/entity rejection and complexity limits.
6. Build a temporary model and commit it only after parsing/rendering succeeds.
7. Preserve the previous active model when replacement open fails.

The validation is synchronous in this release. A worker boundary for large package/XML validation is a documented follow-up because introducing it safely requires broader lifecycle and cancellation work.

## Editing and rendering

Documents parse OOXML into an intermediate representation, then reconstruct editable DOM through `InkDeskSafeDOM`; parser-produced HTML is never copied directly into the live editor. Spreadsheets maintain a workbook model and use a deterministic limited formula evaluator. Presentations retain imported package/source identifiers and patch supported slide parts rather than rebuilding the entire package.

## Export pipeline

1. Enter `export-preparing`; dirty protection remains active.
2. Serialize or patch a new OOXML package.
3. Compare pre/post package inventory where an original package exists.
4. Generate the export Blob and SHA-256 fingerprint.
5. Request a browser download and enter `download-requested-unverified`.
6. Keep `beforeunload` active because browser download completion cannot be observed reliably.
7. When a file is reopened, parse it normally and mark `export-verified` only if SHA-256 and byte length match the generated copy.

## Preservation strategy

Imported DOCX, XLSX, and PPTX writers retain the original JSZip package and update only supported parts. Unrecognized parts remain untouched where possible. Inventory comparisons reject unexpected deletion or duplication. This strategy improves preservation but does not guarantee advanced Office feature fidelity or semantic validity in every third-party application.

## Incremental separation status

The release extracts shared file lifecycle, package/XML validation, DOM safety, formula evaluation, filename/download handling, and package inventory. The Presentation workspace remains a large module combining model, rendering, selection, commands, history, presentation mode, and export; splitting those boundaries is still required but was not combined with this security release to avoid an unbounded rewrite.


## Unified file routing

`shared/file-router.js` maps supported extensions to one of the three workspace entry points. HTTP(S) launches use a short-lived IndexedDB record identified by an unpredictable token; the destination consumes and deletes the record. Direct `file://` launches retain the hub as the top document, load the selected workspace in a full-screen local iframe, and transfer the browser `File` object with a token-scoped `postMessage` exchange. Workspace home links use `target="_top"` so they exit either mode consistently.

This layer routes files only. Format validation, package limits, transactional opening, and export lifecycle remain owned by the destination workspace.

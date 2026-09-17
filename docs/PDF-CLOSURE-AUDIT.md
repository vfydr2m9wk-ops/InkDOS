# PDF closure and integration audit

Status: **FUNCTIONAL BASELINE FROZEN / DISTRIBUTION INTEGRATED**.

The accepted P4.2 PDF workspace remains the architectural baseline. Two isolated domestic-use completion blocks were subsequently added and audited without introducing a shared runtime or a sibling-workspace dependency.

## PDF-P1 — Reader Completion

Approved scope:

- local text search with result snippets and next/previous navigation;
- print through the browser, with an explicit warning when unsaved annotations would not be included;
- improved outline/page navigation;
- current-page handling;
- view-only 90-degree rotation;
- reader shortcuts;
- preservation of the existing annotation/editor path.

The reader completion implementation remains app-local in `apps/pdf/**`. View rotation does not mutate the source PDF.

## PDF-P2 — Page Tools

Approved scope:

- reorder the current page to an explicit target position;
- permanently rotate the current page by 90-degree increments;
- delete a page, while refusing deletion of the only remaining page;
- extract the current page to a separate PDF;
- split after the current page and deliver both resulting PDFs in one local ZIP archive;
- append one or more selected PDFs to the current PDF.

Page transformations are implemented by the app-local `apps/pdf/engine/page-tools-engine.js`. `pdf-lib` and JSZip are vendored only under `apps/pdf/vendor/`, with their license/provenance files retained. No backend, remote document processing or telemetry was added.

The existing frame, hamburger menu, toolbar, viewer and content surface remain the visual contract. Page Tools is exposed from the existing toolbar through one contextual panel; it does not introduce another permanent toolbar or redesign the workspace.

## Data integrity and limits

Before a structural operation, pending PDF.js edits are serialized to a local in-memory snapshot. Generated PDFs are reopened with PDF.js before they replace the active document or are delivered. Structural changes mark the active session dirty and require the existing Save-copy flow to persist them.

Defensive limits are intentional for browser/WebKit use: 128 MB per PDF source, 2,000 pages, up to eight additional PDFs per merge, and 192 MB aggregate merge input. Password-protected/encrypted inputs that `pdf-lib` cannot safely modify are rejected instead of being partially rewritten.

Advanced PDF structures can exceed the domestic scope. In particular, page extraction/merge does not claim complete preservation of every AcroForm, outline, tagged-PDF, signature, attachment or other document-level relationship. The UI states this limitation instead of claiming lossless enterprise-grade round-trip fidelity.

## Offline and standalone closure

All functional dependencies stay physically inside `apps/pdf/`. The workspace remains independently extractable without Home or sibling-app runtime code. The suite service-worker `APP_SHELL` includes the dynamically loaded PDF-P1 reader module and PDF-P2 engine/UI/vendor runtime files, so the PWA shell can cold-start those capabilities offline after installation.

## Verification

The PDF-P2 engine smoke test creates synthetic PDFs locally and verifies permanent rotation, reorder, deletion, extraction, split, merge, page-count invariants and safety guards. The test lives in the repository-level `tests/` tree and is not shipped as an internal PDF fixture.

The repository release gate additionally runs deterministic Plain Text verification, repository validation, standalone app isolation, source audit, checksums and suite contracts. The final PDF-P2 branch passed that complete gate after the page-tools runtime and offline shell integration were present.

No sibling workspace functional file and no Home entry file is part of the PDF-P2 diff. The only non-PDF changes are generated integrity metadata, the repository-level smoke-test gate, this closure documentation and the service-worker resource list required for offline integration.

With PDF-P2 closed, the PDF domestic functional baseline is frozen. The next permitted functional cycle is **DOC-D1 — Home Document Essentials**; PDF may be reopened only for an objective regression or an explicitly requested future change.

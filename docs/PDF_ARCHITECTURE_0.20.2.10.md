# PDF architecture delta — v0.20.2.10

## Scope

Behavior-preserving extraction of PDF page rendering from `apps/pdf/app.js`.

## New boundary

`apps/pdf/viewer/page-renderer.js` owns page placeholders, intersection-driven render windows, PDF.js canvas/text/AcroForm rendering, rendered-page disposal and resize rerender.

`apps/pdf/app.js` remains the orchestration layer and still owns document open/close, navigation state, review annotations, Save, sidebar data and fullscreen.

## Ratchet

- `apps/pdf/app.js`: 1322 physical lines / 0 lines above 240 characters.
- `apps/pdf/viewer/page-renderer.js`: 344 physical lines / 0 long lines.

## Invariants

No visual redesign, no new PDF tool, no save-format change and no workflow change.

# InkDesk v0.20.2.13 — PDF Save Decomposition

This release completes the main PDF refactoring cycle without intentionally changing the UI or file behavior.

## Architecture

- Added `apps/pdf/io/save-controller.js` as the focused owner of unified PDF Save.
- Moved the PDF.js `saveDocument()` path, flattened annotated export, download creation, progress text and Save-button busy lifecycle out of `apps/pdf/app.js`.
- Kept `apps/pdf/app.js` as the document lifecycle and component-composition entry point.
- Reduced `apps/pdf/app.js` from 587 to 486 physical lines, removing it from inherited architecture debt.
- Kept the new save controller below the normal 500-line / 240-character guardrails.

## Behavior preservation

- PDFs without InkDesk review marks still save through PDF.js so supported form state and source structure remain preserved.
- PDFs with InkDesk review marks still save as a flattened visible annotated PDF copy through the existing local exporter.
- The single visible Save command, local review persistence and original-file safety contract are unchanged.
- No new editing command, visual redesign, backend, telemetry or workflow change is introduced.

## Regression coverage

- Added a structural boundary test for the new save controller.
- Added an isolated Chromium scenario covering both save paths, download filenames, saved-PDF validity and Save-button lifecycle.
- Existing PDF rendering, navigation and review browser scenarios remain independent release blockers.

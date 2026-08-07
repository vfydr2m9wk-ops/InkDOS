# InkDesk v0.20.2.12 — PDF Review Decomposition

This architecture-only patch moves PDF review behavior out of the large PDF workspace entry point without intentionally changing the visible review workflow.

## What moved

- `apps/pdf/review/review-controller.js` now owns local review persistence, text-selection highlight/underline/comment flows, tool state, comment-list rendering and review Undo.
- `apps/pdf/review/annotation-layer.js` now owns page review-overlay rendering plus free marker/text pointer placement.
- `apps/pdf/app.js` remains the composition/lifecycle entry point and delegates review behavior to those focused modules.

## What did not change

- PDF rendering and virtualization remain in `viewer/page-renderer.js`.
- Navigation, thumbnails, outline and bookmarks remain in `viewer/navigation-controller.js`.
- Unified Save / flattened annotated export remains in `app.js` for a later isolated extraction.
- No new review tool, redesign, workflow change, backend or telemetry was introduced.

## Regression evidence

A dedicated browser scenario now exercises selected-text highlight, free marker + Undo, selected-text comments, comment-sidebar navigation and local review persistence. The hosted update gate is expected to run 16 isolated Chromium scripts.

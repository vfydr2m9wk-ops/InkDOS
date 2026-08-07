# PDF architecture delta — v0.20.2.13

## Purpose

Complete the main PDF decomposition by moving unified Save / flattened export coordination out of the PDF entry point while preserving the existing user-visible contract.

## Ownership after this release

- `viewer/page-renderer.js`: page placeholders, virtualization, PDF.js canvas/text/AcroForm rendering and rerender lifecycle.
- `viewer/navigation-controller.js`: current-page navigation, page thumbnails, outline destinations, bookmarks and sidebar tabs.
- `review/review-controller.js`: review persistence, selected-text annotations, comments and Undo.
- `review/annotation-layer.js`: visual review overlays and free marker/text geometry.
- `io/save-controller.js`: structure-preserving PDF.js save, flattened annotated export, download creation and Save-button lifecycle.
- `app.js`: document open/close lifecycle, zoom/direction, fullscreen and component composition.

## Ratchet

`apps/pdf/app.js` is now below the normal 500-line new-runtime ceiling, so its grandfathered architecture-debt entry is removed instead of merely lowered. Future growth above the normal limit is therefore blocked by the same rule as any new runtime source.

## Behavior contract

No visible PDF command is added or removed. The Save command still chooses the PDF.js path when there are no InkDesk annotations and the flattened exporter when annotations must be embedded into a portable copy.

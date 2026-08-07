# PDF architecture delta — v0.20.2.11

## Goal

Continue the behavior-neutral PDF decomposition by moving navigation/sidebar responsibilities out of the main entry point without redesigning the PDF workspace.

## Ownership after this cut

- `viewer/page-renderer.js`: page placeholders, viewport/window virtualization, PDF.js canvas/text/AcroForm rendering, disposal and resize rerender.
- `viewer/navigation-controller.js`: current-page synchronization, previous/next/page input, page list, thumbnail window, PDF outline destinations, bookmarks and sidebar tabs.
- `app.js`: document lifecycle, review annotations, tool state, comments list, zoom/direction orchestration, unified Save and fullscreen composition.

## Guardrails

The navigation controller is new-source code and must remain at or below 500 physical lines with no line above 240 characters. `apps/pdf/app.js` is ratcheted to its post-extraction size and may shrink but may not grow beyond that baseline without an explicit architecture-policy change.

## Behavioral evidence

`revalidate_pdf_navigation.py` starts from a fresh browser context and verifies a PDF containing outline entries. It checks page-list/thumbnail generation, previous/next navigation, outline destination resolution, bookmark navigation and sidebar tab state. Page rendering remains independently covered by `revalidate_pdf_page_rendering.py`.

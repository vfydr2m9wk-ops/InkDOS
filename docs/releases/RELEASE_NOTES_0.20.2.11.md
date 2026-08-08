# InkDesk v0.20.2.11 — PDF Navigation Decomposition

This behavior-neutral maintenance release continues the PDF architecture decomposition.

- Moves page navigation, page-number synchronization, page-list construction and windowed thumbnail rendering into `apps/pdf/viewer/navigation-controller.js`.
- Moves PDF outline destination handling, bookmark-list navigation and sidebar tab state into the same focused controller.
- Keeps page rendering in `viewer/page-renderer.js`; review annotations, unified Save and PDF document lifecycle remain in their existing owners.
- Adds a permanent architecture-boundary test plus an isolated Chromium regression for pages, thumbnails, outline destinations, bookmarks and sidebar tabs.
- Tightens the `apps/pdf/app.js` architecture ratchet after the extraction.
- Adds the new navigation component to the offline application shell.
- No workflow files, visible redesign or intentional PDF behavior change are included.

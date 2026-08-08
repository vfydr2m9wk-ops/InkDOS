# InkDesk v0.20.2.10 — PDF Page Rendering Decomposition

This maintenance release begins the PDF architecture decomposition without changing the visible PDF workflow.

- Moves PDF page virtualization, canvas/text/AcroForm rendering, render-window cleanup and resize rerender into `apps/pdf/viewer/page-renderer.js`.
- Keeps navigation, review annotations, unified Save and document lifecycle behavior unchanged.
- Adds a permanent architecture boundary test and an isolated Chromium PDF rendering/navigation regression.
- Tightens the `apps/pdf/app.js` architecture ratchet after the extraction.
- Adds the new runtime component to the offline service-worker shell.
- No workflow files are changed by the update package.

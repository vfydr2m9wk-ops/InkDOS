# InkDesk v0.20.2.4 — Presentations Navigation and Notes Decomposition

Released: 2026-08-07

## What changed

- Continued the behavior-neutral Presentations decomposition.
- Moved slide-thumbnail rendering and thumbnail visibility state out of
  `apps/presentations/app.js` into `apps/presentations/ui/thumbnails-controller.js`.
- Moved presenter-notes rendering, character count, input/debounce handling and
  notes-panel visibility out of `apps/presentations/app.js` into
  `apps/presentations/ui/presenter-notes-controller.js`.
- Preserved the existing Format/Inspector component from v0.20.2.3.
- Added both new components to offline precaching and every browser harness that
  manually loads the Presentations runtime.
- Tightened the Presentations `app.js` source-debt ratchet after extraction.

## What did not change

- No new editing feature or supported format.
- No visual redesign, control relocation or changed default panel visibility.
- No intentional change to PPTX open/save/export, recovery or slideshow behavior.
- No backend, framework migration or runtime build requirement.

InkDesk remains beta software. Important exported files should still be reopened
and verified, and native Safari/iPadOS/Firefox coverage remains an explicit
manual/browser-matrix responsibility.

# InkDesk v0.20.2.3 — Presentations Inspector Decomposition

Released: 2026-08-07

## What changed

- Started the behavior-neutral Presentations decomposition.
- Moved Format/Inspector state and property handlers from the large
  `apps/presentations/app.js` controller into a focused UI component.
- Preserved the existing panel behavior and object-formatting controls.
- Added component-specific architecture and DOM-contract regression checks.
- Added the component to offline precaching and manual browser harnesses.

## What did not change

- No new editing feature or supported format.
- No visual redesign or control relocation.
- No backend, framework migration or runtime build requirement.
- No intentional change to PPTX open/save/export behavior.

InkDesk remains beta software. Important exported files should still be reopened
and verified, and native Safari/iPadOS/Firefox coverage remains an explicit
manual/browser-matrix responsibility.

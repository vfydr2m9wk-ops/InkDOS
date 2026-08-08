# InkDesk 0.20.3 visual/UX roadmap

## Baseline

`v0.20.2.31` is the frozen structural baseline. Changes to recovery, parsers, writers, formula semantics, history and transactional document state require a reproducible defect and explicit risk/benefit justification.

## Phase 1 — v0.20.3.0: shared visual foundation

- Common system typography and presentation tokens.
- Common 44 px titlebar and interaction-state treatment.
- Home/launcher hierarchy and responsive cards.
- Shared start-surface, focus, pressed and coarse-pointer rules.

## Phase 2 — v0.20.3.1: content workspaces

Completed: Documents, TXT and EPUB consistency for toolbar density, empty states, title editing, reader/editor surfaces and narrow-layout refinement. The implementation is a bounded last-loaded presentation layer; data paths remain frozen.

## Phase 3

Spreadsheets: toolbar groups, formula bar, column/row headers, sheet tabs, status and selection hierarchy.

## Phase 4

Presentations and PDF: sidebar hierarchy, toolbar grouping, inspector/navigation surfaces and presentation/review affordances.

## Phase 5

Compact iPhone/iPad/WebKit pass, keyboard/focus review, visual regression sweep and final accessibility polish.

## Rule

Do not combine visual polish with opportunistic architecture refactors. A data-path change must stand on its own defect evidence and validation.

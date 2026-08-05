# InkDesk 0.19.4 ordered implementation roadmap

This roadmap is the authoritative order for the 0.19.4 development sequence.
Each package must remain focused and must not silently absorb later milestones.

## 0.19.4.1 — Incremental update foundation

- Add the permanent manually triggered update workflow.
- Add transactional package application, validation, rollback, and strict
  sequence tracking.
- Do not change workspace behavior.

## 0.19.4.2 — Module registry foundation

- Add module manifests, configuration, generated registry, and loader.
- Register Documents, Spreadsheets, Presentations, and PDF without removing
  direct entry pages.

## 0.19.4.3 — Shared application shell

- Add shared design tokens, shell regions, panel controller, command registry,
  accessibility events, and offline shell assets.

## 0.19.4.4 — Visual homogeneity and default workspace state

- Apply shared visual rules to the existing programs.
- Open Documents without its optional sidebar.
- Open Presentations without formatting and presenter-notes panels.
- Center the PDF empty-state action.

## 0.19.4.5 — PDF shell stabilization

- Keep the PDF navigation sidebar closed by default.
- Make the sidebar toggle deterministic and accessible.
- Ensure a closed sidebar reserves no blank area.
- Keep the chosen state while a document opens.
- Use one red PDF identity in the launcher, start screen, and viewer.

## 0.19.4.6 — PDF selected-text review tools (implemented)

- Highlight, underline, and comment only actual selected PDF text.
- Convert browser selection rectangles into page-relative review segments.
- Support multi-line selections and one linked segment per page.
- Keep free marker and inserted text separate from selected-text commands.
- Preserve the local review sidecar model.

## 0.19.4.7 — Documents ruler linked to page width

- Match the ruler width and horizontal position to the active page.
- Keep numbers inside the ruler track.
- Recalculate for zoom, orientation, page size, and section changes.
- Keep margin and indentation controls relative to the active page.

## 0.19.4.8 — Spreadsheet formula-reference selection

- Preserve the formula target cell while selecting referenced cells.
- Support drag-selected ranges and Ctrl/Command discontinuous references.
- Update the formula bar live.
- Confirm with Enter, cancel with Escape, and provide a touch fallback.

## 0.19.4.9 — Plain Text module

- Add the modular TXT viewer/editor.
- Support new, open, edit, export, undo/redo, find/replace, word wrap,
  line/column status, UTF-8 BOM handling, and unsaved-change protection.

## 0.19.4.10 — EPUB Reader module

- Add local EPUB package parsing, spine order, sanitized readable HTML,
  basic images, lateral pagination, font sizing, reading themes, table of
  contents, and local reading position.
- Do not add DRM bypass, editing, cloud synchronization, AI, or text-to-speech.

## 0.19.4.11 — Integration and stabilization

- Run cross-module browser and direct-file regression work.
- Complete responsive, keyboard, accessibility, service-worker, and export
  checks.
- Update release documentation and generated metadata.

## 0.19.4 — Final consolidated release package

- Set public version-bearing files consistently to `0.19.4`.
- Mark development state complete.
- Run the full validation profile.
- Generate one complete release ZIP and SHA-256 checksum.
- Generate the final incremental package for a correctly sequenced repository.

## Scope control

A milestone may include a small prerequisite correction required for its own
implementation. Larger unrelated work must remain in its assigned package.
When the order changes, update this roadmap explicitly.

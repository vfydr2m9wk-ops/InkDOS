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

## 0.19.4.7 — Documents ruler linked to page width (implemented)

- Match the ruler width and horizontal position to the active page.
- Keep numbers inside the ruler track.
- Recalculate for zoom, orientation, page size, and section changes.
- Keep margin and indentation controls relative to the active page.

## 0.19.4.8 — Spreadsheet formula-reference selection (implemented)

- Preserve the formula target cell while selecting referenced cells.
- Support drag-selected ranges and Ctrl/Command discontinuous references.
- Update the formula bar live.
- Confirm with Enter, cancel with Escape, and provide a touch fallback.


## 0.19.4.9 — Initial in-cell formula editing (implemented, superseded)

- Added direct formula start, but the wide floating input obstructed range selection.

## 0.19.4.10 — Persistent formula sessions and workflow diagnostics (implemented)

- Keep formula drafts in normal-size cells.
- Preserve incomplete drafts while other cells are edited.
- Add successive-click and drag references without mandatory Ctrl.
- Require two function letters before suggestions.
- Treat postfix `%` as percentage and keep remainder in `MOD()`.
- Record failed update diagnostics and rollback status in Actions summaries.


## 0.19.4.11 — Visual foundation (implemented)

- Establish an Apple-like native system-font stack without bundling fonts.
- Standardize rounded button sizes and tactile default, hover, pressed,
  selected, and disabled states.
- Standardize New and Open actions across all current workspaces.
- Round cards, dialogs, fields, dropdowns, tabs, and other visual surfaces.
- Give retractable side panels raised shadows and three-dimensional edge grips.
- Replace letter-only symbols with a minimal InkDesk and module icon family.
- Prepare purple EPUB and yellow TXT icons before those modules are added.

## 0.19.4.12 — PDF unified Save (implemented)

- Replace parallel PDF export actions with one Save command.
- Flatten InkDesk review marks into a portable annotated PDF copy.
- Keep Open in system PDF viewer and Fullscreen.

## 0.19.4.13 — Plain Text module

- Add a modular TXT viewer/editor using the visual foundation.

## 0.19.4.14 — EPUB Reader module

- Add local EPUB reading, lateral pagination, type sizing, themes, and images.

## 0.19.4.15 — Integration and stabilization

- Run cross-module visual, keyboard, responsive, offline, and export checks.
- Consolidate documentation and release metadata.

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


## 0.19.4.13 — Home and document-session refinement (implemented)

- Home presents workspace cards before the universal Open action.
- Stabilization status is compact and placed near the footer.
- Build information moves to the normal footer line.
- Documents, Spreadsheets, Presentations, and PDF expose editable filenames in
  their title bars.
- The shared file lifecycle installs an automatic unload guard for current and
  future editable modules.
- PDF review changes participate in the same warning contract.
- Documents use clearly distinct blue and white start actions.
- Spreadsheet start actions remain side by side on desktop.


## 0.19.4.14 — Plain Text module (implemented)

- Add an optional enabled TXT module to the generated module registry.
- Add a local notebook-style viewer and editor.
- Support UTF-8 and UTF-16 opening with UTF-8 copy export.
- Preserve the detected source line-ending style on Save.
- Include title editing, unsaved-change protection, Find, word wrap, text size,
  undo/redo, and live text counts.
- Route TXT files from the universal Open action.
- Cache the module for offline use.


## 0.19.4.15 — EPUB Reader module (implemented)

- Add an optional enabled EPUB module and purple launcher card.
- Parse container and package metadata locally from the EPUB archive.
- Render sanitized simple text with supported local images.
- Generate lateral pages with buttons, keyboard navigation, and swipe.
- Add adjustable text size and Paper, Sepia, Sage, and Night themes.
- Keep the three-dimensional table-of-contents panel closed by default.
- Support editable filenames and unchanged renamed EPUB copy export.
- Route EPUB files from the universal Open action and cache the reader offline.

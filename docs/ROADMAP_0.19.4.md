# InkDesk 0.19.4 ordered implementation roadmap

This roadmap is the authoritative order for the 0.19.4 development sequence. Each package must remain focused and must not silently absorb later milestones.

## 0.19.4.1 — Incremental update foundation

- Add the permanent manually triggered update workflow.
- Add a transactional update-package engine with path validation and rollback.
- Add strict sequence tracking through `DEVELOPMENT_STATE.json`.
- Add updater tests and maintainer documentation.
- Do not change workspace behavior.

## 0.19.4.2 — Module registry foundation

- Add module schema, registry, configuration, and loader.
- Register Documents, Spreadsheets, Presentations, and PDF without changing their direct entry pages.
- Generate launcher entries from the registry while retaining safe fallbacks.
- Isolate missing or disabled optional modules.
- Add module-discovery and disabled-module tests.

## 0.19.4.3 — Shared application shell

- Add shared design tokens and reusable shell components.
- Define title bar, command tabs, command bar, sidebar, status bar, zoom control, empty state, and common buttons.
- Add a single offline-compatible icon system.
- Preserve existing workspace functionality during the shell migration.

## 0.19.4.4 — Visual homogeneity and default workspace state

- Migrate Documents, Spreadsheets, Presentations, and PDF to the shared visual rules.
- Use the familiar office-program arrangement described in the visual specification without copying proprietary Microsoft assets.
- Open Documents with optional sidebars closed.
- Open Presentations with formatting and speaker-notes panels closed.
- Keep essential slide thumbnails available.
- Center the PDF `Open Document` empty-state action in the actual viewer area.
- Ensure hidden panels reserve no blank space.

## 0.19.4.5 — Plain Text module

- Add the optional TXT viewer/editor module.
- Support new, open, edit, save/export, undo/redo, find/replace, word wrap, line and column status, UTF-8 BOM handling, and unsaved-change protection.
- Use the shared application shell and visual components from its first implementation.

## 0.19.4.6 — EPUB Reader module

- Add a local EPUB reader with manifest/spine order, simplified sanitized HTML, basic images, lateral pagination, font-size controls, light/sepia/dark reading surfaces, table of contents, and local reading-position storage.
- Warn clearly about unsupported DRM and complex fixed-layout EPUB files.
- Do not add editing, cloud synchronization, AI features, or text-to-speech.

## 0.19.4.7 — Spreadsheet formula-reference selection

- Preserve the formula target cell while the mouse selects referenced cells.
- Support drag-selected continuous ranges.
- Support Ctrl/Command selection of multiple discontinuous cells or ranges.
- Add a touch fallback for adding another range.
- Keep the formula bar visible and update references live.
- Add dedicated selection state and regression tests.

## 0.19.4.8 — PDF review interaction modes

- Separate selected-text review commands from free annotation commands.
- Apply highlight, underline, and comments only to actual selected PDF text.
- Group pen, pencil, freehand marker, inserted text, eraser, and annotation selection under a clear drawing-tools control.
- Preserve the local review sidecar model.
- Do not add page insertion, deletion, reordering, merging, splitting, OCR, AI, or full PDF text editing.

## 0.19.4.9 — Integration and stabilization

- Run cross-module regression work.
- Resolve shell, state, file-opening, export, and service-worker integration issues.
- Complete accessibility checks, narrow-width behavior, keyboard behavior, and local `file://` checks.
- Update release notes, compatibility documentation, architecture documentation, tests, and generated metadata.
- Keep beta/experimental wording when real-device evidence remains incomplete.

## 0.19.4 — Final consolidated release package

- Reset development-state metadata from in-progress to complete.
- Set all public version-bearing files consistently to `0.19.4`.
- Run the full validation profile and build the deterministic release archive.
- Generate one complete `InkDesk_v0.19.4.zip` plus SHA-256 checksum.
- Generate a final incremental package capable of moving a correctly sequenced repository to the final version.
- Do not claim that a Git tag or GitHub Release was published unless it was actually published.

## Scope control

A milestone may include a small prerequisite correction required for its own implementation. Larger unrelated changes must remain in their assigned later package. When a requirement changes, update this roadmap explicitly rather than silently changing package scope.

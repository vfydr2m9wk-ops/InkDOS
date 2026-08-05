# InkDesk 0.19.3-beta.7

This corrective beta addresses three regressions observed in the downloaded beta.6 package when opened directly from the filesystem.

## PDF opening

- Replaced the ES-module PDF.js entry point that Edge blocks on `file://` with the official classic PDF.js 3.11.174 distribution and classic local worker.
- The PDF workspace now initializes before the user clicks **Open PDF**, so the button opens the native file chooser in direct local-file mode.
- Opening a PDF through the InkDesk hub and its local iframe handoff was verified without the previous 30-second transfer timeout.
- Selectable text, AcroForm fields, outline navigation, thumbnails, page synchronization and the five-page render window remain active.
- Direct local-file tests opened the synthetic 4,000-page PDF and jumped to page 3,500 with no JavaScript errors and at most five full page canvases.

## Presentation loading feedback

- PPTX opening now displays a modal progress bar immediately.
- Reading uses `FileReader` progress events and reports bytes read.
- Package validation, relationships, theme/layout processing, per-slide parsing and initial rendering have distinct progress stages.
- The overlay is removed on both success and failure, preserving the previous presentation when an open operation fails.

## Spreadsheet formula discovery

- Pressing `=` while a cell is selected now moves directly to the formula bar with `=` already entered.
- Ten filtered function suggestions appear immediately, with function syntax and a short description.
- Arrow keys choose an item; Enter or Tab inserts it; Escape dismisses the list.
- Suggestions also remain available when typing directly in the formula bar.

## Packaging

- Added a dedicated architecture gate that rejects retired PDF embeds, fragment navigation, `.mjs` local runtime files and duplicate PDF.js inventories.
- Added a simple GitHub Actions workflow for pushes to `main` (or manual execution) that runs architecture, unit and privacy checks, builds the release and uploads the ZIP with its checksum.
- Added a full-replacement proposal and migration checklist under `docs/GITHUB_FULL_REPLACEMENT_PROPOSAL.md`.
- Runtime checksums, SPDX inventory, documentation and tests were regenerated.
- Only synthetic fixtures are included. No private reference document or identifying local path is present.

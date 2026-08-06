# Final consolidation review — InkDesk v0.20.0

## Decision

v0.20.0 is a complete beta consolidation rather than a stable 1.0 release. It
removes the public-facing sequence of `0.19.4.x` update suffixes and establishes
a single source baseline for future `0.20.x` patches.

## Included workspaces

- Documents — focused DOCX editing and copy export.
- Spreadsheets — local BIFF8 XLS import, XLSX editing, formulas, and copy export.
- Presentations — focused PPTX editing and presentation mode.
- PDF — local PDF.js rendering, forms, review marks, and unified Save.
- Plain Text — local TXT viewing/editing.
- EPUB Reader — local reflowed reading with themes and simple images.

## Consolidation changes

- Repaginated home with six compact workspace cards.
- Public version metadata, cache identity, release notes, and manifests set to
  `0.20.0`.
- Complete-replacement publication workflow with dry run, backup branch, strict
  post-vendor validation, repository replacement, commit, and optional tag.
- Pinned PDF.js acquisition during publication; no remote runtime dependency.
- Explicit PDF.js eval disablement.
- Current PDF.js page-layer stylesheet restored without retired native embed
  selectors.
- Source-audit plans for the inherited PDF and shared-layout controllers.
- Old incremental and bootstrap workflows retired from the consolidated tree.

## Validation status

The local source checks and 170-test structural suite passed as documented in
`docs/VALIDATION_REPORT.md`. Strict PDF-vendor validation is delegated to the
publication workflow because the local artifact environment could not retrieve
the npm package. A GitHub dry run is required before publication.

## Residual risk

- Real-device and native-browser coverage remains incomplete.
- The current PDF.js classic version must be migrated in the 0.20 line.
- Office and EPUB fidelity remain intentionally partial.
- Crash/session recovery is not implemented.
- Save generally downloads a new copy rather than overwriting the source.

**Classification: beta.**

# Project status

Release: **InkDOS 2.0.12**

Status: **domestic-use roadmap frozen on 2026-09-10**.

InkDOS contains six installed independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. The functional roadmap completed TXT-T1, TXT-T2, EPUB-E1, EPUB-E2, PDF-P1, PDF-P2, DOC-D1, DOC-D2, PPT-P1, PPT-P2, XLS-S1, XLS-S2 and the integrated Audit before entering the final Freeze phase.

## Current frozen baseline

The active stability baseline is documented in `docs/STABILITY-FREEZE-2026-09-10.md`. Its functional runtime anchor is `44896f583d14dba6ba00b4ee1311f85ed513ad8a`, produced by the approved real-device remediation merge. The freeze candidate was validated at commit `7e852032e21a35710e4fcb3a0c33d0f76ff609e6` by aggregate Stability freeze regression run `34458997715`.

`STABILITY_STATE.json` records the stability program as inactive/frozen after all six workspace audits and cross-suite revalidation. The aggregate freeze gate protects suite architecture/offline behavior, frozen static contracts, PDF.js security configuration, preserved format round-trips and the primary stability browser matrix in Chromium, Firefox and WebKit.

## Real-device remediation included

The frozen runtime includes the post-audit fixes for PDF kinetic/continuous scrolling, EPUB selection Highlight/Note actions, Spreadsheet theme/indexed/tint and table-style color handling, TXT large-file operation, and Presentation legacy-PPT/PPTX fidelity and conversion behavior. These are regression-backed domestic-use improvements; they are not a claim of exhaustive Office, EPUB or PDF compatibility.

## Architecture and integration

Each workspace remains physically rooted under its own `apps/<workspace>/` directory and retains app-local runtime, state and I/O responsibilities. Home remains an optional suite bridge. Semantic features are not owned by toolbar button placement, and the command/state/persistence boundaries remain part of the frozen regression contract.

The root service worker keeps the installed suite available through the validated offline shell. Package-preserving writers and round-trip tests are used where supported; unsupported imported structures are preserved conservatively where the existing contracts permit rather than silently presented as fully editable equivalents.

## Scope boundary

The completed roadmap targets practical domestic use, not exhaustive parity with Microsoft Office, LibreOffice or every feature of DOCX/XLS/XLSX/PPT/PPTX/EPUB/PDF. Known limitations remain authoritative in `docs/KNOWN_LIMITATIONS.md`.

The next development stage is user testing and bug correction against this frozen baseline. Any future fix must keep the stability, architecture, persistence, offline and cross-browser gates intact.

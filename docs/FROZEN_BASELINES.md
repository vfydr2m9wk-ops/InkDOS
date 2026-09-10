# Frozen application baselines

The active frozen domestic-use baseline is the 2026-09-10 refreeze documented in `docs/STABILITY-FREEZE-2026-09-10.md`. The earlier 2026-09-08 freeze remains historical evidence and no longer represents the active runtime baseline.

## Canonical workspace lineage

- Documents — original `InkDOS-2.0-Phase2-Documents-App04-FINAL.zip` baseline plus approved DOC-D1 and DOC-D2 increments.
- Spreadsheets — original `InkDOS-2.0-Phase2-Spreadsheets-App05-FINAL.zip` baseline plus approved XLS-S1 and XLS-S2 increments.
- Presentations — original `InkDOS-2.0-Phase2-Presentations-App05-FINAL.zip` baseline plus approved PPT-P1 and PPT-P2 increments.
- Plain Text — original App01 baseline plus approved TXT-T1 and TXT-T2 increments.
- EPUB Reader — original App02 baseline plus approved EPUB-E1 and EPUB-E2 increments.
- PDF Workspace — accepted P4.2 baseline plus approved PDF-P1 and PDF-P2 increments.

## Completed functional order

The approved roadmap progressed in this order:

1. TXT-T1 — Editing Essentials
2. TXT-T2 — Structured Text / XML
3. EPUB-E1 — Navigation & Retrieval
4. EPUB-E2 — Notes & Reading Library
5. PDF-P1 — Reader Completion
6. PDF-P2 — Page Tools
7. DOC-D1 — Home Document Essentials
8. DOC-D2 — Documents P1 + Legacy Import
9. PPT-P1 — PPTX Home Editing
10. PPT-P2 — Presentation Completion + PPT Import
11. XLS-S1 — Spreadsheet structural integrity, formulas, worksheet semantics and save/reopen preservation
12. XLS-S2 — domestic formatting, basic printing and spreadsheet fidelity/closure polish
13. Audit — integrated cross-suite closure audit
14. Freeze — final stability refreeze

## Workspace scope retained by the freeze

PDF-P2 closes the planned domestic PDF functional scope around local page operations. DOC-D1/DOC-D2 provide the approved domestic Documents authoring, review/structure and conservative legacy-import baseline. PPT-P1/PPT-P2 provide the approved Presentations editing/completion baseline, while unsupported or complex imported objects remain subject to the documented preservation and fidelity limits. XLS-S1/XLS-S2 establish the approved spreadsheet domestic-use baseline, including structural/formula/worksheet semantics and the supported formatting/printing closure scope.

Plain Text and EPUB retain their approved T1/T2 and E1/E2 capabilities. The 2026-09-10 real-device remediation is also part of the active baseline: PDF kinetic-scroll behavior, EPUB contextual annotations, Spreadsheet color fidelity, TXT large-file handling and Presentation fidelity/conversion paths are protected by their applicable regression contracts.

## Stability Functional Isolation Refreeze — 2026-09-10

Frozen functional runtime anchor: `44896f583d14dba6ba00b4ee1311f85ed513ad8a`.

Cross-suite remediation revalidation run: `34457839525`.

Freeze candidate validation commit: `7e852032e21a35710e4fcb3a0c33d0f76ff609e6`.

Aggregate freeze candidate run: `34458997715`.

The freeze protects command/control independence, app-local responsibility boundaries, proportional modularity, browser behavior, offline bootstrap, security configuration and preserved file-format round-trips. Exact integrity values and installed-tree hashes remain recorded in `SOURCE_LOCK.json` and `CHECKSUMS.sha256`.

## Scope boundary

This baseline is for the implemented domestic-use feature set. It does not claim exhaustive DOCX/XLS/XLSX/PPT/PPTX/EPUB/PDF fidelity or parity with full desktop office suites. Future bug fixes discovered by user testing must preserve the frozen contracts and require fresh regression evidence before integration.

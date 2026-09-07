# Frozen application baselines

The six installed application trees come from these canonical FINAL archives:

- Documents — `InkDOS-2.0-Phase2-Documents-App04-FINAL.zip`
- Spreadsheets — `InkDOS-2.0-Phase2-Spreadsheets-App05-FINAL.zip`
- Presentations — `InkDOS-2.0-Phase2-Presentations-App05-FINAL.zip`
- Plain Text — original App01 baseline plus the approved TXT-T1 Editing Essentials and TXT-T2 Structured XML increments.
- EPUB Reader — original App02 baseline plus the approved EPUB-E1 Navigation & Retrieval and EPUB-E2 Notes & Reading Library increments.
- PDF Workspace — accepted P4.2 baseline plus approved PDF-P1 Reader Completion and PDF-P2 Page Tools increments.

## Functional development freeze order

Approved and frozen in sequence:

1. TXT-T1 — Editing Essentials
2. TXT-T2 — Structured Text / XML
3. EPUB-E1 — Navigation & Retrieval
4. EPUB-E2 — Notes & Reading Library
5. PDF-P1 — Reader Completion
6. PDF-P2 — Page Tools

PDF-P2 closes the planned domestic PDF functional scope: local page reorder, permanent rotation, deletion, extraction, split and merge. Its app-local vendor dependencies remain under `apps/pdf/vendor/`; the external smoke test is kept outside the distributable app tree. The suite service worker lists the required PDF P1/P2 runtime resources so the PWA shell can remain offline-capable.

The next permitted functional cycle is **DOC-D1 — Home Document Essentials**. PDF must not receive additional functional work during DOC-D1 unless an objective regression requires reopening the frozen baseline.

Exact SHA-256 values and integration hashes for installed trees are recorded in `SOURCE_LOCK.json` and `CHECKSUMS.sha256`.

# Frozen application baselines

The six installed application trees come from these canonical FINAL archives and approved increments:

- Documents — original `InkDOS-2.0-Phase2-Documents-App04-FINAL.zip` baseline plus the approved DOC-D1 Home Document Essentials and DOC-D2 Documents P1 + Legacy Import increments.
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
7. DOC-D1 — Home Document Essentials
8. DOC-D2 — Documents P1 + Legacy Import

PDF-P2 closes the planned domestic PDF functional scope: local page reorder, permanent rotation, deletion, extraction, split and merge. Its app-local vendor dependencies remain under `apps/pdf/vendor/`; the external smoke test is kept outside the distributable app tree. The suite service worker lists the required PDF P1/P2 runtime resources so the PWA shell can remain offline-capable.

DOC-D1 establishes the domestic Documents authoring baseline on top of the existing paged DOCX editor: text color and highlight; strikethrough, subscript and superscript; find/replace; Letter/A4/Legal paper sizes; portrait/landscape orientation; margins; header/footer text; page numbering; explicit page breaks; and browser print/PDF handoff. DOCX persistence is implemented through an app-local OOXML extension over the existing parser/writer. A Chromium round-trip test verifies generated OOXML, parser re-import and reopening in the Documents workspace, including page layout, header/footer, PAGE field, page break and the added run formatting.

DOC-D2 extends that frozen baseline with browser spellcheck integration, comments, footnotes, automatic TOC, additional styles, table operations, next-page sections and one-to-three-column layouts. The review/structure and section capabilities are persisted through app-local WordprocessingML extensions and protected by Chromium writer → OOXML → parser → reopen tests.

DOC-D2 also adds local RTF import for a conservative domestic subset. RTF is normalized into the Documents model and saved only as DOCX; legacy RTF bytes are not retained as an output source. A Chromium conversion test verifies RTF open → edit → DOCX serialization → OOXML inspection → DOCX reopen. Binary Word 97–2003 `.doc` import is deliberately deferred because its OLE/CFB, FIB, piece-table and formatting-table parser surface is disproportionate to current home-use benefit. This deferral is explicitly allowed by the DOC-D2 roadmap; `.doc` export remains out of scope.

The next permitted functional cycle is **PPT-P1 — PPTX Home Editing**. Documents and all previously frozen workspaces must not receive additional functional work during PPT-P1 unless an objective regression requires reopening a frozen baseline.

Exact SHA-256 values and integration hashes for installed trees are recorded in `SOURCE_LOCK.json` and `CHECKSUMS.sha256`.

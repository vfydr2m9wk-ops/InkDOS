# Frozen application baselines

The six installed application trees come from these canonical FINAL archives and approved increments:

- Documents — original `InkDOS-2.0-Phase2-Documents-App04-FINAL.zip` baseline plus the approved DOC-D1 Home Document Essentials and DOC-D2 Documents P1 + Legacy Import increments.
- Spreadsheets — `InkDOS-2.0-Phase2-Spreadsheets-App05-FINAL.zip`
- Presentations — original `InkDOS-2.0-Phase2-Presentations-App05-FINAL.zip` baseline plus the approved PPT-P1 PPTX Home Editing increment.
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
9. PPT-P1 — PPTX Home Editing

PDF-P2 closes the planned domestic PDF functional scope: local page reorder, permanent rotation, deletion, extraction, split and merge. Its app-local vendor dependencies remain under `apps/pdf/vendor/`; the external smoke test is kept outside the distributable app tree. The suite service worker lists the required PDF P1/P2 runtime resources so the PWA shell can remain offline-capable.

DOC-D1 establishes the domestic Documents authoring baseline on top of the existing paged DOCX editor: text color and highlight; strikethrough, subscript and superscript; find/replace; Letter/A4/Legal paper sizes; portrait/landscape orientation; margins; header/footer text; page numbering; explicit page breaks; and browser print/PDF handoff. DOCX persistence is implemented through an app-local OOXML extension over the existing parser/writer. A Chromium round-trip test verifies generated OOXML, parser re-import and reopening in the Documents workspace, including page layout, header/footer, PAGE field, page break and the added run formatting.

DOC-D2 extends that frozen baseline with browser spellcheck integration, comments, footnotes, automatic TOC, additional styles, table operations, next-page sections and one-to-three-column layouts. The review/structure and section capabilities are persisted through app-local WordprocessingML extensions and protected by Chromium writer → OOXML → parser → reopen tests.

DOC-D2 also adds local RTF import for a conservative domestic subset. RTF is normalized into the Documents model and saved only as DOCX; legacy RTF bytes are not retained as an output source. A Chromium conversion test verifies RTF open → edit → DOCX serialization → OOXML inspection → DOCX reopen. Binary Word 97–2003 `.doc` import is deliberately deferred because its OLE/CFB, FIB, piece-table and formatting-table parser surface is disproportionate to current home-use benefit. This deferral is explicitly allowed by the DOC-D2 roadmap; `.doc` export remains out of scope.

PPT-P1 establishes the domestic PPTX editing baseline on top of the existing Presentations reader/editor. New presentations and imported PPTX files support slide add/duplicate/delete/reorder; text insertion/editing; local image insertion; rectangle, rounded-rectangle, ellipse and line shapes; contextual move/resize/rotate controls; basic fill/border/text colors; bullet lists; and basic Title + Content, Two Content and Section Header layouts. Imported PPTX uses app-local package-preserving structure/object writers rather than flattening the source package. Chromium tests verify real file-input open, hit-tested geometry interaction, PPTX serialization, ZIP/XML inspection, decoder re-import and app reopening. Unsupported complex imported objects remain preserved rather than being exposed as unsafe editable equivalents, and legacy `.ppt` remains read-only until PPT-P2.

The suite service worker includes the PPT-P1 structure writer, object writer and contextual tool module so this baseline remains available in the installed offline shell.

## Stability Functional Isolation Freeze — 2026-09-08

The six functional baselines above are additionally protected by the frozen `stability-functional-isolation` regression baseline recorded in `docs/STABILITY-FREEZE-2026-09-08.md`.

The stability freeze covers PDF, Documents, Presentations, Plain Text, EPUB Reader and Spreadsheets in sequence, followed by an integrated cross-suite frame/bootstrap/offline audit. Its aggregate gate protects command/control independence, app-local responsibility boundaries, proportional modularity, browser behavior, offline bootstrap, security configuration and preserved file-format round-trips.

The frozen runtime anchor is `9da9b798c624e3db6bcf933d85ed19892997bf5f`. The aggregate freeze candidate passed workflow run `34270610710` at commit `f17e102e3e9b612e86da020ba3ab880b16f5741c` across static contracts, preservation round-trips, Chromium, Firefox and WebKit.

Future feature phases must preserve this baseline. A later feature is not approved solely by its own tests; its applicable workspace stability regression and cross-suite offline/isolation regression remain part of the acceptance gate.

The next previously permitted functional cycle remains **PPT-P2 — Presentation Completion + PPT Import**, subject to a subsequent authorized development phase. The stability freeze itself does not start PPT-P2, XLS-S1 or XLS-S2.

Exact SHA-256 values and integration hashes for installed trees are recorded in `SOURCE_LOCK.json` and `CHECKSUMS.sha256`.
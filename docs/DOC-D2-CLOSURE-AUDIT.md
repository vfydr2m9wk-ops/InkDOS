# DOC-D2 closure and integration audit

Status: **FUNCTIONAL BASELINE FROZEN / READY FOR INTEGRATION**.

Phase: **DOC-D2 — Documents P1 + Legacy Import**.

DOC-D2 extends the frozen DOC-D1 Documents workspace only. It does not introduce a shared document engine, backend service, telemetry, remote conversion path, or runtime dependency on another InkDOS workspace. The existing Documents App Frame, Home relationship, appearance bridge, primary toolbar, pagination surface and save/share model remain structurally intact.

## Confirmed P1 functional scope

- Browser-native spellcheck toggle when the host browser provides spelling services.
- Comments attached to selected text, with local add/remove workflow.
- Footnotes with visible references and editable text payload.
- Automatic table of contents generated from document headings and current page positions.
- Additional paragraph styles: Heading 3, Subtitle and Quote, plus TOC paragraph styles.
- Table improvements: merge with right cell, delete row and delete column, with DOCX grid-span persistence for merged cells.
- Section authoring with explicit next-page section breaks.
- One-, two- and three-column section layout with configurable column gap.
- DOCX import/export augmentation for the supported review, style, table and section structures.

## DOCX persistence

The app-local D2 extensions wrap the production parser/writer rather than replacing the frozen Documents engine. Supported D2 structures are represented with standard WordprocessingML parts and elements, including:

- `word/comments.xml`, comment ranges and references;
- `word/footnotes.xml` and footnote references;
- paragraph styles used by Heading 3, Subtitle, Quote and TOC entries;
- `w:gridSpan` for the supported merged-cell operation;
- `w:sectPr`, `w:type` and `w:cols` for next-page sections and column counts/gaps.

Continuous sections from imported DOCX are normalized to the simpler next-page section authoring model while editing. DOC-D2 therefore does not claim exhaustive Word section-layout fidelity.

## RTF legacy import

RTF is the implemented legacy-text import path for DOC-D2.

The importer is entirely app-local and client-side. It validates an RTF header, imposes conservative limits on file size, nesting depth, paragraph count and accumulated text, skips unsupported or non-document destinations, and supports a practical domestic subset including:

- ANSI / Windows-1252 text and RTF Unicode escapes;
- font and color tables;
- bold, italic, underline and strikethrough;
- superscript and subscript;
- font size, font family, text color and highlight;
- paragraph alignment, indents and basic spacing;
- tabs, line breaks, page breaks and section breaks.

RTF is **import-only**. When an RTF file opens, its legacy bytes are not retained as a writable source package. The session is normalized to a `.docx` output name, and Save/Share uses the production DOCX writer to create a new modern-format document. No `.rtf` export or RTF round-trip is claimed.

## Legacy `.doc` decision

Word 97–2003 binary `.doc` import is **deferred** from this baseline, as explicitly permitted by the DOC-D2 roadmap when implementation complexity exceeds practical home-use benefit.

The feasibility audit confirmed that a credible `.doc` reader requires a materially larger binary-format stack than the RTF importer: OLE/CFB container handling, Word FIB interpretation, `WordDocument` plus `0Table`/`1Table` streams, CLX/piece-table reconstruction, paragraph and character property tables, styles, tables, lists and related legacy structures. Implementing or vendoring that stack would substantially increase the Documents regression and security surface for a comparatively low-frequency home-use format.

This is a deliberate scope decision, not an assertion that `.doc` is impossible. A future isolated legacy-compatibility cycle may revisit `.doc` if user demand justifies the additional app-local parser, vendor-license audit and fixture matrix. Any future `.doc` support must remain import-only and convert into the Documents model with DOCX output; `.doc` export remains out of scope.

## Verification evidence

DOC-D2 is protected by repository-level static/syntax/isolation validation plus three Chromium browser round-trip paths:

1. Review/structure round-trip: comments, footnotes, TOC, added styles and table merge are authored, serialized through the production writer, inspected in OOXML, parsed again and reopened in Documents.
2. Section/columns round-trip: two-column and one-column sections, next-page section break and `w:sectPr/w:cols` survive serialization, parser recovery and app reopening.
3. RTF conversion round-trip: a local RTF `File` opens through the production app, enters an RTF session with no retained legacy source package, is edited, written as DOCX, inspected as OOXML and reopened as a normal DOCX session.

The release-validation snapshot also verifies source isolation, checksums, generated metadata, suite contracts and the presence of all DOC-D2 runtime modules in the service-worker application shell.

## Limitations

- Browser spellcheck quality and language availability are host-browser capabilities rather than an InkDOS dictionary engine.
- Comments currently target a selection inside one paragraph; full multi-paragraph review markup is not claimed.
- Footnotes and comments implement the supported domestic authoring subset rather than every Microsoft Word metadata field.
- Automatic TOC is explicitly regenerated from current headings/page positions; it is not a full Word field-update engine.
- Section editing is intentionally normalized to next-page breaks and up to three columns.
- RTF support is a conservative import subset and does not claim exhaustive RTF specification fidelity, embedded OLE objects, macros or arbitrary drawing reconstruction.
- Legacy `.doc` binary import is deferred; `.doc` export is not planned.

## Freeze and next phase

DOC-D2 is frozen when this branch is integrated into `main`. Further Documents functional work requires either an objective regression fix or a separately authorized future compatibility cycle.

The next permitted functional cycle after integration is **PPT-P1 — PPTX Home Editing**.

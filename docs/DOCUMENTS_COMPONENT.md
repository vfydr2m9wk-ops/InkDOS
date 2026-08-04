# Documents Component

## Entry point

`apps/documents/index.html`

## Main source files

- `app.js` — editor state, section-aware page rendering, toolbar commands, opening and saving workflows.
- `docx-parser.js` — DOCX package parsing, styles, numbering, relationships, section geometry and modern wrapper content.
- `docx-writer.js` — package-preserving DOCX copy generation for imported files and minimal generation for new blank files.
- `styles.css` — Documents-specific page, header/footer, toolbar, ruler, sidebar and modal styling.
- `vendor/` — local JSZip and pako browser builds.

## Imported-file save model

The parser records which direct `w:body` child produced each editable block. On Save Copy, the writer loads the original DOCX with JSZip, patches text or table cells linked to those source blocks, retains unrendered OOXML parts, and appends newly created simple blocks before the final section properties.

This approach is intentionally conservative: unsupported features are preserved rather than reconstructed or silently removed.

## User workflow

1. Create a blank document or select a DOCX.
2. Edit the generated page DOM.
3. Use toolbar commands, ruler controls, search, outline and page navigation.
4. Save a generated DOCX copy; the source file is never overwritten.

## Integration notes

The Documents component uses the shared shell only for visual consistency. Its parser, writer and state remain independent from the spreadsheet and presentation applications. Keep the complete directory structure intact so local vendor scripts load correctly.

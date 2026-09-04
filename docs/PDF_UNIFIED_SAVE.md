# PDF unified Save

Development sequence `0.19.4.12` simplifies the PDF workspace to one Save
command after the InkDOS visual foundation.

## Visible document actions

The title bar keeps:

- Open PDF.
- Save.
- Open in system PDF viewer.
- Fullscreen.

The interface removes:

- Export review JSON.
- Import review JSON.
- Save original PDF.
- Print.
- A second parallel Save PDF copy command.

Bookmarks remain available as local review navigation.

## Two Save paths

### No InkDOS review marks

When the document contains no InkDOS highlight, underline, comment, marker, or
inserted text, Save uses PDF.js `saveDocument()`. This preserves supported form
state and keeps the source PDF structure and selectable text.

### InkDOS review marks present

When InkDOS review marks exist, Save:

1. renders each page locally with PDF.js;
2. includes supported form appearances from the current annotation storage;
3. draws InkDOS highlights, underlines, comments, marker areas, and inserted
   text;
4. encodes one page at a time;
5. builds and downloads `original-name-modified.pdf`.

The original file is never overwritten. The editable local review sidecar is
kept after saving.

## Portability trade-off

The annotated copy is flattened so the review marks remain visible in ordinary
PDF readers. Its page appearance is portable, but text in that annotated copy
is not selectable and form fields are no longer editable.

The unannotated/form-only Save path does not have this trade-off.

## Offline and memory behavior

The exporter is bundled and cached in the InkDOS application shell. It does
not upload the document or call an external service.

Pages are rendered and encoded one at a time. The default target is 144 DPI
with an eight-million-pixel page ceiling to reduce browser memory pressure.

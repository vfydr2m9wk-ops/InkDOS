# PDF selected-text review tools

Development sequence `0.19.4.6` separates text review from free annotation.

## Text selection commands

The following tools operate only on a real browser selection inside the PDF.js
text layer:

- Highlight selected text.
- Underline selected text.
- Comment on selected text.

The user may either:

1. select PDF text and then press a command; or
2. activate a command and then select the passage.

After the command is applied, the tool remains active so another passage can be
selected.

## Geometry

InkDesk inspects the selected portions of PDF.js text spans, collects their
browser rectangles, clips them to the page text layer, merges adjacent
rectangles on the same line, and converts them to normalized page-relative
coordinates.

The review sidecar stores one linked annotation record per affected page. Each
record may contain multiple line rectangles and shares a `groupId` with the
other pages in the same selection.

This supports:

- individual words;
- partial lines;
- multi-line passages;
- selections crossing rendered pages;
- zoom and rerendering without storing screen pixels.

## Free annotation

The free review overlay is active only for:

- Marker area.
- Insert free text.

Highlight, underline, and comment no longer create an arbitrary rectangle from
pointer-down to pointer-up.

## Persistence and compatibility

The sidecar remains `inkdesk-pdf-review/2`. Older rectangular annotations
continue to render. New selected-text records add:

- `source: "text-selection"`;
- `selectedText`;
- `groupId`;
- `rects`;
- optional `comment`.

Undo removes all page records belonging to the same selected passage.

## Deliberate exclusions

This milestone does not add OCR, source-PDF text editing, font changes, page
reordering, page deletion, or AI assistance.

# InkDesk v0.20.3.1 — Content Workspaces Visual Pass

This release is the second step of the 0.20.3 user-visible UX train. It keeps the v0.20.2.31 structural/data-safety baseline frozen and refines the three content-centric workspaces: Documents, Plain Text and EPUB.

## What changes

- Adds `shared/ui/content-workspaces-v02031.css`, loaded after the v0.20.3.0 shared visual foundation.
- Refines Documents with denser formatting chrome, clearer active/sidebar states, a calmer page canvas, lighter document shadows and an emphasized enabled Save control.
- Refines Plain Text into a quieter writing surface with a compact display toolbar, stronger yellow identity, restrained editor paper treatment and clearer status segmentation.
- Refines EPUB into a book-first reader with grouped text/theme controls, quieter circular page navigation, a less decorative reading surface and a calmer contents drawer.
- Harmonizes title editing, start cards, icons, status bars and narrow-width spacing across the three workspaces.
- Preserves every command and keeps the visual layer bounded to Documents/TXT/EPUB selectors.
- Adds a dedicated unit contract and a 19th Chromium regression script for the content-workspace visual pass.

## Intentionally unchanged

DOCX/EPUB parsing and writing behavior, TXT file semantics, recovery, history, transactional Open/New/Discard, download safety, formula behavior, Spreadsheet/Presentation/PDF editor logic and all workflow files are unchanged apart from release/cache metadata.

Full notes: [`docs/releases/RELEASE_NOTES_0.20.3.1.md`](docs/releases/RELEASE_NOTES_0.20.3.1.md)

Historical notes: [`docs/releases/`](docs/releases/)
